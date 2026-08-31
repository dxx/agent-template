from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.memory.context import AppAgentContext
from agent.subagents import SubAgentEnum
from agent.prompts import AGENT_PROMPT_WRITING, AGENT_DESCRIPTION_WRITING
from agent.middleware import RouteTaskAgent


class WritingAgent(RouteTaskAgent):
    """路由编排使用的写作代理。"""

    def __init__(self):

        agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.WRITING.value,
            system_prompt=AGENT_PROMPT_WRITING,
            context_schema=AppAgentContext,
        )
    
        super().__init__(
            name=SubAgentEnum.WRITING.value,
            description=AGENT_DESCRIPTION_WRITING,
            agent=agent
        )
