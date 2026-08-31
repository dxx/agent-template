from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.memory.context import AppAgentContext
from agent.memory.state import AppAgentState
from agent.middleware import RouteTaskAgent
from agent.subagents import SubAgentEnum
from agent.prompts import AGENT_PROMPT_GREET, AGENT_DESCRIPTION_GREET
from agent.skills import RemoteSkillLoader
from agent.tools import greet
from agent.middleware.prebuild.skills import SkillsMiddleware


class GreetAgent(RouteTaskAgent):
    """路由编排使用的招待代理。"""

    def __init__(self):

        agent =  create_agent(
                model=create_chat_model(enable_thinking=False),
                name=SubAgentEnum.GREET.value,
                system_prompt=AGENT_PROMPT_GREET,
                context_schema=AppAgentContext,
                state_schema=AppAgentState,
                middleware=[
                    SkillsMiddleware(
                        loader=RemoteSkillLoader(
                            ["https://raw.githubusercontent.com/dxx/agent-template/refs/heads/main/src/skills/greet/SKILL.md"]
                        ),
                        grouped_tools={
                            "greet": [greet],
                        },
                    )
                ],
            )
        
        super().__init__(
            name=SubAgentEnum.GREET.value,
            description=AGENT_DESCRIPTION_GREET,
            agent=agent
        )
