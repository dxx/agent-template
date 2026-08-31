from pathlib import Path

from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.memory.context import AppAgentContext
from agent.subagents import SubAgentEnum
from agent.prompts import AGENT_PROMPT_RESEARCH, AGENT_DESCRIPTION_RESEARCH
from agent.middleware import RouteTaskAgent
from agent.middleware.prebuild.mcp_client import MCPClientMiddleware

class ResearchAgent(RouteTaskAgent):
    """路由编排使用的研究代理。"""

    def __init__(self):

        agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.RESEARCH.value,
            system_prompt=AGENT_PROMPT_RESEARCH,
            context_schema=AppAgentContext,
            middleware=[
                MCPClientMiddleware(
                    mcp_config={
                        "arxiv": {
                            "transport": "stdio",
                            "command": "uvx",
                            "args": [
                                "--from",
                                "arxiv-mcp-server==0.4.12",
                                "arxiv-mcp-server",
                                "--storage-path",
                                f"{Path.cwd()}/arxiv/paper",
                            ],
                        }
                    }
                )
            ],
        )
        
        super().__init__(
            name=SubAgentEnum.RESEARCH.value,
            description=AGENT_DESCRIPTION_RESEARCH,
            agent=agent
        )
