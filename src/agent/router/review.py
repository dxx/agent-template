from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.subagents import SubAgentEnum
from agent.memory.context import AppAgentContext
from agent.prompts import AGENT_REVIEW_PROMPT
from agent.middleware import RouteTaskAgent


class ReviewAgent(RouteTaskAgent):
    """路由编排使用的审核代理。"""

    def __init__(self):

        agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.REVIEW.value,
            system_prompt=AGENT_REVIEW_PROMPT,
            context_schema=AppAgentContext,
        )
        
        super().__init__(
            name=SubAgentEnum.REVIEW.value,
            description="擅长检查和改进内容质量，对事物进行评价",
            agent=agent
        )
