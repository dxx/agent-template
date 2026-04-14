from langchain.agents import create_agent
from pathlib import Path

from agent.llm import create_chat_model
from agent.middleware import SubAgent
from agent.tools import user
from agent.memory import AppAgentContext, AppAgentState

class UserAgent(SubAgent):
    def __init__(self):
        super().__init__()

        self._agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name="user",
            system_prompt="你是一个专业的维护用户信息的助手。",
            context_schema=AppAgentContext,
            # 子代理需要访问 state 时配置
            state_schema=AppAgentState,
            tools=[user.save_user_info, user.get_user_info],
        )

    def get_name(self) -> str:
        return "user"

    def get_description(self) -> str:
        return "用户信息管理"
