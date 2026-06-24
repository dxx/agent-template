import asyncio
from typing import Any
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph
from langchain.agents.middleware import summarization
from langchain.agents.middleware.types import AgentState

from agent.llm import create_chat_model
from agent.memory import (
    AppAgentContext,
    get_checkpointer,
    get_store,
)
from agent.middleware import (
    RouteAgentMiddleware,
    SummarizationMiddleware,
    SystemTimeMiddleware,
    ToolCallsPatchMiddleware,
    ToolErrorHandlingMiddleware,
    MessageRecordMiddleware,
)
from agent.router.file_manager import FileManagerAgent
from agent.router.greet import GreetAgent
from agent.router.research import ResearchAgent
from agent.router.review import ReviewAgent
from agent.router.writing import WritingAgent

_router_agent = None
_router_agent_lock = asyncio.Lock()

_message_record_middleware: MessageRecordMiddleware | None = None


def get_message_record_middleware():
    global _message_record_middleware
    if _message_record_middleware is None:
        _message_record_middleware = MessageRecordMiddleware(get_store())
    return _message_record_middleware


async def get_router_agent() -> CompiledStateGraph[AgentState, AppAgentContext, Any, Any]:
    """获取全局路由 Agent，避免并发请求重复初始化。"""
    global _router_agent
    if _router_agent is not None:
        return _router_agent

    async with _router_agent_lock:
        if _router_agent is None:
            _router_agent = create_router_agent()
        return _router_agent


def create_router_agent() -> CompiledStateGraph[AgentState, AppAgentContext, Any, Any]:
    """创建路由编排 Agent

    使用 router 目录下的写作、研究、审核、招待和文件管理代理，由
    `RouterAgent` 根据 `query` 动态路由并编排执行。
    """

    checkpointer = get_checkpointer()
    store = get_store()
    
    message_record_middleware = get_message_record_middleware()

    agents = [
        WritingAgent(),
        ResearchAgent(),
        ReviewAgent(),
        GreetAgent(),
        FileManagerAgent(),
    ]

    route_agent_middleware = RouteAgentMiddleware(
        name="router_agent",
        router_model=create_chat_model(enable_thinking=False),
        agents=agents,
        context_schema=AppAgentContext,
    )

    return create_agent(
        name="router_main_agent",
        model=create_chat_model(enable_thinking=False),
        context_schema=AppAgentContext,
        checkpointer=checkpointer,
        store=store,
        middleware=[
            route_agent_middleware,
            # 注入系统当前时间提示词
            SystemTimeMiddleware(),
            # 中间件执行规则
            # before_* hooks: First to last
            # after_* hooks: Last to first (reverse)
            # wrap_* hooks: Nested (first middleware wraps all others)
            SummarizationMiddleware(
                model=create_chat_model(),
                trigger=[
                    ("tokens", 10000), # 当 Token 数量达到 10000 时触发
                    ("messages", 30),  # 当消息数量达到 30 时触发
                ],
                keep=("messages", 20), # 保留多少最近 20 条消息
                summary_prompt=summarization.DEFAULT_SUMMARY_PROMPT + "\n<note>请用中文总结</note>",
            ),
            ToolCallsPatchMiddleware(),
            ToolErrorHandlingMiddleware(),
            message_record_middleware, # type: ignore[arg-type]
        ]
    )
