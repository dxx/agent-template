from langchain.agents import create_agent
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


_checkpointer = get_checkpointer()
_store = get_store()

_message_record_middleware = MessageRecordMiddleware(_store)


def get_message_record_middleware():
    return _message_record_middleware


def create_main_agent():
    """创建主 Agent"""

    main_chat_model = create_chat_model(enable_thinking=False)

    summarization_chat_model = create_chat_model()

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
        checkpointer=_checkpointer,
        store=_store,
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
            _message_record_middleware, # type: ignore[arg-type]
        ]
    )
