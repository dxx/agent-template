from collections.abc import AsyncIterable
from typing import Annotated

from fastapi import APIRouter, Body, Query, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from agent.router import task_agent_holder
from log import get_logger
from web.schemas import (
    CODE_SUCCESS,
    ApiResult,
    AppState,
    ChatResponse,
    RouterChatRequest,
    RequestMsgTypeEnum,
)
from web.service.router_chat_service import router_chat_response

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/router/chat/stream",
    response_class=EventSourceResponse,
    response_model=ChatResponse,
)
async def router_chat_stream(
    request: Request,
    chat_request: Annotated[RouterChatRequest, Body(description="路由对话请求参数")],
) -> AsyncIterable[ServerSentEvent]:
    """路由 Agent 流式对话接口"""

    app_state: AppState = getattr(request.state, "app_state")

    async for response in router_chat_response(app_state, chat_request):
        yield ServerSentEvent(data=response)


@router.get("/router/chat/agents", response_model=ApiResult[list[dict[str, str]]])
async def router_chat_agents(
    request: Request,
) -> ApiResult[list[dict[str, str]]]:
    """获取路由可调用的代理列表"""

    agents = [
        {
            "name": agent.get_name(),
            "description": agent.get_description(),
        }
        for agent in task_agent_holder.get_agents()
    ]

    return ApiResult(code=CODE_SUCCESS, message="success", data=agents)


@router.get("/test/router/chat/stream", response_class=EventSourceResponse)
async def test_router_chat_stream(
    user_id: Annotated[str, Query(description="用户id")],
    chat_id: Annotated[str, Query(description="对话id")],
    content: Annotated[str, Query(description="对话请求内容")],
) -> AsyncIterable[ServerSentEvent]:
    """测试路由 Agent 流式对话接口"""

    app_state = AppState(user_id, chat_id)
    chat_request = RouterChatRequest(
        msg_type=RequestMsgTypeEnum.NORMAL,
        content=content,
    )

    async for response in router_chat_response(app_state, chat_request):
        yield ServerSentEvent(data=response)
