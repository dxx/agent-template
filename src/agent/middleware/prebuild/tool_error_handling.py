"""工具调用错误处理中间件。

捕获工具执行时抛出的异常，并转换为 ToolMessage 返回给大模型，避免单个
工具异常直接中断 agent 执行。
"""

from collections.abc import Awaitable
from typing import Any, Callable, override

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ContextT,
    ResponseT,
    StateT,
)
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command

from log import get_logger

logger = get_logger(__name__)

ErrorContent = str | Callable[[Exception], str]


class ToolErrorHandlingMiddleware(AgentMiddleware[StateT, ContextT, ResponseT]):
    """工具调用错误处理中间件。"""

    def __init__(self, error_content: ErrorContent | None = None):
        """初始化工具调用错误处理中间件。

        Args:
            error_content: 工具调用失败时返回给大模型的错误内容。可以是固定字符串，
                也可以是接收 Exception 并返回字符串的回调函数。
        """
        self.error_content = error_content

    @override
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        try:
            return handler(request)
        except Exception as error:
            return self._build_error_message(request, error)

    @override
    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        try:
            return await handler(request)
        except Exception as error:
            return self._build_error_message(request, error)

    def _build_error_message(
        self, request: ToolCallRequest, error: Exception
    ) -> ToolMessage:
        tool_call = request.tool_call
        tool_name = tool_call.get("name", "unknown")
        tool_call_id = tool_call.get("id")

        logger.error("Tool call failed: %s", tool_name, exc_info=error)

        return ToolMessage(
            name=tool_name,
            tool_call_id=tool_call_id,
            content=self._get_error_content(error),
            status="error",
        )

    def _get_error_content(self, error: Exception) -> str:
        if isinstance(self.error_content, str):
            return self.error_content
        if callable(self.error_content):
            return self.error_content(error)
        return f"工具调用失败: {type(error).__name__}: {error}"
