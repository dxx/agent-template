from collections.abc import AsyncIterable
from typing import Annotated

from fastapi import APIRouter, Body, Query, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from log import get_logger
from web.schemas import AppState, ChatRequest, ChatResponse, RequestMsgTypeEnum
from web.service.chat_router_service import router_chat_response

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/chat/router/stream",
    response_class=EventSourceResponse,
    response_model=ChatResponse,
)
async def chat_router_stream(
    request: Request,
    chat_request: Annotated[ChatRequest, Body(description="路由对话请求参数")],
) -> AsyncIterable[ServerSentEvent]:
    """路由 Agent 流式对话接口"""

    app_state: AppState = getattr(request.state, "app_state")

    async for response in router_chat_response(app_state, chat_request):
        yield ServerSentEvent(data=response)


@router.get("/test/chat/router/stream", response_class=EventSourceResponse)
async def test_chat_router_stream(
    user_id: Annotated[str, Query(description="用户id")],
    chat_id: Annotated[str, Query(description="对话id")],
    content: Annotated[str, Query(description="对话请求内容")],
) -> AsyncIterable[ServerSentEvent]:
    """测试路由 Agent 流式对话接口"""

    app_state = AppState(user_id, chat_id)
    chat_request = ChatRequest(
        msg_type=RequestMsgTypeEnum.NORMAL,
        content=content,
    )

    async for response in router_chat_response(app_state, chat_request):
        yield ServerSentEvent(data=response)
