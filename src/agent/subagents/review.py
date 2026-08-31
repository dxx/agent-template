from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.subagents import SubAgentEnum
from agent.middleware import SubAgent
from agent.prompts import AGENT_PROMPT_REVIEW, AGENT_DESCRIPTION_REVIEW
from agent.memory import AppAgentContext

class ReviewAgent(SubAgent):

    def __init__(self):
        
        agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.REVIEW.value,
            system_prompt=AGENT_PROMPT_REVIEW,
            context_schema=AppAgentContext
        )
        
        super().__init__(
            name=SubAgentEnum.REVIEW.value,
            description=AGENT_DESCRIPTION_REVIEW,
            agent=agent
        )
