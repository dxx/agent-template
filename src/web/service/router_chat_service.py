import uuid
from collections.abc import AsyncIterator
from typing import Any
from langchain_core.messages import AIMessage, ToolMessage, AIMessageChunk
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from agent.executor import Event, EventType, stream_events
from agent.memory import AppAgentContext
from agent.memory.router_state import AgentTask
from agent.router import get_router_agent, task_agent_holder
from log import get_logger
from web.schemas import (
    AppState,
    Approve,
    ApproveItem,
    RouterChatRequest,
    ChatResponse,
    Decision,
    DecisionItem,
    ResponseMsgTypeEnum,
)
from config import AppEnv, get_settings
from session import format_thread_id

logger = get_logger(__name__)


async def router_chat_response(
    app_state: AppState,
    request: RouterChatRequest,
) -> AsyncIterator[ChatResponse]:
    """路由 Agent 流式对话响应。"""

    router_agent = await get_router_agent()

    content = request.content
    decision = request.decision

    inputs = {
        "messages": [{"role": "user", "content": content}],
    }

    # 解析指定的代理。名称未注册时返回错误
    agents, error = _parse_agents(request.agents)

    if error:
        logger.warning("Invalid agents, error=%s", error)
        yield ChatResponse(
            msg_id=str(uuid.uuid4()),
            msg_type=ResponseMsgTypeEnum.ERROR,
            content=error,
        )
        return

    context = AppAgentContext(
        user_id=app_state.user_id,
        chat_id=app_state.chat_id,
        agents=agents,
    )

    thread_id = format_thread_id(app_state.user_id, app_state.chat_id)

    config = RunnableConfig(configurable={"thread_id": thread_id})

    resume = _resume(decision)

    logger.info("router resume=%s", resume)

    if resume:
        inputs = Command(resume=resume)

    try:
        async for event in stream_events(
            agent=router_agent,
            inputs=inputs,
            config=config,
            context=context,
            # 收集 RouteAgentMiddleware 构建的节点
            extra_nodes=["router", "join"],
            subgraphs=True,
        ):
            # 消息类型
            if event.event_type == EventType.MESSAGE:
                # LLM Token
                chat_response = _render_message_chunk(event)
                if chat_response:
                    yield chat_response
            elif event.event_type in (EventType.MODEL, EventType.TOOLS):
                # create_agent 构建的 subgraph 中的 model 或 tools 节点
                # 最新的一条消息
                chat_response = _render_completed_message(event)
                if chat_response:
                    yield chat_response
            elif event.event_type == EventType.UPDATE:
                # 以下是 RouteAgentMiddleware 构建的节点
                # 当前更新格式：agent.memory.router_state.RouterState
                state = event.state or {}
                if event.node == "router":
                    routers = state.get("routers", [])
                    if routers:
                        yield ChatResponse(
                            msg_id=str(uuid.uuid4()),
                            msg_type=ResponseMsgTypeEnum.PROCESS,
                            content="路由到 " + "、".join(router.name for router in routers),
                        )
                        _log_state(state)
                    else:
                        yield ChatResponse(
                            msg_id=str(uuid.uuid4()),
                            msg_type=ResponseMsgTypeEnum.PROCESS,
                            content="没有找到路由",
                        )
                if event.node == "join":
                    final_result = state.get("final_result", "")
                    if final_result:
                        yield ChatResponse(
                            msg_id=str(uuid.uuid4()),
                            msg_type=ResponseMsgTypeEnum.PROCESS,
                            content=f"处理结果: {final_result}",
                        )
                # RouteAgentMiddleware 构建的节点结束
            elif event.event_type == EventType.INTERRUPT:
                # 只返回根 graph 触发的中断，避免重复提示。
                chat_response = _render_interrupt(event)
                if chat_response:
                    yield chat_response
    except Exception as e:
        logger.error("Router chat error, e=%s", str(e), exc_info=e)
        yield ChatResponse(
            msg_id=str(uuid.uuid4()),
            msg_type=ResponseMsgTypeEnum.ERROR,
            content=f"{str(e)}",
        )


def _log_state(state: dict[str, Any]) -> None:
    """开发环境下打印路由状态。"""

    settings = get_settings()
    if settings.app_env != AppEnv.DEV.value:
        return

    logger.info("Router state: %s", state)


def _parse_agents(
    agents: list[AgentTask] | None,
) -> tuple[list[AgentTask] | None, str | None]:
    """解析指定的代理。

    返回 (代理列表, 错误信息)。名称或任务内容为空的静默忽略，
    名称未注册的返回错误信息。
    """

    if not agents:
        return None, None

    names = task_agent_holder.get_agent_names()

    parsed = []
    for agent in agents:
        name = agent["name"].strip()
        query = agent["query"].strip()

        if not name or not query:
            logger.warning(
                "Ignore invalid agent, name=%s, query=%s",
                agent["name"],
                agent["query"],
            )
            continue

        if name not in names:
            return None, f"未知的代理: {name}"

        parsed.append({"name": name, "query": query})

    return parsed or None, None


def _render_message_chunk(event: Event) -> ChatResponse | None:
    """渲染消息块。"""
    token = event.message

    if isinstance(token, AIMessageChunk) and token.text:
        return ChatResponse(
            msg_id=event.msg_id or str(uuid.uuid4()),
            content=token.text,
        )
    return None

def _render_completed_message(event: Event) -> ChatResponse | None:
    """渲染完整消息"""

    message = event.message

    settings = get_settings()
    if settings.app_env == AppEnv.DEV.value:
        # llm 回复的完整消息
        if isinstance(message, AIMessage) and message.tool_calls:
            logger.info("Tool calls: %s", message.tool_calls)
        # 工具消息
        if isinstance(message, ToolMessage):
            logger.info(f"Tool %s response: %s", message.name, message.content)
    
    # llm 回复的完整消息
    if isinstance(message, AIMessage) and message.tool_calls:
        tool_names = [tool_call["name"] for tool_call in message.tool_calls]
        return ChatResponse(
            msg_id=event.msg_id or str(uuid.uuid4()),
            msg_type=ResponseMsgTypeEnum.PROCESS,
            content="调用 " + "、".join(tool_names),
        )
     # 工具消息
    if isinstance(message, ToolMessage):
        return ChatResponse(
            msg_id=event.msg_id or str(uuid.uuid4()),
            msg_type=ResponseMsgTypeEnum.PROCESS,
            content=f"{message.name} 执行{"成功" if message.status == "success" else "失败"}",
        )
    return None

def _render_interrupt(event: Event) -> ChatResponse | None:
    """渲染中断信息。

    同一 superstep 可能产生多个中断，这里只取第一个。
    """
    interrupts = event.interrupts

    if not interrupts:
        return None

    interrupt = interrupts[0]

    interrupt_id = interrupt.id
    interrupt_value = interrupt.value
    action_requests = interrupt_value["action_requests"]
    review_configs = interrupt_value["review_configs"]

    config_map = {cfg["action_name"]: cfg for cfg in review_configs}

    approve_items = []

    for action in action_requests:
        review_config = config_map[action["name"]]
        approve_items.append(
            ApproveItem(
                name=action["name"],
                description=action["description"],
                decisions=review_config["allowed_decisions"],
            )
        )

    return ChatResponse(
        msg_id=str(uuid.uuid4()),
        msg_type=ResponseMsgTypeEnum.APPROVE,
        approve=Approve(approve_id=interrupt_id, items=approve_items),
    )


def _resume(decision: Decision | None) -> dict | None:
    if not decision:
        return None
    return {
        # 决策 id。对应中断时的审批 id
        decision.decision_id: {
            "decisions": [
                # 多个审批，按顺序对应。必须和要审批的数量一致
                _build_decision(item)
                for item in decision.items
            ]
        }
    }


def _build_decision(item: DecisionItem) -> dict:
    if item.decision_type == "reject":
        # reject 时补充明确说明，避免模型把用户拒绝当作工具执行结果后反复重试
        message = (
            f"用户已拒绝该操作：{item.description}。该工具调用未执行，"
            "请不要重试该工具调用，直接向用户说明操作已取消即可。"
        )
    else:
        message = item.description
    return {"type": item.decision_type, "message": message}
