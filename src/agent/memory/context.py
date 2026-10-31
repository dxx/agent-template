from dataclasses import dataclass

from agent.memory.router_state import AgentTask

@dataclass
class AppAgentContext:
    """Agent 应用上下文"""

    user_id: str

    chat_id: str
    
    message_record: bool = True
    """是否把消息记录到聊天历史。False 时不记录。"""

    agents: list[AgentTask] | None = None
    """指定的任务代理及任务内容。

    为空时由路由模型自动选择代理；非空时跳过路由判断，直接调用指定代理。
    """
