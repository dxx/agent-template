from pathlib import Path
from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.subagents import SubAgentEnum
from agent.middleware import SubAgent
from agent.prompts import AGENT_PROMPT_RESEARCH, AGENT_DESCRIPTION_RESEARCH
from agent.memory import AppAgentContext
from agent.middleware import MCPClientMiddleware


class ReseachAgent(SubAgent):
    
    def __init__(self):

        agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.RESEARCH.value,
            system_prompt=AGENT_PROMPT_RESEARCH,
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
                                "--from",
                                "arxiv-mcp-server==0.4.12",
                                "arxiv-mcp-server",
                                "--storage-path",
                                f"{Path.cwd()}/arxiv/paper"
                            ]
                        }
                    }
                )
            ]
        )
        
        super().__init__(
            name=SubAgentEnum.RESEARCH.value,
            description=AGENT_DESCRIPTION_RESEARCH,
            agent=agent
        )
