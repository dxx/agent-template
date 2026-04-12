from collections.abc import AsyncIterable
from langchain_core.messages import AIMessage, ToolMessage, AnyMessage, AIMessageChunk
from langgraph.types import Interrupt, Command
from datetime import datetime
import uuid

from agent.subagents import create_main_agent
from agent.memory import AppAgentContext, AppAgentState
from log import get_logger
from web.schemas import (
    ChatRequest,
    ChatResponse,
    ResponseMsgTypeEnum,
    Approve,
    ApproveItem,
    Decision
)
from config import AppEnv, get_settings

logger = get_logger(__name__)

settiongs = get_settings()

# 创建 main_agent
main_agent = create_main_agent()

async def chat_response(user_id: str, request: ChatRequest) -> AsyncIterable[ChatResponse[str]]:
    content = request.content
    decision = request.decision

    # state 初始值
    state = AppAgentState(sub_agent_calls=[])
    inputs = {
        "messages": [{"role": "user", "content": content}],
        # 将 state 字段拆开传递
        **state
    }

    config = {"configurable": {"thread_id": user_id}}
    context = AppAgentContext(user_id=user_id)

    resume = _resume(decision)

    logger.info("resume=%s", resume)

    if resume:
        inputs = Command(
            resume=resume
        )

    try:
        async for chunk in main_agent.astream(
            inputs,
            config=config,
            context=context,
            stream_mode=[
                "updates", "messages"
            ],
            version="v2",
            # 开启子 graph 流事件
            subgraphs=True
        ):
            # 消息类型
            if chunk["type"] == "messages":
                # LLM Token
                token, metadata = chunk["data"]
                lc_source = metadata.get("lc_source", None)
                if lc_source == "summarization":
                    # SummarizationMiddleware 汇总节点忽略
                    continue
                agent_name = metadata.get("lc_agent_name")
                if agent_name != main_agent.get_name():
                    # 只返回主 agent 对话的消息
                    continue
                if isinstance(token, AIMessageChunk):
                    chat_response = _render_message_chunk(token)
                    if chat_response:
                        yield chat_response
            elif chunk["type"] == "updates":
                # graph 中节点数据
                for source, update in chunk["data"].items():
                    # model 或 tools 节点
                    if source in ("model", "tools"):
                        # 最新的一条消息
                        chat_response = _render_completed_message(update["messages"][-1])
                        if chat_response:
                            yield chat_response
                    if source == "__interrupt__":
                        # 只返回主 agent 触发的中断，开启子 graph 流事件子 agent 也会触发
                        if str(chunk["ns"]) == "()":
                            yield _render_interrupt(update[0])
    except Exception as e:
        logger.error("Chat error, e=%s", str(e))
        yield ChatResponse(
            msg_id=str(uuid.uuid4()),
            msg_type=ResponseMsgTypeEnum.ERROR,
            content=f"{str(e)}",
            created=int(datetime.now().timestamp() * 1000),
        )

def _render_message_chunk(token: AIMessageChunk) -> ChatResponse | None:
    """渲染消息块

    token 内容示例:

    content = '今天吃什么，我来给你一些推荐吧！🍽️\n\n##'
    additional_kwargs = {}
    response_metadata = {
        'model_provider': 'openai'
    }
    id = 'lc_run--019d609c-ddc7-7f32-83cd-157d476f3b0a'
    tool_calls = [] invalid_tool_calls = [] tool_call_chunks = []

    content = ' 今日饮食建议\n\n### 🍚 主食选择\n- **北方口味**：面条、'
    additional_kwargs = {}
    response_metadata = {
        'model_provider': 'openai'
    }
    id = 'lc_run--019d609c-ddc7-7f32-83cd-157d476f3b0a'
    tool_calls = [] invalid_tool_calls = [] tool_call_chunks = []

    content = '饺子、馒头\n- **南方口味**：米饭、粥类\n\n### 🥬 营养搭配建议\n一顿健康的餐'
    additional_kwargs = {}
    response_metadata = {
        'model_provider': 'openai'
    }
    id = 'lc_run--019d609c-ddc7-7f32-83cd-157d476f3b0a'
    tool_calls = [] invalid_tool_calls = [] tool_call_chunks = []
    """

    # 分块文本信息
    if token.text:
        return ChatResponse(
            msg_id=token.id,
            content=token.text,
            created=int(datetime.now().timestamp() * 1000),
        )
    return None

def _render_completed_message(message: AnyMessage) -> ChatResponse | None:
    """渲染完整消息

    message 内容示例:

    content = '今天吃什么这个问题，让我来帮你做个决定吧！🍽️\n\n给你几个选择：\n\n1. **火锅** 🍲 - 热气腾腾，适合和朋友
    一起分享\n2. **日料** 🍣 - 新鲜美味，清淡健康\n3. **川菜** 🌶️ - 麻辣鲜香，下饭神器\n4. **披萨意面** 🍕 - 西式
    风味，经典舒适\n5. **沙拉轻食** 🥗 - 清新爽口，无负担\n\n或者如果你告诉我：\n- 你现在的心情（想吃点辣的？清淡的？）\n- 你
    在哪个地区（我可以推荐更具体的）\n- 想点外卖还是自己做饭？\n\n我可以帮你做出更精准的推荐！😋'
    additional_kwargs = {}
    response_metadata = {
        'finish_reason': 'stop',
        'model_name': 'MiniMax-M2.7',
        'model_provider': 'openai'
    }
    name = 'main_agent'
    id = 'lc_run--019d60a1-1a5a-7211-9a6e-3643db7c4d12'
    tool_calls = [] invalid_tool_calls = []
    """

    if settiongs.app_env == AppEnv.DEFAULT.value or settiongs.app_env == AppEnv.DEV.value:
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
            msg_id=message.id,
            msg_type=ResponseMsgTypeEnum.PROCESS,
            content="调用: " + "、".join(tool_names),
            created=int(datetime.now().timestamp() * 1000),
        )
     # 工具消息
    if isinstance(message, ToolMessage):
        return ChatResponse(
            msg_id=message.id,
            msg_type=ResponseMsgTypeEnum.PROCESS,
            content=f"{message.name} 执行结果: {message.content}",
            created=int(datetime.now().timestamp() * 1000),
        )
    return None


def _render_interrupt(interrupt: Interrupt) -> ChatResponse:
    """渲染中断信息

    interrupt 内容示例:

    value = {
        'action_requests': [{
            'name': 'write_file',
            'args': {
                'file_path': 'hello.txt',
                'content': 'hello'
            },
            'description': '写入文件需要审批'
        }],
        'review_configs': [{
            'action_name': 'write_file',
            'allowed_decisions': ['approve', 'reject']
        }]
    },
    id = 'f96ef5b2139198600bd7c58db3248380'
    """

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
                decisions=review_config["allowed_decisions"]
            )
        )

    return ChatResponse(
        msg_id=str(uuid.uuid4()),
        msg_type=ResponseMsgTypeEnum.APPROVE,
        approve=Approve(approve_id=interrupt_id, items=approve_items),
        created=int(datetime.now().timestamp() * 1000)
    )

def _resume(decision: Decision) -> dict:
    if not decision:
        return None
    return {
        # 决策 id。对应中断时的审批 id
        decision.decision_id: {
            "decisions": [
                # 多个审批，按顺序对应。必须和要审批的数量一致
                {"type": item.decision_type, "message": item.description }
                for item in decision.items
            ]
        }
    }
