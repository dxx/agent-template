from fastapi import APIRouter, Request

from log import get_logger
from web.schemas import ApiResult, Message, MessageResponse, CODE_SUCCESS, AppState
from web.service.message_service import (
    create_chat_id,
    get_chat_message_list,
    get_all_chat_messages,
    delete_chat_messages,
    delete_all_chat_messages,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post("/message/chat/create", response_model=ApiResult[str])
async def create_chat(request: Request) -> ApiResult[str]:
    """创建新的对话"""
    app_state: AppState = getattr(request.state, "app_state")
    user_id = app_state.user_id
    chat_id = await create_chat_id(user_id)
    return ApiResult(code=CODE_SUCCESS, message="success", data=chat_id)

@router.get("/message/all", response_model=ApiResult[list[MessageResponse]])
async def get_all_messages(
    request: Request,
) -> ApiResult[list[MessageResponse]]:
    """获取用户所有对话的消息列表"""
    app_state: AppState = getattr(request.state, "app_state")
    user_id = app_state.user_id

    all_messages = await get_all_chat_messages(user_id)
    return ApiResult(code=CODE_SUCCESS, message="success", data=all_messages)

@router.get("/message/chat/{chat_id}", response_model=ApiResult[list[Message]])
async def get_messages(request: Request, chat_id: str) -> ApiResult[list[Message]]:
    """获取指定对话的消息列表"""
    app_state: AppState = getattr(request.state, "app_state")
    user_id = app_state.user_id

    messages = await get_chat_message_list(user_id, chat_id)
    return ApiResult(code=CODE_SUCCESS, message="success", data=messages)

@router.delete("/message/chat/{chat_id}", response_model=ApiResult[bool])
async def delete_messages(
    request: Request,
    chat_id: str,
) -> ApiResult[bool]:
    """删除指定对话的所有消息"""
    app_state: AppState = getattr(request.state, "app_state")
    user_id = app_state.user_id

    success = await delete_chat_messages(user_id, chat_id)
    return ApiResult(code=CODE_SUCCESS, message="success", data=success)


@router.delete("/message/all", response_model=ApiResult[bool])
async def delete_all_messages(
    request: Request,
) -> ApiResult[bool]:
    """删除用户所有对话的消息"""
    app_state: AppState = getattr(request.state, "app_state")
    user_id = app_state.user_id

    success = await delete_all_chat_messages(user_id)
    return ApiResult(code=CODE_SUCCESS, message="success", data=success)
