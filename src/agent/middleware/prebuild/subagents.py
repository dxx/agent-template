"""Sub Agent 中间件
使用一个 task 工具分发任务给子 Agent 执行任务
"""
from collections.abc import Awaitable
from typing import Any, override, Annotated, Callable, Literal
from langchain.messages import ToolMessage
from langgraph.types import Command, StreamMode
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.runnables import Runnable, RunnableConfig
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

class SubAgent:
    """SubAgent 基类"""

    def __init__(self, *, name: str, description: str, agent: Runnable[Any, Any]):
        self.name = name
        self.description = description
        self._agent = agent

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self.description

    def invoke(
        self,
        input: dict[str, Any] | Command[Any] | None,
        config: RunnableConfig | None = None,
        *,
        context: Any | None = None,
        stream_mode: StreamMode = "values",
        version: Literal["v1", "v2"] = "v1",
        **kwargs: Any,
    ) -> dict[str, Any] | Any:
        return self._agent.invoke(
            input,
            config=config,
            context=context,
            stream_mode=stream_mode,
            version=version,
            **kwargs,
        )

    async def ainvoke(
        self,
        input: dict[str, Any] | Command[Any] | None,
        config: RunnableConfig | None = None,
        *,
        context: Any | None = None,
        stream_mode: StreamMode = "values",
        version: Literal["v1", "v2"] = "v1",
        **kwargs: Any,
    ) -> dict[str, Any] | Any:
        return await self._agent.ainvoke(
            input,
            config=config,
            context=context,
            stream_mode=stream_mode,
            version=version,
            **kwargs,
        )


def _create_task_tool(sub_agents: list[SubAgent]) -> StructuredTool:
    """创建 Task 工具"""

    if not sub_agents:
        raise ValueError("sub_agents is not empty")
    
    _subagent_registry: dict[str, SubAgent] = {}

    def _register_subagent(sub_agent: SubAgent):
        """注册 SubAgent"""
        agent_name = sub_agent.get_name()
        _subagent_registry[agent_name] = sub_agent

    def _get_subagent(agent_name: str) -> SubAgent:
        if agent_name not in _subagent_registry:
            raise ValueError(f"Unknown agent: {agent_name}")
        return _subagent_registry[agent_name]
    
    def task(
        agent_name: Annotated[str, "代理名称。必须是工具描述中的代理名称"],
        task_input: Annotated[str, "代执行任务的内容，包含必要的上下文信息"],
        runtime: ToolRuntime[ContextT, AgentState]
    ) -> str | Command:
        """分发给指定的子代理执行任务"""

        logger.info("Execute atask call subagent %s", agent_name)

        agent = _get_subagent(agent_name)

        inputs = _prepare_state(
            content=task_input, runtime=runtime
        )

        result = agent.invoke(
            inputs,
            context=runtime.context
        )

        (message_text, state_update) = _return_message_with_state_update(result)

        sub_agent_calls = runtime.state.get(SUB_AGENT_CALLS_KEY, None)
        if sub_agent_calls != None:
            # 存在 SUB_AGENT_CALLS_KEY 时进行更新
            state_update[SUB_AGENT_CALLS_KEY] = [*sub_agent_calls, agent_name]
 
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
    
    async def atask(
        agent_name: Annotated[str, "代理名称。必须是工具描述中的代理名称"],
        task_input: Annotated[str, "代执行任务的内容，包含必要的上下文信息"],
        runtime: ToolRuntime[ContextT, AgentState]
    ) -> str | Command:
        """分发给指定的子代理执行任务"""

        logger.info("Execute atask call subagent %s", agent_name)

        agent = _get_subagent(agent_name)

        inputs = _prepare_state(
            content=task_input, runtime=runtime
        )

        result = await agent.ainvoke(
            inputs,
            context=runtime.context
        )

        (message_text, state_update) = _return_message_with_state_update(result)

        sub_agent_calls = runtime.state.get(SUB_AGENT_CALLS_KEY, None)
        if sub_agent_calls != None:
            # 存在 SUB_AGENT_CALLS_KEY 时进行更新
            state_update[SUB_AGENT_CALLS_KEY] = [*sub_agent_calls, agent_name]
 
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
        """初始化 Sub Agent 中间件。

        Args:
            sub_agents: 可被 `task` 工具调度的子代理列表。每个子代理必须实现
                `get_name()` 和 `get_description()`。
            system_prompt: 注入到模型系统提示词中的子代理使用说明。传入 `None` 时，
                不追加子代理调度提示词，但仍会注册 `task` 工具。
        """
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


def _prepare_state(content: str, runtime: ToolRuntime[ContextT, AgentState]) -> dict:
    """准备 state"""
    # 创建一个新的状态字典，以避免修改原始数据
    state = {k: v for k, v in runtime.state.items() if k not in _EXCLUDED_STATE_KEYS}
    state["messages"] = [{"role": "user", "content": content}]
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
