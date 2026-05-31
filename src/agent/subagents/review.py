from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.subagents import SubAgentEnum
from agent.middleware import SubAgent
from agent.prompts import AGENT_REVIEW_PROMPT
from agent.memory import AppAgentContext

class ReviewAgent(SubAgent):
    def __init__(self):
        super().__init__(
            name=SubAgentEnum.REVIEW.value,
            description="擅长检查和改进内容质量，对事物进行评价",
            agent=create_agent(
                model=create_chat_model(),
                name=SubAgentEnum.REVIEW.value,
                system_prompt=AGENT_REVIEW_PROMPT,
                context_schema=AppAgentContext
            )
        )
