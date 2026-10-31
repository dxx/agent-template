from langchain.agents import create_agent
from pathlib import Path

from agent.llm import create_chat_model
from agent.middleware import SubTaskAgent, SkillsMiddleware
from agent.subagents import SubAgentEnum
from agent.prompts import AGENT_PROMPT_GREETING, AGENT_DESCRIPTION_GREETING
from agent.skills import DirectorySkillLoader
from agent.tools import greet
from agent.memory import AppAgentContext, AppAgentState

class GreetingAgent(SubTaskAgent):
    """带有 Skills 的 Agent"""
    def __init__(self):
        
        # 寻找项目 src 目录
        project_root = Path(__file__).resolve().parent.parent.parent

        skill_dir = project_root.joinpath("skills")

        agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name=SubAgentEnum.GREETING.value,
            system_prompt=AGENT_PROMPT_GREETING,
            context_schema=AppAgentContext,
            # 子代理需要访问 state 时配置
            state_schema=AppAgentState,
            # 安装 skills 中间件
            middleware=[
                SkillsMiddleware(
                    loader=DirectorySkillLoader([str(skill_dir)]),
                    grouped_tools={
                        # 当使用 greeting skill 时动态加载 greet 工具
                        "greeting": [greet]
                    }
                )
            ]
        )

        super().__init__(
            name=SubAgentEnum.GREETING.value,
            description=AGENT_DESCRIPTION_GREETING,
            agent=agent
        )
