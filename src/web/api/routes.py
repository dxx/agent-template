from collections.abc import AsyncIterable
from fastapi import APIRouter, Body, Query, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from typing import Annotated

from web.schemas import ChatRequest, ChatResponse, HealthResponse, AppState
from web.service.chat_service import chat_response
from log import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.post("/chat/stream", response_class=EventSourceResponse, response_model=ChatResponse)
async def chat(
    request: Request,
    chat_request: Annotated[ChatRequest, Body(description="对话请求参数")],
) -> AsyncIterable[ServerSentEvent]:
    """流式对话接口"""

    app_state: AppState  = getattr(request.state, "app_state")

    async for response in chat_response(app_state, chat_request):
        yield ServerSentEvent(data=response)


@router.get("/test/chat/stream", response_class=EventSourceResponse)
async def test_chat(
    user_id: Annotated[str, Query(description="用户id")],
    chat_id: Annotated[str, Query(description="对话id")],
    content: Annotated[str, Query(description="对话请求内容")],
) -> AsyncIterable[ServerSentEvent]:
    """测试对话接口"""

    app_sate = AppState(
        user_id, chat_id
    )
    
    chat_request = ChatRequest(
        msg_type="NORMAL",
        content=content
    )

    async for response in chat_response(app_sate, chat_request):
        yield ServerSentEvent(data=response)


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")
