from typing import Annotated
from langchain.agents import AgentState

def sub_agent_calls_add(a: list[str], b: list[str]) -> list[str]:
    """并发更新 sub_agent_calls 时处理多个值
    当新值为空时，清空
    当新值不为空时，添加到原内容中
    """
    if not b:
        return []
    return a + b

class AppAgentState(AgentState):
    """Agent 应用状态"""
    sub_agent_calls: Annotated[list[str], sub_agent_calls_add]
