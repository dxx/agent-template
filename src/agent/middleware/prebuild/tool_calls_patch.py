"""检查大模型发起工具调用后，是否执行了工具并返回工具消息，如果
没有某些大模型对话中会报错，需要把工具调用后的工具返回消息传给大
模型，在 human-in-the-loop 时，没有正确的完成人工介入，缺少
ToolMessage 内容，该 middleware 会检查在 AIMessage 中的
tool_calls 补充对应的 ToolMessage
"""

from typing import Any, override
from langgraph.runtime import Runtime
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    RemoveMessage,
    ToolMessage,
    ToolCall
)
from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    ResponseT,
    StateT,
)
from langgraph.graph.message import (
    REMOVE_ALL_MESSAGES,
)

from log import get_logger

logger = get_logger(__name__)

class ToolCallsPatchMiddleware(AgentMiddleware[StateT, ContextT, ResponseT]):

    @override
    def before_agent(
        self, state: AgentState[Any], runtime: Runtime[ContextT]
    ) -> dict[str, Any] | None:
        messages = state["messages"]
        if not messages or len(messages) == 0:
            return None
        
        new_messages = self._check_get_messages(messages)

        if len(new_messages) == len(messages):
            return None
 
        logger.info("Patch missing tool call messages")
            
        # 替换掉 messages
        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *new_messages,
            ]
        }
    
    @override
    async def abefore_agent(
        self, state: AgentState[Any], runtime: Runtime[ContextT]
    ) -> dict[str, Any] | None:
        return self.before_agent(state, runtime)
    
    def _check_get_messages(self, messages: list[AnyMessage]) -> list[AnyMessage]:
        new_messages = []
        for i, message in enumerate(messages):
            new_messages.append(message)
            if  isinstance(message, AIMessage) and message.tool_calls:
                for tool_call in message.tool_calls:
                    if self._check_after(tool_call, i + 1, messages):
                        continue
                    # 补充 ToolMessage
                    new_messages.append(ToolMessage(
                            tool_call_id=tool_call["id"],
                            name=tool_call["name"],
                            content="任务被取消了",
                        )
                    )
        return new_messages
    
    def _check_after(self, tool_call: ToolCall, i, messages: list[AnyMessage]) -> bool:
        while i < len(messages):
            message = messages[i]
            if isinstance(message, ToolMessage):
                # 找到工具回复的消息
                if tool_call["id"] == message.tool_call_id and tool_call["name"] == message.name:
                    return True
            i = i + 1
        return False
