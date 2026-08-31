from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.middleware import SubAgent
from agent.tools import user
from agent.subagents import SubAgentEnum
from agent.prompts import AGENT_PROMPT_USER, AGENT_DESCRIPTION_USER
from agent.memory import AppAgentContext, AppAgentState

class UserAgent(SubAgent):

    def __init__(self):
        
        agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name=SubAgentEnum.USER.value,
            system_prompt=AGENT_PROMPT_USER,
            context_schema=AppAgentContext,
            # 子代理需要访问 state 时配置
            state_schema=AppAgentState,
            tools=[user.save_user_info, user.get_user_info],
        )
        
        super().__init__(
            name=SubAgentEnum.USER.value,
            description=AGENT_DESCRIPTION_USER,
            agent=agent
        )
