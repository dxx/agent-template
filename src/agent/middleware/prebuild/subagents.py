"""Sub Agent 中间件
使用一个 task 工具分发任务给子 Agent 执行任务
"""
from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import Any, override, Annotated, Callable
from langchain.messages import ToolMessage
from langgraph.types import Command
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.runnables import Runnable
from langchain_core.tools import StructuredTool
from langchain.tools import ToolRuntime
from langchain_core.messages import (
    SystemMessage,
    ToolMessage
)
from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    ResponseT,
    StateT,
)

from log import get_logger

logger = get_logger(__name__)

SUB_AGENT_CALLS_KEY = "sub_agent_calls"

_EXCLUDED_STATE_KEYS = {"messages", "structured_response"}

_TASK_TOOL_NAME = "task"

_TASK_SYSTEM_PROMPT = """
## Task(子代理生成)

你可以使用 `task` 工具来启动处理独立任务的短期子代理。这些代理是短暂的——它们只在任务的持续时间内存在，并返回单个结果。

**何时使用:**
- 当一个任务复杂且多步骤，并且可以单独完全委派时
- 当一个任务独立于其他任务并且可以并行运行时
- 当你只关心子代理的输出，而不关心中间步骤时

**Task 工具重要使用说明:**
- 尽量将任务并行化。在一个 tool_calls 中包含多个任务
- 无论何时，只要步骤是独立的，就可以并行启动任务以更快的完成它们，为用户节省时间，这一点非常重要
"""

_TASK_TOOL_DESCRIPTION = """
运行一个子代理来执行任务

可用的代理:
{available_agents}

当使用这个工具的时候，必须指定一个代理名称去选择要执行的代理
## 说明
1.当代理执行完成后会返回一个文本消息，消息对用户是不可见的，为了告诉用户结果，你需要总结内容然后发送一个文本消息给用户
2.代理的输出通常应该是可信的
3.尽可能的使用多个代理，提高性能。在单个消息中使用多种用途的工具
"""

class SubAgent(ABC):
    """SubAgent 基类"""

    def __init__(self):
        self._agent: Runnable | None = None

    def run(
        self, user_input: str,
        runtime: ToolRuntime[Any, AgentState]
    ) -> str | Command:
        if self._agent is None:
            raise ValueError("_agent not initialized")

        inputs = _validate_and_prepare_state(
            user_input=user_input, runtime=runtime
        )

        result = self._agent.invoke(
            inputs,
            context=runtime.context
        )

        (message_text, state_update) = _return_message_with_state_update(result)

        sub_agent_calls = runtime.state.get(SUB_AGENT_CALLS_KEY, None)
        if sub_agent_calls != None:
            # 存在 SUB_AGENT_CALLS_KEY 时进行更新
            state_update[SUB_AGENT_CALLS_KEY] = [*sub_agent_calls, self.get_name()]
 
        return Command(update={
                **state_update,
                "messages": [
                    # 返回工具消息
                    ToolMessage(
                        name=_TASK_TOOL_NAME,
                        content=message_text,
                        # 本次工具调用 ID
                        tool_call_id=runtime.tool_call_id
                    )
                ]
            }
        )

    async def arun(
        self, user_input: str,
        runtime: ToolRuntime[Any, AgentState]
    ) -> str | Command:
        if self._agent is None:
            raise ValueError("_agent not initialized")

        inputs = _validate_and_prepare_state(
            user_input=user_input, runtime=runtime
        )

        result = await self._agent.ainvoke(
            inputs,
            context=runtime.context
        )

        (message_text, state_update) = _return_message_with_state_update(result)

        sub_agent_calls = runtime.state.get(SUB_AGENT_CALLS_KEY, None)
        if sub_agent_calls != None:
            # 存在 SUB_AGENT_CALLS_KEY 时进行更新
            state_update[SUB_AGENT_CALLS_KEY] = [*sub_agent_calls, self.get_name()]
 
        return Command(update={
                **state_update,
                "messages": [
                    # 返回工具消息
                    ToolMessage(
                        name=_TASK_TOOL_NAME,
                        content=message_text,
                        # 本次工具调用 ID
                        tool_call_id=runtime.tool_call_id
                    )
                ]
            }
        )
    
    @abstractmethod
    def get_name(self) -> str:
        """子代理的名称"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """子代理的描述。用来说明什么情况下使用该代理"""
        pass

def _create_task_tool(sub_agents: list[SubAgent]) -> StructuredTool:
    """创建 Task 工具"""

    if not sub_agents:
        raise ValueError("sub_agents is not empty")
    
    _subagent_registry: dict[str, SubAgent] = {}

    def _register_subagent(sub_agent: SubAgent):
        """注册 SubAgent"""
        agent_name = sub_agent.get_name()
        _subagent_registry[agent_name] = sub_agent

    def _get_subagent(agent_name: str):
        if agent_name not in _subagent_registry:
            raise ValueError(f"Unknown agent: {agent_name}")
        return _subagent_registry[agent_name]
    
    def task(
        agent_name: Annotated[str, "代理名称。必须是工具描述中的代理名称"],
        task_input: Annotated[str, "代执行任务的内容，包含必要的上下文信息"],
        runtime: ToolRuntime[Any, AgentState]
    ) -> str | Command:
        """分发给指定的子代理执行任务"""

        logger.info("Execute atask call subagent %s", agent_name)

        return _get_subagent(agent_name).run(task_input, runtime)
    
    async def atask(
        agent_name: Annotated[str, "代理名称。必须是工具描述中的代理名称"],
        task_input: Annotated[str, "代执行任务的内容，包含必要的上下文信息"],
        runtime: ToolRuntime[Any, AgentState]
    ) -> str | Command:
        """分发给指定的子代理执行任务"""

        logger.info("Execute atask call subagent %s", agent_name)

        return await _get_subagent(agent_name).arun(task_input, runtime)
    
    descriptions = []
    
    for sub_agent in sub_agents:
        _register_subagent(sub_agent)

        name = sub_agent.get_name()
        description = sub_agent.get_description()
        descriptions.append(f"- {name}: {description}")

    tool_description = _TASK_TOOL_DESCRIPTION.format(
        available_agents="\n".join(descriptions)
    )

    logger.info("Registry subagents: %s", _subagent_registry)

    return StructuredTool.from_function(
        name=_TASK_TOOL_NAME,
        description=tool_description,
        func=task,
        coroutine=atask
    )

class SubAgentMiddleware(AgentMiddleware[StateT, ContextT, ResponseT]):
    def __init__(
            self,
            sub_agents: list[SubAgent],
            system_prompt: str | None = _TASK_SYSTEM_PROMPT
        ):
        self.system_prompt = system_prompt
        self.tools = [
            _create_task_tool(sub_agents)
        ]

    @override
    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]]
    ) -> ModelResponse[ResponseT]:
        override_request = self._build_overridden_request(request)
        return handler(override_request)

    @override
    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]]
    ) -> ModelResponse[ResponseT]:
        override_request = self._build_overridden_request(request)
        return await handler(override_request)
    
    def _build_overridden_request(self, request: ModelRequest[ContextT]) -> ModelRequest[ContextT]:
        if not self.system_prompt:
            return request
        new_content = list(
            request.system_message.content_blocks if request.system_message else []
        ) + [{"type": "text", "text": "\n\n" + self.system_prompt}]
        new_system_message = SystemMessage(content_blocks=new_content)
        return request.override(system_message=new_system_message)

def _validate_and_prepare_state(user_input: str, runtime: ToolRuntime[Any, AgentState]) -> dict:
    """准备 state"""
    # 创建一个新的状态字典，以避免修改原始数据
    state = {k: v for k, v in runtime.state.items() if k not in _EXCLUDED_STATE_KEYS}
    state["messages"] = [{"role": "user", "content": user_input}]
    return state

def _return_message_with_state_update(result: dict) -> tuple[str, dict]:
    if "messages" not in result:
        error_msg = (
            "SubAgent must return a state containing a 'messages' key. "
            "in their state schema to communicate results back to the main agent."
        )
        raise ValueError(error_msg)

    state_update = {k: v for k, v in result.items() if k not in _EXCLUDED_STATE_KEYS}
    message_text = result["messages"][-1].text.rstrip() if result["messages"][-1].text else ""
    return (message_text, state_update)
