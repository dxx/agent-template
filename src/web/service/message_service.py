from typing import Any
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from agent.memory import (
    get_checkpointer,
    get_store,
)
from web.session import format_thread_id, generate_chat_id
from web.schemas import Message, MessageResponse
from exception import SystemException

_checkpointer = get_checkpointer()
_store = get_store()

_NAMESPACE_CHAT_ID = ("user_chat_id",)

_MAX_CHAT_COUNT = 10


async def create_chat_id(user_id: str) -> str:
    """创建新的 chat id"""
    is_over_limit, current_count = await _check_max_chat_count(user_id)
    if is_over_limit:
        raise SystemException(f"已达到最大对话数量限制 {_MAX_CHAT_COUNT}")
    chat_id = generate_chat_id()
    await _record_chat_id(user_id, chat_id)
    return chat_id


async def get_user_chat_ids(user_id: str) -> list[str]:
    """获取用户的所有 chat id"""
    key = user_id
    existing = await _store.aget(_NAMESPACE_CHAT_ID, key)
    if existing and existing.value:
        return existing.value.get("chat_ids", [])
    return []


async def get_chat_message_list(user_id: str, chat_id: str) -> list[Message]:
    """获取指定对话的消息列表（转换为 Message schema）"""
    raw_messages = await get_chat_messages(user_id, chat_id)
    messages = []
    for msg in raw_messages:
        converted = _convert_to_message(msg)
        if converted:
            messages.append(converted)
    return messages


async def get_all_chat_messages(user_id: str) -> list[MessageResponse]:
    """获取用户所有对话的消息记录，返回 MessageResponse 列表"""
    chat_ids = await get_user_chat_ids(user_id)
    all_responses = []

    for chat_id in chat_ids:
        messages = await get_chat_message_list(user_id, chat_id)
        all_responses.append(MessageResponse(chat_id=chat_id, messages=messages))

    return all_responses


async def delete_chat_messages(user_id: str, chat_id: str) -> bool:
    """删除指定对话的所有消息"""
    # 从 checkpointer 中删除消息
    thread_id = format_thread_id(chat_id, user_id)
    await _checkpointer.adelete_thread(thread_id)

    # 从用户的 chat_ids 列表中移除该 chat_id
    key = user_id
    existing = await _store.aget(_NAMESPACE_CHAT_ID, key)
    if existing and existing.value:
        chat_ids = existing.value.get("chat_ids", [])
        if chat_id in chat_ids:
            chat_ids.remove(chat_id)
            await _store.aput(_NAMESPACE_CHAT_ID, key, {"chat_ids": chat_ids})
            return True
    return False


async def delete_all_chat_messages(user_id: str) -> bool:
    """删除用户所有对话的消息"""
    chat_ids = await get_user_chat_ids(user_id)
    
    # 删除每个对话的消息
    for chat_id in chat_ids:
        thread_id = format_thread_id(chat_id, user_id)
        await _checkpointer.adelete_thread(thread_id)
    
    # 删除用户的 chat_ids 记录
    key = user_id
    await _store.adelete(_NAMESPACE_CHAT_ID, key)
    
    return True


async def get_chat_messages(user_id: str, chat_id: str) -> list[AnyMessage]:
    """从 checkpointer 获取指定用户的对话消息记录"""

    thread_id = format_thread_id(chat_id, user_id)
    config = RunnableConfig(configurable={"thread_id": thread_id})

    checkpoint_tuple = await _checkpointer.aget_tuple(config)

    if checkpoint_tuple:
        checkpoint = checkpoint_tuple.checkpoint
        if checkpoint:
            messages = checkpoint.get("channel_values", {}).get("messages", [])
            return messages

    return []


async def _check_max_chat_count(user_id: str) -> tuple[bool, int]:
    """检查用户是否达到最大对话数量限制

    Returns:
        (是否超过限制, 当前对话数量)
    """
    chat_ids = await get_user_chat_ids(user_id)
    current_count = len(chat_ids)
    return current_count >= _MAX_CHAT_COUNT, current_count


async def _record_chat_id(user_id: str, chat_id: str):
    """记录 chat id"""
    key = user_id
    existing = await _store.aget(_NAMESPACE_CHAT_ID, key)
    if existing and existing.value:
        chat_ids = existing.value.get("chat_ids", [])
        if chat_id not in chat_ids:
            chat_ids.append(chat_id)
            await _store.aput(_NAMESPACE_CHAT_ID, key, {"chat_ids": chat_ids})
    else:
        await _store.aput(_NAMESPACE_CHAT_ID, key, {"chat_ids": [chat_id]})


def _convert_to_message(any_msg: AnyMessage) -> Message | None:
    """将 AnyMessage 转换为 Message schema"""
    if isinstance(any_msg, HumanMessage):
        return Message(
            message_id=any_msg.id if any_msg.id else "",
            message_type="user",
            content=any_msg.text,
        )
    elif isinstance(any_msg, AIMessage):
        if not any_msg.text:
            return None
        return Message(
            message_id=any_msg.id if any_msg.id else "",
            message_type="ai",
            content=any_msg.text,
        )
    return None
