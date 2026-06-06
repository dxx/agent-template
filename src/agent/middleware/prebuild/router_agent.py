"""Route Agent 中间件

提供一个 `route` 工具，由主 Agent 主动调用后，再通过内部
StateGraph 路由到多个任务 Agent 执行。

`RouteAgentMiddleware` 的内部流程：

1. 向主 Agent 注册 `route` 工具
2. 工具从当前 `runtime.state["messages"]` 中提取最近一条用户输入
3. 内部 `_RouteGraphAgent` 使用 `StateGraph` 执行 `router → call_agent → join`
4. `router` 节点用 LLM 生成结构化 `RouterResult`
5. `call_agent` 节点根据路由结果调用一个或多个 `RouteTaskAgent`
6. `join` 节点返回单个 `final_result`

路由任务代理通过 `RouteTaskAgent` 包装普通 LangChain/LangGraph agent，必须提供：

- `name`: 路由模型可选择的代理名称
- `description`: 路由模型判断何时使用该代理的描述
- `agent`: 实际执行任务的 Runnable
"""

from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Literal, override, cast

from langchain.agents.middleware import ModelRequest, ModelResponse
from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    ResponseT,
    StateT,
)
from langchain.chat_models import BaseChatModel
from langchain.tools import ToolRuntime
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from langchain_core.tools import StructuredTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, Send, StreamMode

from agent.memory.router_state import (
    AgentOutput,
    AgentRouter,
    RouterResult,
    RouterState,
)

from log import get_logger

logger = get_logger(__name__)

_ROUTER_TOOL_NAME = "route"

_ROUTER_SYSTEM_PROMPT = """
## Router(路由任务)

你可以使用 `route` 工具通过路由代理处理用户问题。

当用户请求需要选择合适的专业代理、拆分给多个代理协作，或者你不确定应该由哪个
代理处理时，调用该工具。
"""

_ROUTER_PROMPT = """
你是一个代理路由器，负责把用户请求拆分并分配给合适的代理执行。

可用代理:
{agents}

要求:
1. 只能选择可用代理列表中的 name。
2. 如果一个请求需要多个代理协作，可以返回多个 routers。
3. 每个 router.query 应该是分配给该代理的完整、独立任务描述。
4. 如果没有合适代理，返回空 routers。列如 `{{"routers": []}}`。
"""


class RouteTaskAgent:
    """路由编排使用的子代理基类。"""

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


class _RouteGraphAgent(RouteTaskAgent):
    """内部路由图。"""

    def __init__(
        self,
        *,
        name: str,
        agents: Sequence[RouteTaskAgent],
        router_model: BaseChatModel,
        merge_model: BaseChatModel | None = None,
        state_schema: type[RouterState] = RouterState,
        context_schema: type[Any] | None = None,
        system_prompt: str = _ROUTER_PROMPT,
    ):
        self._name = name
        self._router_model = router_model
        self._merge_model = merge_model or router_model
        self._json_output_parser = JsonOutputParser(pydantic_object=RouterResult)
        self._agents = self._build_agent_registry(agents)
        self._system_prompt = system_prompt.format(
            agents=self._format_agents(self._agents)
        )

        logger.info("Registry router agents: %s", self._agents)

        self._graph = self._compile_graph(
            state_schema=state_schema,
            context_schema=context_schema,
        )

        super().__init__(name=name, description="路由图代理", agent=self._graph)

    def get_graph(self) -> CompiledStateGraph:
        return self._graph

    def _compile_graph(
        self,
        *,
        state_schema: type[RouterState],
        context_schema: type[Any] | None,
    ) -> CompiledStateGraph:
        graph = StateGraph(
            state_schema=state_schema,
            context_schema=context_schema,
        )
        graph.add_node("router", RunnableLambda(self._route, afunc=self._aroute))
        graph.add_node("call_agent", RunnableLambda(self._call_agent, afunc=self._acall_agent))
        graph.add_node("join", RunnableLambda(self._join, afunc=self._ajoin))

        graph.add_edge(START, "router")
        graph.add_conditional_edges("router", self._dispatch)
        graph.add_edge("call_agent", "join")
        graph.add_edge("join", END)

        return graph.compile(name=self._name)

    def _route(self, state: RouterState) -> dict[str, list[AgentRouter]]:
        if not state["query"]:
            return {"routers": []}

        result = self._parse_router_result(
            self._router_model.invoke(
                self._build_router_messages(state["query"]),
                config={"tags": ["nostream"], "metadata": {"source": self.get_name}},
            ).text
        )
        return {"routers": self._filter_routers(result.routers)}

    async def _aroute(self, state: RouterState) -> dict[str, list[AgentRouter]]:
        if not state["query"]:
            return {"routers": []}

        result = self._parse_router_result(
            (
                await self._router_model.ainvoke(
                    self._build_router_messages(state["query"]),
                    config={"tags": ["nostream"], "metadata": {"source": self.get_name}},
                )
            ).text
        )
        return {"routers": self._filter_routers(result.routers)}

    def _dispatch(self, state: RouterState) -> list[Send] | str:
        routers = state.get("routers", [])
        if not routers:
            return "join"
        return [
            Send(
                "call_agent",
                {
                    "query": state["query"],
                    "routers": routers,
                    "router": router,
                },
            )
            for router in routers
        ]

    def _call_agent(self, state: RouterState, config: RunnableConfig) -> dict[str, list[AgentOutput]]:
        router = self._get_current_router(state)
        agent = self._agents[router.name]
        result = agent.invoke(
            self._build_agent_input(state, router),
            context=self._get_runtime_context(config),
        )
        return {"results": [self._build_agent_output(router.name, result)]}

    async def _acall_agent(
        self,
        state: RouterState,
        config: RunnableConfig,
    ) -> dict[str, list[AgentOutput]]:
        router = self._get_current_router(state)
        agent = self._agents[router.name]
        result = await agent.ainvoke(
            self._build_agent_input(state, router),
            context=self._get_runtime_context(config),
        )
        return {"results": [self._build_agent_output(router.name, result)]}

    def _join(self, state: RouterState) -> dict[str, Any]:
        results = state.get("results", [])
        if not results:
            return {"final_result": "抱歉，没有处理结果"}
        if len(results) == 1:
            return {"final_result": results[0]["result"], "results": []}
        message = self._merge_model.invoke(
            self._build_merge_messages(results),
            config={"tags": ["nostream"], "metadata": {"source": self.get_name}},
        )
        return {"final_result": self._extract_result_text(message), "results": []}

    async def _ajoin(self, state: RouterState) -> dict[str, Any]:
        results = state.get("results", [])
        if not results:
            return {"final_result": "抱歉，没有处理结果"}
        if len(results) == 1:
            return {"final_result": results[0]["result"], "results": []}
        message = await self._merge_model.ainvoke(
            self._build_merge_messages(results),
            config={"tags": ["nostream"], "metadata": {"source": self.get_name}},
        )
        return {"final_result": self._extract_result_text(message), "results": []}

    def _join_text(self, results: list[AgentOutput]) -> str:
        return "\n\n".join(
            "[{source}]\n{result}".format(
                source=result["source"],
                result=result["result"],
            )
            for result in results
        )

    def _build_merge_messages(self, results: list[AgentOutput]) -> list[BaseMessage]:
        return [
            SystemMessage(
                content=(
                    "你是一个专业的结果合并助手。请将多个代理的处理结果合并为一个"
                    "清晰、连贯、无重复的中文回答。保留关键信息，不要编造未提供的内容。"
                )
            ),
            HumanMessage(content="请合并以下多个代理的结果：\n\n" + self._join_text(results)),
        ]

    def _build_router_messages(self, query: str) -> list[BaseMessage]:
        return [
            SystemMessage(
                content=(
                    self._system_prompt
                    + "\n\n"
                    + self._json_output_parser.get_format_instructions()
                )
            ),
            HumanMessage(content=query),
        ]

    def _parse_router_result(self, text: str) -> RouterResult:
        parsed = self._json_output_parser.parse(text)
        if isinstance(parsed, RouterResult):
            return parsed
        return RouterResult.model_validate(parsed)

    def _filter_routers(self, routers: list[AgentRouter]) -> list[AgentRouter]:
        return [router for router in routers if router.name in self._agents]

    def _build_agent_input(self, state: RouterState, router: AgentRouter) -> dict[str, Any]:
        return {
            **state,
            "messages": [{"role": "user", "content": router.query}],
        }

    def _build_agent_output(self, source: str, result: Any) -> AgentOutput:
        return {
            "source": source,
            "result": self._extract_result_text(result),
        }

    @staticmethod
    def _get_current_router(state: RouterState) -> AgentRouter:
        router = state.get("router")
        if router is None:
            raise ValueError("缺少当前代理路由信息")
        return router

    @staticmethod
    def _get_runtime_context(config: RunnableConfig) -> Any:
        runtime = (config.get("configurable") or {}).get("__pregel_runtime")
        return getattr(runtime, "context", None)

    @staticmethod
    def _extract_result_text(result: Any) -> str:
        if isinstance(result, str):
            return result.rstrip()
        if isinstance(result, dict) and result.get("messages"):
            return _RouteGraphAgent._extract_result_text(result["messages"][-1])
        if isinstance(result, dict):
            return _RouteGraphAgent._extract_result_text(
                result.get("text") or result.get("content") or ""
            )

        text = getattr(result, "text", None)
        if text:
            return str(text).rstrip()

        content = result.content if isinstance(result, BaseMessage) else result
        if isinstance(content, str):
            return content.rstrip()
        if isinstance(content, list):
            return "".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            ).rstrip()
        return str(content).rstrip()

    @staticmethod
    def _build_agent_registry(agents: Sequence[RouteTaskAgent]) -> dict[str, RouteTaskAgent]:
        registry: dict[str, RouteTaskAgent] = {}
        for agent in agents:
            name = agent.get_name()
            if name in registry:
                raise ValueError(f"重复的代理名称: {name}")
            registry[name] = agent
        return registry

    @staticmethod
    def _format_agents(agents: dict[str, RouteTaskAgent]) -> str:
        lines = []
        for name, agent in agents.items():
            description = agent.get_description()
            lines.append(f"- name: {name}\n  description: {description}")
        return "\n".join(lines)


class RouteAgentMiddleware(AgentMiddleware[StateT, ContextT, ResponseT]):
    def __init__(
        self,
        *,
        name: str,
        agents: Sequence[RouteTaskAgent],
        router_model: BaseChatModel,
        merge_model: BaseChatModel | None = None,
        state_schema: type[Any] = RouterState,
        context_schema: type[Any] | None = None,
        system_prompt: str | None = _ROUTER_SYSTEM_PROMPT,
        router_prompt: str = _ROUTER_PROMPT,
        tool_name: str = _ROUTER_TOOL_NAME,
    ):
        """初始化 Route Agent 中间件。

        Args:
            name: 内部路由图名称。
            agents: 可被路由调用的下游任务 Agent 列表。
            router_model: 用于生成结构化路由结果的聊天模型。
            merge_model: 用于合并多个下游 Agent 结果的聊天模型。不传时复用 `router_model`。
            state_schema: 内部 StateGraph 使用的状态结构。需要透传父 Agent state 时，
                传入包含对应字段的 state schema。
            context_schema: 内部 StateGraph 的运行上下文结构。
            system_prompt: 注入主 Agent 系统提示词的工具使用说明。传入 `None` 时不注入。
            router_prompt: 路由模型提示词。不传时使用内置路由提示词。
            tool_name: 注册到主 Agent 的路由工具名称。
        """
        self.system_prompt = system_prompt
        self._router_agent = _RouteGraphAgent(
            name=name,
            agents=agents,
            router_model=router_model,
            merge_model=merge_model,
            state_schema=state_schema,
            context_schema=context_schema,
            system_prompt=router_prompt,
        )
        self.tools = [_create_router_tool(self._router_agent, tool_name)]

    @override
    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT]:
        return handler(self._build_overridden_request(request))

    @override
    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
    ) -> ModelResponse[ResponseT]:
        return await handler(self._build_overridden_request(request))
    
    def get_graph(self) -> CompiledStateGraph:
        return self._router_agent.get_graph()

    def _build_overridden_request(self, request: ModelRequest[ContextT]) -> ModelRequest[ContextT]:
        if not self.system_prompt:
            return request
        new_content = list(
            request.system_message.content_blocks if request.system_message else []
        ) + [{"type": "text", "text": "\n\n" + self.system_prompt}]
        return request.override(system_message=SystemMessage(content_blocks=new_content))


def _create_router_tool(router_agent: _RouteGraphAgent, tool_name: str) -> StructuredTool:
    def route(runtime: ToolRuntime[ContextT, AgentState]) -> str:
        """通过路由处理用户输入。"""
        result = router_agent.invoke(
            _build_router_input(runtime.state),
            context=runtime.context,
        )
        return result["final_result"]

    async def aroute(runtime: ToolRuntime[ContextT, AgentState]) -> str:
        """通过路由处理用户输入。"""
        result = await router_agent.ainvoke(
            _build_router_input(runtime.state),
            context=runtime.context,
        )
        return result["final_result"]

    return StructuredTool.from_function(
        name=tool_name,
        description="通过路由代理处理当前用户输入。",
        func=route,
        coroutine=aroute,
    )


def _build_router_input(state: AgentState) -> dict[str, Any]:
    query = _extract_user_input(state)
    return {
        "query": query,
    }


def _extract_user_input(state: AgentState) -> str:
    messages = state.get("messages", [])
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.text
        if isinstance(message, dict) and message.get("role") == "user":
            return str(message.get("content", ""))
    return ""
