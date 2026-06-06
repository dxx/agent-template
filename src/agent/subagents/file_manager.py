from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentState
from typing import Any

from agent.llm import create_chat_model
from agent.subagents import SubAgentEnum
from agent.hitl import approve
from agent.prompts import AGENT_FILE_MANAGER_PROMPT
from agent.tools import read_file, write_file
from agent.memory import AppAgentContext
from agent.middleware import SubAgent, HumanInTheLoopMiddleware

class FileManagerAgent(SubAgent):

    def __init__(self):
        
        agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name=SubAgentEnum.FILE_MANAGER.value,
            system_prompt=AGENT_FILE_MANAGER_PROMPT,
            context_schema=AppAgentContext,
            tools=[read_file, write_file],
            middleware=[HumanInTheLoopMiddleware[AgentState[Any], AppAgentContext, Any](
                interrupt_on={
                    "write_file": {
                        # 可选的审批
                        "allowed_decisions": approve.default_allowed_decisions,
                        # 审批描述
                        "description": approve.default_descript_callable
                    },
                    "read_file": {
                        # 可选的审批
                        "allowed_decisions": approve.default_allowed_decisions,
                        # 审批描述
                        "description": "读取文件需要审批"
                    },
                }
            )]
        )
        
        super().__init__(
            name=SubAgentEnum.FILE_MANAGER.value,
            description="擅长对文件进行管理",
            agent=agent
        )
