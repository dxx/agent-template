from typing import Any
from langchain_core.messages import ToolCall, SystemMessage, HumanMessage
from langgraph.runtime import Runtime
from langchain.agents.middleware.types import (
    AgentState,
    ContextT,
)

from agent.llm import create_chat_model

decision_llm = create_chat_model(enable_thinking=False)

sys_prompt = """
你是一个专业的审核提示词助手，擅长优化提示词的内容。
不要过度思考，只需要优化内容，快速回复
"""

user_prompt = """
现在用户需要进行审批，原始审批内容如下：

{content}

检查和翻译以上审核的内容，把审批信息以用户友好的方式告诉用户
记住：不要给用户出选择，不要询问用户审批
"""

default_allowed_decisions = ["approve", "reject"]

def default_descript_callable(
    tool_call: ToolCall,
    state: AgentState[Any],
    runtime: Runtime[ContextT]
) -> str:
    """默认的审批描述内容处理"""
    content = f"执行工具: {tool_call["name"]}, 参数内容: {tool_call["args"]}\n"
    ai_message = decision_llm.invoke(
        [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt.format(content=content))
        ]
    )

    return ai_message.content
    