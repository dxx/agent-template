from agent.subagents import (
    get_checkpointer,
    get_store,
    get_message_record_middleware,
)
from agent.memory.namespace import ns
from agent.middleware.message_record import MessageRecord
from session import format_thread_id, generate_chat_id
from web.schemas import Message, MessageResponse
from web.service.title_service import generate_chat_title
from exception import SystemException


_NAMESPACE_CHAT_ID = ns("user_chat_id")

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
    existing = await get_store().aget(_NAMESPACE_CHAT_ID, key)
    if existing and existing.value:
        return existing.value.get("chat_ids", [])
    return []


async def is_chat_id_exists(user_id: str, chat_id: str) -> bool:
    """判断用户的 chat_id 是否存在"""
    user_chat_ids = await get_user_chat_ids(user_id)
    return chat_id in user_chat_ids


async def get_chat_message_list(user_id: str, chat_id: str) -> tuple[str | None, list[Message]]:
    """获取指定对话的标题与消息列表"""
    record = await get_message_record_middleware().get_history(user_id, chat_id)
    messages = []
    for msg in record["messages"]:
        converted = _convert_to_message_record(msg)
        if converted:
            messages.append(converted)
    return record.get("title"), messages


async def get_chat_messages(user_id: str, chat_id: str) -> MessageResponse:
    """获取指定对话的消息详情（标题 + 消息列表）；chat_id 未登记时返回空消息列表。"""
    if not await is_chat_id_exists(user_id, chat_id):
        return MessageResponse(chat_id=chat_id, title=None, messages=[])
    title, messages = await get_chat_message_list(user_id, chat_id)
    return MessageResponse(chat_id=chat_id, title=title, messages=messages)


async def get_all_chat_messages(user_id: str) -> list[MessageResponse]:
    """获取用户所有对话的消息记录，返回 MessageResponse 列表"""
    chat_ids = await get_user_chat_ids(user_id)
    all_responses = []

    for chat_id in chat_ids:
        title, messages = await get_chat_message_list(user_id, chat_id)
        all_responses.append(
            MessageResponse(chat_id=chat_id, title=title, messages=messages)
        )

    return all_responses


async def generate_title(
    user_id: str, content: str, chat_id: str | None = None
) -> str:
    """生成会话标题；传入 chat_id 时，生成成功后写入该对话的标题。

    chat_id 必须是该用户已登记的对话，否则不写入（避免为不存在的对话创建记录）。
    """
    title = await generate_chat_title(content)
    if chat_id and await is_chat_id_exists(user_id, chat_id):
        await get_message_record_middleware().set_title(user_id, chat_id, title)
    return title


async def delete_chat_messages(user_id: str, chat_id: str) -> bool:
    """删除指定对话的所有消息"""
    # 从 message_record 中清除消息历史
    await get_message_record_middleware().clear_history(user_id, chat_id)

    # 从 checkpointer 中删除消息
    thread_id = format_thread_id(user_id, chat_id)
    await get_checkpointer().adelete_thread(thread_id)

    # 从用户的 chat_ids 列表中移除该 chat_id
    key = user_id
    store = get_store()
    existing = await store.aget(_NAMESPACE_CHAT_ID, key)
    if existing and existing.value:
        chat_ids = existing.value.get("chat_ids", [])
        if chat_id in chat_ids:
            chat_ids.remove(chat_id)
            await store.aput(_NAMESPACE_CHAT_ID, key, {"chat_ids": chat_ids})
            return True
    return False


async def delete_all_chat_messages(user_id: str) -> bool:
    """删除用户所有对话的消息（含消息记录与检查点）"""
    chat_ids = await get_user_chat_ids(user_id)

    checkpointer = get_checkpointer()
    middleware = get_message_record_middleware()
    for chat_id in chat_ids:
        # 清理消息记录（含标题）
        await middleware.clear_history(user_id, chat_id)
        # 清理检查点
        thread_id = format_thread_id(user_id, chat_id)
        await checkpointer.adelete_thread(thread_id)

    # 删除用户的 chat_ids 记录
    await get_store().adelete(_NAMESPACE_CHAT_ID, user_id)

    return True


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
    store = get_store()
    existing = await store.aget(_NAMESPACE_CHAT_ID, key)
    if existing and existing.value:
        chat_ids = existing.value.get("chat_ids", [])
        if chat_id not in chat_ids:
            chat_ids.append(chat_id)
            await store.aput(_NAMESPACE_CHAT_ID, key, {"chat_ids": chat_ids})
    else:
        await store.aput(_NAMESPACE_CHAT_ID, key, {"chat_ids": [chat_id]})


def _convert_to_message_record(msg: MessageRecord) -> Message | None:
    """将 MessageRecord 转换为 Message schema"""
    msg_type = msg.get("message_type", "")
    if hasattr(msg_type, "value"):
        type_value: str = msg_type.value
    else:
        type_value = str(msg_type)
    return Message(
        message_id=msg.get("message_id", ""),
        message_type=type_value,  # type: ignore[arg-type]
        content=msg.get("content", ""),
        created=msg.get("timestamp", 0),
    )
