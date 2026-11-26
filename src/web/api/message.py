from fastapi import APIRouter, Body, Request
from typing import Annotated

from log import get_logger
from web.schemas import (
    CODE_SUCCESS,
    ApiResult,
    MessageResponse,
    AppState,
    GenerateTitleRequest,
    GenerateTitleResponse,
)
from web.service.message_service import (
    create_chat_id,
    get_chat_messages,
    get_all_chat_messages,
    delete_chat_messages,
    delete_all_chat_messages,
    generate_title,
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


@router.get("/message/chat/{chat_id}", response_model=ApiResult[MessageResponse])
async def get_messages(request: Request, chat_id: str) -> ApiResult[MessageResponse]:
    """获取指定对话的消息详情（含标题）"""
    app_state: AppState = getattr(request.state, "app_state")
    user_id = app_state.user_id

    chat = await get_chat_messages(user_id, chat_id)
    return ApiResult(code=CODE_SUCCESS, message="success", data=chat)


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


@router.post("/message/chat/generate-title", response_model=ApiResult[GenerateTitleResponse])
async def generate_chat_title(
    request: Request,
    title_request: Annotated[GenerateTitleRequest, Body(description="标题生成参数")],
) -> ApiResult[GenerateTitleResponse]:
    """根据用户输入内容生成会话标题。

    传入 `chat_id` 时，生成成功后更新该对话的标题；未传只返回标题、不落库。
    """
    app_state: AppState = getattr(request.state, "app_state")
    user_id = app_state.user_id

    title = await generate_title(user_id, title_request.content, title_request.chat_id)
    return ApiResult(
        code=CODE_SUCCESS,
        message="success",
        data=GenerateTitleResponse(title=title),
    )
