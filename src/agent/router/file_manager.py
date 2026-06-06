from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.agents.middleware.types import AgentState

from agent.hitl import approve
from agent.llm import create_chat_model
from agent.subagents import SubAgentEnum
from agent.memory.context import AppAgentContext
from agent.prompts import AGENT_FILE_MANAGER_PROMPT
from agent.middleware import RouteTaskAgent
from agent.tools import read_file, write_file


class FileManagerAgent(RouteTaskAgent):
    """路由编排使用的文件管理代理。"""

    def __init__(self):

        agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name=SubAgentEnum.FILE_MANAGER.value,
            system_prompt=AGENT_FILE_MANAGER_PROMPT,
            context_schema=AppAgentContext,
            tools=[read_file, write_file],
            middleware=[
                HumanInTheLoopMiddleware[AgentState[Any], AppAgentContext, Any](
                    interrupt_on={
                        "write_file": {
                            "allowed_decisions": approve.default_allowed_decisions,
                            "description": approve.default_descript_callable,
                        },
                        "read_file": {
                            "allowed_decisions": approve.default_allowed_decisions,
                            "description": "读取文件需要审批",
                        },
                    }
                )
            ],
        )
        
        super().__init__(
            name=SubAgentEnum.FILE_MANAGER.value,
            description="擅长对文件进行管理",
            agent=agent
        )
