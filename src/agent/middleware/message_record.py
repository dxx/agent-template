from collections.abc import Awaitable
from datetime import datetime
from enum import Enum
from typing import Any, TypedDict, cast, override
from uuid import uuid4
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import (
    ContextT,
    StateT,
)
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
    """聊天消息记录，用于存储用户与模型的所有对话"""

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
            namespace=("message_history",)
        )

        # 获取历史记录
        history = await middleware.get_history(user_id="123", chat_id="456")

        # 清除历史记录
        await middleware.clear_history(user_id="123", chat_id="456")

    注意：
        - runtime.context 必须包含 user_id 和 chat_id 属性
    """

    def __init__(
        self, store: BaseStore, namespace: tuple[str, ...] = ("message_history",)
    ) -> None:
        self.store = store
        self.namespace = namespace

    @override
    def before_agent(
        self,
        state: StateT,
        runtime: Any,
    ) -> dict[str, Any] | None:
        user_input = self._get_user_input(state)
        if not user_input:
            return None
        key = self._get_key_from_runtime(runtime)
        import asyncio

        asyncio.create_task(self._record_user_message(key, user_input))
        return None

    @override
    async def abefore_agent(
        self,
        state: StateT,
        runtime: Any,
    ) -> dict[str, Any] | None:
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
        runtime: Any,
    ) -> dict[str, Any] | None:
        agent_response = self._get_agent_response(state)
        if not agent_response:
            return None
        key = self._get_key_from_runtime(runtime)
        if key:
            import asyncio

            asyncio.create_task(self._record_agent_message(key, agent_response))
        return None

    @override
    async def aafter_agent(
        self,
        state: StateT,
        runtime: Any,
    ) -> dict[str, Any] | None:
        agent_response = self._get_agent_response(state)
        if not agent_response:
            return None
        key = self._get_key_from_runtime(runtime)
        await self._record_agent_message(key, agent_response)
        return None

    def _get_key_from_runtime(self, runtime: Any) -> str:
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
            from langchain_core.messages import HumanMessage

            human_messages = [m for m in messages if isinstance(m, HumanMessage)]
            if not human_messages:
                return None
            last_msg = human_messages[-1]
            return last_msg.text
        except Exception:
            return None

    def _get_agent_response(self, state: StateT) -> str | None:
        try:
            messages = state.get("messages", [])
            if not messages:
                return None
            from langchain_core.messages import AIMessage

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
        record = await self._get_chat_record(key)
        record["messages"].append(self._create_message_info(MessageType.USER, content))
        await self.store.aput(self.namespace, key, dict(record))

    async def _record_agent_message(self, key: str, content: str) -> None:
        record = await self._get_chat_record(key)
        record["messages"].append(self._create_message_info(MessageType.AGENT, content))
        await self.store.aput(self.namespace, key, dict(record))

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
