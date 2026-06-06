from pathlib import Path

from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.memory.context import AppAgentContext
from agent.memory.state import AppAgentState
from agent.middleware import RouteTaskAgent
from agent.tools import greet
from agent.middleware.prebuild.skills import SkillsMiddleware


class GreetAgent(RouteTaskAgent):
    """路由编排使用的招待代理。"""

    def __init__(self):

        project_root = Path(__file__).resolve().parent.parent.parent
        skill_dir = project_root.joinpath("skills")

        agent =  create_agent(
                model=create_chat_model(enable_thinking=False),
                name="greet",
                system_prompt="你是一个专业的招待助手，擅长和用户打招呼。",
                context_schema=AppAgentContext,
                state_schema=AppAgentState,
                middleware=[
                    SkillsMiddleware(
                        dirs=[str(skill_dir)],
                        grouped_tools={
                            "greet": [greet],
                        },
                    )
                ],
            )
        
        super().__init__(
            name="greet",
            description="擅长和用户打招呼",
            agent=agent
        )
