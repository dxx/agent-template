from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.memory.context import AppAgentContext
from agent.prompts import AGENT_REVIEW_PROMPT
from agent.middleware import RouteTaskAgent


class ReviewAgent(RouteTaskAgent):
    """路由编排使用的审核代理。"""

    def __init__(self):
        super().__init__(
            name="review",
            description="擅长检查和改进内容质量，对事物进行评价",
            agent=create_agent(
                model=create_chat_model(),
                name="review",
                system_prompt=AGENT_REVIEW_PROMPT,
                context_schema=AppAgentContext,
            ),
        )
