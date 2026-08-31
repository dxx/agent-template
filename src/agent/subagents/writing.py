from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.subagents import SubAgentEnum
from agent.middleware import SubAgent
from agent.prompts import AGENT_PROMPT_WRITING, AGENT_DESCRIPTION_WRITING
from agent.memory import AppAgentContext

class WritingAgent(SubAgent):

    def __init__(self):
        
        agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.WRITING.value,
            system_prompt=AGENT_PROMPT_WRITING,
            context_schema=AppAgentContext
        )

        super().__init__(
            name=SubAgentEnum.WRITING.value,
            description=AGENT_DESCRIPTION_WRITING,
            agent=agent
        )
