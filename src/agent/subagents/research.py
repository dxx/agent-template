from pathlib import Path
from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.subagents import SubAgentEnum
from agent.middleware import SubAgent
from agent.prompts import AGENT_RESEARCH_PROMPT
from agent.memory import AppAgentContext
from agent.middleware import MCPClientMiddleware


class ReseachAgent(SubAgent):
    def __init__(self):
        super().__init__()
        self._agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.RESEARCH.value,
            system_prompt=AGENT_RESEARCH_PROMPT,
            context_schema=AppAgentContext,
            middleware=[
                # 安装 MCP 中间件
                MCPClientMiddleware(
                    mcp_config={
                        # ArXiv AI搜索服务
                        "arxiv": {
                            "transport": "stdio",
                            "command": "uvx",
                            "args": [
                                "arxiv-mcp-server",
                                "--storage-path",
                                f"{Path.cwd()}/arxiv/paper"
                            ]
                        }
                    }
                )
            ]
        )

    def get_name(self) -> str:
        return SubAgentEnum.RESEARCH.value

    def get_description(self) -> str:
        return "擅长从多个信息源收集和整理信息"
