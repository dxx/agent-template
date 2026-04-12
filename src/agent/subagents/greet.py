from langchain.agents import create_agent
from pathlib import Path

from agent.llm import create_chat_model
from agent.middleware import SubAgent, SkillsMiddleware
from agent.tools import read_file, greet
from agent.memory import AppAgentContext, AppAgentState

class GreetAgent(SubAgent):
    """带有 Skills 的 Agent"""
    def __init__(self):
        super().__init__()

        # 寻找项目 src 目录
        project_root = Path(__file__).resolve().parent.parent.parent

        skill_dir = project_root.joinpath("skills")

        self._agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name="greet",
            system_prompt="你是一个专业的招待助手，擅长和用户打招呼。",
            context_schema=AppAgentContext,
            # 子代理需要访问 state 时配置
            state_schema=AppAgentState,
            # read_file，当 skills 中需要读取参考文件时使用
            tools=[read_file],
            # 安装 skills 中间件
            middleware=[
                SkillsMiddleware(
                    dirs=[str(skill_dir)],
                    grouped_tools={
                        # 当使用 greet skill 时动态加载 greet 工具
                        "greet": [greet]
                    }
                )
            ]
        )

    def get_name(self) -> str:
        return "greet"

    def get_description(self) -> str:
        return "擅长和用户打招呼"
