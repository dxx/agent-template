from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.subagents import SubAgentEnum
from agent.middleware import SubAgent
from agent.prompts import AGENT_REVIEW_PROMPT
from agent.memory import AppAgentContext

class ReviewAgent(SubAgent):
    def __init__(self):
        super().__init__()
        self._agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.REVIEW.value,
            system_prompt=AGENT_REVIEW_PROMPT,
            context_schema=AppAgentContext
        )

    def get_name(self) -> str:
        return SubAgentEnum.REVIEW.value

    def get_description(self) -> str:
        return "擅长检查和改进内容质量，对事物进行评价"
