import asyncio
from typing import Any
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph
from langchain.agents.middleware import summarization

from agent.llm import create_chat_model
from agent.prompts import AGENT_MAIN_PROMPT
from agent.middleware import (
    SubAgentMiddleware,
    SummarizationMiddleware,
    SystemTimeMiddleware,
    ToolCallsPatchMiddleware,
    ToolErrorHandlingMiddleware,
    MessageRecordMiddleware,
)
from agent.memory import (
    AppAgentContext,
    AppAgentState,
    get_checkpointer,
    get_store,
)
from agent.subagents.file_manager import FileManagerAgent
from agent.subagents.research import ReseachAgent
from agent.subagents.writing import WritingAgent
from agent.subagents.review import ReviewAgent
from agent.subagents.greet import GreetAgent
from agent.subagents.user import UserAgent


_main_agent = None
_main_agent_lock = asyncio.Lock()

_message_record_middleware: MessageRecordMiddleware | None = None


def get_message_record_middleware():
    global _message_record_middleware
    if _message_record_middleware is None:
        _message_record_middleware = MessageRecordMiddleware(get_store())
    return _message_record_middleware


async def get_main_agent() -> CompiledStateGraph[AppAgentState, AppAgentContext, Any, Any]:
    """获取全局主 Agent，避免并发请求重复初始化。"""
    global _main_agent
    if _main_agent is not None:
        return _main_agent

    async with _main_agent_lock:
        if _main_agent is None:
            _main_agent = create_main_agent()
        return _main_agent


def create_main_agent() -> CompiledStateGraph[AppAgentState, AppAgentContext, Any, Any]:
    """创建主 Agent"""

    main_chat_model = create_chat_model(enable_thinking=False)

    summarization_chat_model = create_chat_model()

    checkpointer = get_checkpointer()
    store = get_store()
    
    message_record_middleware = get_message_record_middleware()

    sub_agents = [
        FileManagerAgent(),
        ReseachAgent(),
        WritingAgent(),
        ReviewAgent(),
        GreetAgent(),
        UserAgent(),
    ]

    return create_agent(
        name="main_agent",
        system_prompt=AGENT_MAIN_PROMPT,
        model=main_chat_model,
        context_schema=AppAgentContext,
        state_schema=AppAgentState,
        checkpointer=checkpointer,
        store=store,
        middleware=[
            SubAgentMiddleware(
                sub_agents=sub_agents
            ),
            # 注入系统当前时间提示词
            SystemTimeMiddleware(),
            # 中间件执行规则
            # before_* hooks: First to last
            # after_* hooks: Last to first (reverse)
            # wrap_* hooks: Nested (first middleware wraps all others)
            SummarizationMiddleware(
                model=summarization_chat_model,
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
