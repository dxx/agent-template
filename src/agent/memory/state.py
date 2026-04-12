from langchain.agents import AgentState

class AppAgentState(AgentState):
    """Agent 应用状态"""
    sub_agent_calls: list[str]
