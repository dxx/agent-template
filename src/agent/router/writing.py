from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.memory.context import AppAgentContext
from agent.prompts import AGENT_WRITING_PROMPT
from agent.middleware import RouteTaskAgent


class WritingAgent(RouteTaskAgent):
    """路由编排使用的写作代理。"""

    def __init__(self):
        super().__init__(
            name="writing",
            description="擅长根据需求撰写高质量的内容",
            agent=create_agent(
                model=create_chat_model(),
                name="writing",
                system_prompt=AGENT_WRITING_PROMPT,
                context_schema=AppAgentContext,
            ),
        )
