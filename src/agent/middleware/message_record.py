import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, TypedDict, cast, override
from uuid import uuid4
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import (
    ContextT,
    StateT,
)
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.runtime import Runtime
from langgraph.store.base import BaseStore


class MessageType(str, Enum):
    USER = "user"
    AGENT = "agent"


class MessageRecord(TypedDict):
    message_id: str
    message_type: MessageType
    content: str
    timestamp: int


class ChatMessageRecord(TypedDict):
    """聊天消息记录，用于存储用户与 Agent 的所有对话"""

    user_id: str
    chat_id: str
    messages: list[MessageRecord]


class MessageRecordMiddleware(AgentMiddleware[StateT, ContextT, Any]):
    """记录用户与模型对话消息的中间件

    该中间件用于记录用户提问和模型回复消息，并将消息历史存储在 BaseStore 中。

    工作流程：
    1. before_agent: 记录用户最新的提问消息
    2. after_agent: 记录模型最新的回复消息

    存储结构：
    - namespace: 可配置的命名空间，默认为 ("message_history",)
    - key: 格式为 "{user_id}:{chat_id}"，从 runtime.context 获取
    - value: ChatMessageRecord，包含用户ID、聊天ID和消息列表

    ChatMessageRecord 结构：
    - user_id: str, 用户ID
    - chat_id: str, 聊天ID
    - messages: list[MessageRecord], 消息列表

    MessageRecord 结构：
    - message_id: str, UUID
    - message_type: MessageType, 枚举值 (USER/AGENT)
    - content: str, 消息内容
    - timestamp: int, 毫秒级时间戳

    使用示例：
        store = InMemoryStore()
        middleware = MessageRecordMiddleware(
            store=store,
            namespace=("message_history",),
            keep_size=100,      # 清理后保留 100 条（偶数）
            trigger_size=120,   # 攒到 120 条再清理
        )

        # 获取历史记录
        history = await middleware.get_history(user_id="123", chat_id="456")

        # 清除历史记录
        await middleware.clear_history(user_id="123", chat_id="456")

    注意：
        - runtime.context 必须包含 user_id 和 chat_id 属性
        - runtime.context.message_record 为 False 时不记录消息
    """

    def __init__(
        self,
        store: BaseStore,
        namespace: tuple[str, ...] = ("message_history",),
        keep_size: int | None = 100,
        trigger_size: int | None = None,
    ) -> None:
        """初始化消息记录中间件。

        Args:
            store: 消息存储。
            namespace: 存储命名空间。
            keep_size: 清理后保留的消息条数。向下取偶数，保证按「用户提问 +
                Agent 回答」成对保留。None 表示不裁切。
            trigger_size: 触发清理的阈值。消息数量达到该值时清理。
                None 时用 `keep_size` 作为阈值。
        """
        self.store = store
        self.namespace = namespace
        self.keep_size = keep_size
        self.trigger_size = trigger_size

    @override
    def before_agent(
        self,
        state: StateT,
        runtime: Runtime[Any],
    ) -> dict[str, Any] | None:
        if not self._is_record_enabled(runtime):
            return None
        user_input = self._get_user_input(state)
        if not user_input:
            return None
        key = self._get_key_from_runtime(runtime)

        asyncio.create_task(self._record_user_message(key, user_input))
        return None

    @override
    async def abefore_agent(
        self,
        state: StateT,
        runtime: Runtime[Any],
    ) -> dict[str, Any] | None:
        if not self._is_record_enabled(runtime):
            return None
        user_input = self._get_user_input(state)
        if not user_input:
            return None
        key = self._get_key_from_runtime(runtime)
        await self._record_user_message(key, user_input)
        return None

    @override
    def after_agent(
        self,
        state: StateT,
        runtime: Runtime[Any],
    ) -> dict[str, Any] | None:
        if not self._is_record_enabled(runtime):
            return None
        agent_response = self._get_agent_response(state)
        if not agent_response:
            return None
        key = self._get_key_from_runtime(runtime)
        if key:
            asyncio.create_task(self._record_agent_message(key, agent_response))
        return None

    @override
    async def aafter_agent(
        self,
        state: StateT,
        runtime: Runtime[Any],
    ) -> dict[str, Any] | None:
        if not self._is_record_enabled(runtime):
            return None
        agent_response = self._get_agent_response(state)
        if not agent_response:
            return None
        key = self._get_key_from_runtime(runtime)
        await self._record_agent_message(key, agent_response)
        return None

    def _is_record_enabled(self, runtime: Runtime[Any]) -> bool:
        """是否需要记录消息。

        上下文里的 `message_record` 为 False 时不记录，
        用于路由 Agent 这类不应该写入聊天历史的内部调用。
        """
        context = getattr(runtime, "context", None)
        if context is None:
            return True
        return bool(getattr(context, "message_record", True))

    def _get_key_from_runtime(self, runtime: Runtime[Any]) -> str:
        if not hasattr(runtime, "context") or not runtime.context:
            raise ValueError("runtime.context is required")
        ctx = runtime.context
        user_id = getattr(ctx, "user_id", None)
        chat_id = getattr(ctx, "chat_id", None)
        if not user_id or not chat_id:
            raise ValueError("runtime.context must have user_id and chat_id")
        return self._format_key(user_id, chat_id)

    def _get_user_input(self, state: StateT) -> str | None:
        try:
            messages = state.get("messages", [])
            if not messages:
                return None

            human_messages = [m for m in messages if isinstance(m, HumanMessage)]
            if not human_messages:
                return None
            last_msg = human_messages[-1]
            if isinstance(last_msg.content, str):
                text_value = last_msg.content
            else:
                # Must be a list
                blocks = []
                for block in last_msg.content:
                    if not block:
                        continue
                    if isinstance(block, str):
                        blocks.append(block)
                    if isinstance(block, dict):
                        if (block.get("type") == "text" and isinstance(block.get("text"), str) and block.get("text")):
                            blocks.append(block.get("text"))
                        elif block.get("type") in ["image", "image_url"]:
                            image_url = block.get("url") or block.get("image_url", {}).get("url")
                            if image_url:
                                blocks.append(f"<msg-img-url>{image_url}</msg-img-url>")
                        elif block.get("type") in ["video", "video_url"]:
                            video_url = block.get("url") or block.get("video_url", {}).get("url")
                            if video_url:
                                blocks.append(f"<msg-video-url>{video_url}</msg-video-url>")
                        else:
                            blocks.append("[未知]")
                text_value = "\n".join(
                    blocks
                )
            return text_value
        except Exception:
            return None

    def _get_agent_response(self, state: StateT) -> str | None:
        try:
            messages = state.get("messages", [])
            if not messages:
                return None

            ai_messages = [m for m in messages if isinstance(m, AIMessage)]
            if not ai_messages:
                return None
            last_msg = ai_messages[-1]
            return last_msg.text
        except Exception:
            return None

    def _format_key(self, user_id: str, chat_id: str) -> str:
        return f"{user_id}:{chat_id}"

    def _parse_key(self, key: str) -> tuple[str, str]:
        parts = key.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid key format: {key}")
        return parts[0], parts[1]

    def _create_message_info(
        self,
        message_type: MessageType,
        content: str,
    ) -> MessageRecord:
        return {
            "message_id": str(uuid4()),
            "message_type": message_type,
            "content": content,
            "timestamp": int(datetime.now().timestamp() * 1000),
        }

    async def _get_chat_record(self, key: str) -> ChatMessageRecord:
        user_id, chat_id = self._parse_key(key)
        item = await self.store.aget(self.namespace, key)
        if item and item.value:
            value = item.value
            if isinstance(value, dict) and "messages" in value:
                return cast(ChatMessageRecord, value)
        return cast(
            ChatMessageRecord,
            {
                "user_id": user_id,
                "chat_id": chat_id,
                "messages": [],
            },
        )

    async def _record_user_message(self, key: str, content: str) -> None:
        """记录用户提问。只追加，不清理。"""
        record = await self._get_chat_record(key)
        record["messages"].append(self._create_message_info(MessageType.USER, content))
        await self.store.aput(self.namespace, key, dict(record))

    async def _record_agent_message(self, key: str, content: str) -> None:
        """记录 Agent 回复。追加后按阈值清理旧的记录。"""
        record = await self._get_chat_record(key)
        messages = record["messages"]
        messages.append(self._create_message_info(MessageType.AGENT, content))
        record["messages"] = self._trim_messages(messages)
        await self.store.aput(self.namespace, key, dict(record))

    def _trim_messages(self, messages: list[MessageRecord]) -> list[MessageRecord]:
        """达到触发阈值时，保留最近的偶数条记录。

        - `keep_size` 为 None 时不裁切
        - `trigger_size` 为 None 时用 `keep_size` 作为阈值
        """
        keep = self.keep_size
        if keep is None or keep <= 0:
            return messages

        trigger = self.trigger_size if self.trigger_size is not None else keep
        if trigger <= 0 or len(messages) < trigger:
            return messages

        # 保留的条数向下取偶数，保证按对保留
        keep = keep - (keep % 2)
        if keep <= 0:
            return messages
        return messages[-keep:]

    async def get_history(self, user_id: str, chat_id: str) -> list[MessageRecord]:
        """获取指定用户和聊天的消息历史

        Args:
            user_id: 用户ID
            chat_id: 聊天ID

        Returns:
            list[MessageRecord]: 消息列表
        """
        key = self._format_key(user_id, chat_id)
        record = await self._get_chat_record(key)
        return record["messages"]

    async def clear_history(self, user_id: str, chat_id: str) -> None:
        """清除指定用户和聊天的所有消息历史

        Args:
            user_id: 用户ID
            chat_id: 聊天ID
        """
        key = self._format_key(user_id, chat_id)
        await self.store.adelete(self.namespace, key)

    async def delete_message(self, user_id: str, chat_id: str, message_id: str) -> bool:
        """根据 message_id 删除单条消息

        Args:
            user_id: 用户ID
            chat_id: 聊天ID
            message_id: 消息ID

        Returns:
            bool: 是否删除成功
        """
        key = self._format_key(user_id, chat_id)
        record = await self._get_chat_record(key)
        for i, msg in enumerate(record["messages"]):
            if msg["message_id"] == message_id:
                record["messages"].pop(i)
                await self.store.aput(self.namespace, key, dict(record))
                return True
        return False
