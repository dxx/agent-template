from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.subagents import SubAgentEnum
from agent.middleware import SubAgent
from agent.prompts import AGENT_WRITING_PROMPT
from agent.memory import AppAgentContext

class WritingAgent(SubAgent):
    def __init__(self):
        super().__init__()
        self._agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.WRITING.value,
            system_prompt=AGENT_WRITING_PROMPT,
            context_schema=AppAgentContext
        )

    def get_name(self) -> str:
        return SubAgentEnum.WRITING.value

    def get_description(self) -> str:
        return "擅长根据需求撰写高质量的内容"
