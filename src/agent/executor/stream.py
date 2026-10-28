"""Agent 执行器。

把 Agent 流式执行过程（`astream`）转换成统一的执行事件。
"""

import uuid
from collections.abc import AsyncIterator
from typing import Any, TypeVar, cast

from langchain_core.messages import AIMessageChunk, AnyMessage
from langchain_core.runnables import RunnableConfig
from langchain.agents import AgentState
from langgraph.types import Command, StreamPart
from langgraph.graph.state import CompiledStateGraph

from agent.executor.event import Event, EventType
from agent.memory import AppAgentContext
from log import get_logger

logger = get_logger(__name__)

# Agent 的状态类型
StateT = TypeVar("StateT", bound=AgentState)

# graph 中的节点名
_NODE_MODEL = "model"
_NODE_TOOLS = "tools"
_NODE_INTERRUPT = "__interrupt__"

# 根 graph 的命名空间
_ROOT_NS = ()

# SummarizationMiddleware 汇总节点的标识
_LC_SOURCE_SUMMARIZATION = "summarization"


async def stream_events(
    agent: CompiledStateGraph[StateT, AppAgentContext, Any, Any],
    inputs: StateT | Command | dict[str, Any],
    config: RunnableConfig,
    context: AppAgentContext,
    subgraphs: bool = True,
    extra_agents: list[str] | None = None,
    extra_nodes: list[str] | None = None,
) -> AsyncIterator[Event]:
    """执行 Agent 流式处理，输出执行事件。

    Args:
        agent: 执行主体。create_main_agent 或 create_router_agent 创建的 graph
        inputs: 输入内容。消息或者 Command
        config: 运行配置。包含 thread_id
        context: 运行上下文
        subgraphs: 是否开启子 graph 流事件
        extra_agents: 额外收集消息的 Agent 名称。主 Agent 的消息始终收集
        extra_nodes: 额外收集更新数据的节点名。model、tools、__interrupt__ 始终收集
    """

    collect_nodes = set(extra_nodes) if extra_nodes else None

    # 主 Agent 的消息始终收集
    collect_agents = {agent.get_name()}
    if extra_agents:
        collect_agents.update(extra_agents)

    async for chunk in agent.astream(
        inputs,
        config,
        context=context,
        stream_mode=[
            "updates", "messages"
        ],
        version="v2",
        # 开启子 graph 流事件
        subgraphs=subgraphs,
    ):
        for event in _parse_chunk(chunk, collect_agents, collect_nodes):
            yield event


def _parse_chunk(
    chunk: StreamPart[Any, Any],
    agents: set[str] | None = None,
    extra_nodes: set[str] | None = None,
) -> list[Event]:
    """把 astream 的一个数据块转换成事件列表。

    chunk 结构示例：

    ```
    {"type": "messages", "data": (token, metadata), "ns": ()}
    {"type": "updates", "data": {"model": {"messages": [...]}}, "ns": ()}
    ```

    Args:
        chunk: astream 的数据块
        agents: 收集消息的 Agent 名称
        extra_nodes: 额外收集更新数据的节点名
    """

    chunk_type = chunk["type"]

    if chunk_type == "messages":
        data = cast(tuple[AnyMessage, dict[str, Any]], chunk["data"])
        return _parse_messages(data, agents)

    if chunk_type == "updates":
        data = cast(dict[str, Any], chunk["data"])
        return _parse_updates(data, chunk["ns"], extra_nodes)

    return []


def _parse_messages(data: tuple[AnyMessage, dict[str, Any]], agents: set[str] | None = None) -> list[Event]:
    """解析 messages 流。LLM 输出的文本分片。

    Args:
        data: 消息分片和元数据
        agents: 收集消息的 Agent 名称。未指定时收集所有 Agent 的消息
    """

    if not data:
        return []

    token, metadata = data
    metadata = metadata or {}

    if metadata.get("lc_source") == _LC_SOURCE_SUMMARIZATION:
        # SummarizationMiddleware 汇总节点忽略
        return []

    if not isinstance(token, AIMessageChunk):
        return []

    if agents is not None and metadata.get("lc_agent_name") not in agents:
        # 只返回指定 agent 的消息
        return []

    if not token.text:
        # 没有文本内容
        return []

    return [
        Event(
            event_type=EventType.MESSAGE,
            msg_id=token.id if token.id else str(uuid.uuid4()),
            chunk=token.text,
            message=token,
        )
    ]


def _parse_updates(data: Any, ns: tuple[str, ...], extra_nodes: set[str] | None = None) -> list[Event]:
    """解析 updates 流。graph 中节点的数据。

    Args:
        data: 节点的数据
        ns: 节点所在的命名空间
        extra_nodes: 额外收集更新数据的节点名。model、tools、__interrupt__ 始终收集
    """

    events: list[Event] = []

    for node, update in (data or {}).items():
        if node == _NODE_MODEL:
            event = _parse_node_message(EventType.MODEL, update)
            if event:
                events.append(event)
        elif node == _NODE_TOOLS:
            event = _parse_node_message(EventType.TOOLS, update)
            if event:
                events.append(event)
        elif node == _NODE_INTERRUPT:
            if ns != _ROOT_NS:
                # 只返回根 graph 触发的中断，子 graph 触发的不返回，避免重复提示
                continue
            events.append(
                Event(
                    event_type=EventType.INTERRUPT,
                    msg_id=str(uuid.uuid4()),
                    # 同一 superstep 可能产生多个中断
                    interrupts=list(update),
                )
            )
        elif extra_nodes and node in extra_nodes:
            # 其它节点的数据。router、join 等
            events.append(
                Event(
                    event_type=EventType.UPDATE,
                    node=node,
                    state=update or {},
                )
            )

    return events


def _parse_node_message(event_type: EventType, update: Any) -> Event | None:
    """解析 model、tools 节点的数据。节点中最新的那条消息。"""

    messages = (update or {}).get("messages") or []
    if not messages:
        return None

    message = messages[-1]

    return Event(
        event_type=event_type,
        msg_id=message.id if message.id else str(uuid.uuid4()),
        message=message,
    )
