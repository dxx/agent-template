import uuid
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, ToolMessage, AnyMessage, AIMessageChunk
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command, Interrupt

from agent.memory import AppAgentContext
from agent.router import create_router_agent
from log import get_logger
from web.schemas import (
    AppState,
    Approve,
    ApproveItem,
    ChatRequest,
    ChatResponse,
    Decision,
    ResponseMsgTypeEnum,
)
from config import AppEnv, get_settings
from web.session import format_thread_id

logger = get_logger(__name__)

settings = get_settings()

# 创建 router_agent
router_agent = create_router_agent()


async def router_chat_response(
    app_state: AppState,
    request: ChatRequest,
) -> AsyncIterator[ChatResponse]:
    """路由 Agent 流式对话响应。"""
    content = request.content
    decision = request.decision

    inputs = {
        "messages": [{"role": "user", "content": content}],
    }

    thread_id = format_thread_id(app_state.user_id, app_state.chat_id)
    config = RunnableConfig(configurable={"thread_id": thread_id})
    context = AppAgentContext(user_id=app_state.user_id, chat_id=app_state.chat_id)

    resume = _resume(decision)

    logger.info("router resume=%s", resume)

    if resume:
        inputs = Command(resume=resume)

    try:
        async for chunk in router_agent.astream(
            inputs,
            config=config,
            context=context,
            stream_mode=["updates", "messages"],
            version="v2",
            subgraphs=True,
        ):
            if chunk["type"] == "messages":
                token, metadata = chunk["data"]
                lc_source = metadata.get("lc_source", None)
                if lc_source == "summarization":
                    # SummarizationMiddleware 汇总节点忽略
                    continue
                agent_name = metadata.get("lc_agent_name")
                if agent_name != router_agent.get_name():
                    # 只返回主 agent 对话的消息
                    continue
                if isinstance(token, AIMessageChunk):
                    chat_response = _render_message_chunk(token)
                    if chat_response:
                        yield chat_response
            elif chunk["type"] == "updates":
                for node_name, state in chunk["data"].items():
                    # create_agent 构建的 subgraph 中的 model 或 tools 节点
                    if node_name in ("model", "tools"):
                        # 最新的一条消息
                        chat_response = _render_completed_message(state["messages"][-1])
                        if chat_response:
                            yield chat_response

                    # 以下是 RouteAgentMiddleware 构建的节点
                    if node_name == "router":
                        routers = state.get("routers", [])
                        if routers:
                            yield ChatResponse(
                                msg_id=str(uuid.uuid4()),
                                msg_type=ResponseMsgTypeEnum.PROCESS,
                                content="路由到 " + "、".join(router.name for router in routers),
                            )
                        else:
                            yield ChatResponse(
                                msg_id=str(uuid.uuid4()),
                                msg_type=ResponseMsgTypeEnum.PROCESS,
                                content="没有找到路由",
                            )
                    if node_name == "join":
                        final_result = state.get("final_result", "")
                        if final_result:
                            yield ChatResponse(
                                msg_id=str(uuid.uuid4()),
                                msg_type=ResponseMsgTypeEnum.PROCESS,
                                content=f"处理结果: {final_result}",
                            )
                    # RouteAgentMiddleware 构建的节点结束

                    if node_name == "__interrupt__":
                        # 与 chat_service 保持一致：只返回根 graph 触发的中断，避免重复提示。
                        if str(chunk["ns"]) == "()":
                            yield _render_interrupt(state[0])
    except Exception as e:
        logger.error("Router chat error, e=%s", str(e), exc_info=e)
        yield ChatResponse(
            msg_id=str(uuid.uuid4()),
            msg_type=ResponseMsgTypeEnum.ERROR,
            content=f"{str(e)}",
        )


def _render_message_chunk(token: AIMessageChunk) -> ChatResponse | None:
    """渲染消息块。"""
    if token.text:
        return ChatResponse(
            msg_id=token.id if token.id else str(uuid.uuid4()),
            content=token.text,
        )
    return None

def _render_completed_message(message: AnyMessage) -> ChatResponse | None:
    """渲染完整消息"""

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
            msg_id=message.id if message.id else str(uuid.uuid4()),
            msg_type=ResponseMsgTypeEnum.PROCESS,
            content="调用 " + "、".join(tool_names),
        )
     # 工具消息
    if isinstance(message, ToolMessage):
        return ChatResponse(
            msg_id=message.id if message.id else str(uuid.uuid4()),
            msg_type=ResponseMsgTypeEnum.PROCESS,
            content=f"{message.name} 执行{"成功" if message.status == "success" else "失败"}",
        )
    return None

def _render_interrupt(interrupt: Interrupt) -> ChatResponse:
    """渲染中断信息。"""
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
        decision.decision_id: {
            "decisions": [
                {"type": item.decision_type, "message": item.description}
                for item in decision.items
            ]
        }
    }
