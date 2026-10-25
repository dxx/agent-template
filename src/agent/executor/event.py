"""Agent 执行事件。

把 Agent 流式执行过程中的事件统一抽象出来，保留 LangChain / LangGraph 的原始结构，
上层按事件类型渲染成各自的响应格式。

事件来源对应 `astream` 的两种流模式：

- `messages`: LLM 输出的文本分片，对应 `MESSAGE` 事件
- `updates`: graph 中节点的数据，对应 `MODEL`、`TOOLS`、`INTERRUPT`、`UPDATE` 事件

事件类型：

- `MESSAGE`: LLM 输出的文本分片
- `MODEL`: 模型节点执行的消息
- `TOOLS`: 工具节点执行的消息
- `INTERRUPT`: 人工审批中断
- `UPDATE`: 状态更新

节点收集：`model`、`tools`、`__interrupt__` 始终收集，其它节点（router、join 等）
需要通过 `stream_events` 的 `extra_nodes` 参数指定。
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from langchain_core.messages import AnyMessage
from langgraph.types import Interrupt


class EventType(StrEnum):
    """事件类型

    MESSAGE: LLM 输出的文本分片
    MODEL: 模型节点执行的消息
    TOOLS: 工具节点执行的消息
    INTERRUPT: 人工审批中断
    UPDATE: 状态更新
    """

    MESSAGE = "message"
    MODEL = "model"
    TOOLS = "tools"
    INTERRUPT = "interrupt"
    UPDATE = "update"


@dataclass
class Event:
    """Agent 执行事件"""

    event_type: EventType
    """事件类型"""

    msg_id: str = ""
    """消息 id。同一条消息的多个事件共用一个 id"""

    chunk: str = ""
    """增量文本内容。message 事件使用"""

    message: AnyMessage | None = None
    """原始消息。按事件类型区分：

    - message 事件：`AIMessageChunk`，LLM 输出的文本分片
    - model 事件：`AIMessage`，模型节点执行的消息
    - tools 事件：`ToolMessage`，工具节点执行的消息
    """

    interrupt: Interrupt | None = None
    """中断信息。interrupt 事件使用。

    value 中包含 action_requests、review_configs，
    action_requests 中带有工具的调用参数
    """

    node: str = ""
    """产生事件的 graph 节点名。如 router、join 等，注意 model 和 tools 不包含在里面"""

    state: dict[str, Any] = field(default_factory=dict)
    """状态数据。update 事件使用"""
