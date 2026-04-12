from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.subagents import SubAgentEnum
from agent.middleware import SubAgent
from agent.prompts import AGENT_RESEARCH_PROMPT
from agent.memory import AppAgentContext


class ReseachAgent(SubAgent):
    def __init__(self):
        super().__init__()
        self._agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.RESEARCH.value,
            system_prompt=AGENT_RESEARCH_PROMPT,
            context_schema=AppAgentContext
        )

    def get_name(self) -> str:
        return SubAgentEnum.RESEARCH.value

    def get_description(self) -> str:
        return "擅长从多个信息源收集和整理信息"
