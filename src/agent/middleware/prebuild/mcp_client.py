"""MCP Client 中间件
连接 MCP Server，动态注入 tools
"""

from collections.abc import Awaitable
from typing import Any, override, Callable
from langchain.tools import BaseTool
from langchain.tools.tool_node import ToolCallRequest
from langchain.agents.middleware import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain.messages import ToolMessage
from langgraph.types import Command
from langchain.agents.middleware.types import (
    AgentMiddleware,
    ContextT,
    ResponseT,
    StateT,
)
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.callbacks import Callbacks
from langchain_mcp_adapters.interceptors import ToolCallInterceptor
from langchain_mcp_adapters.sessions import Connection

from log import get_logger

logger = get_logger(__name__)


class MCPClientMiddleware(AgentMiddleware[StateT, ContextT, ResponseT]):
    """MCP Client 中间件。连接 MCP Server 并注入 tools"""

    def __init__(
        self,
        mcp_config: dict[str, Connection],
        callbacks: Callbacks | None = None,
        tool_interceptors: list[ToolCallInterceptor] | None = None,
        ignore_tools: list[str] | None = None,
    ):
        """初始化 MCP Client 中间件

        Args:
            mcp_config: MultiServerMCPClient 原始配置字典
            callbacks: 用于处理通知和事件的可选回调函数。
            tool_interceptors: 可选的工具调用拦截器列表，用于修改请求与响应。
            ignore_tools: 忽略的工具名称，以 server name 加 _ 开头，如 `weather_search`。
        """
        self.mcp_config = mcp_config

        self.client = MultiServerMCPClient(
            mcp_config,
            callbacks=callbacks,
            tool_interceptors=tool_interceptors,
            tool_name_prefix=True,  # 强制启用前缀，避免冲突
        )
        self.mcp_tools: list[BaseTool] = []
        self.ignore_tools = ignore_tools
        self._initialized = False

    async def _initialize(self):
        """初始化并获取 tools"""
        if self._initialized:
            return
        logger.info("Initializing MCP client...")
        all_tools = await self.client.get_tools()

        if self.ignore_tools:
            self.mcp_tools = [
                tool for tool in all_tools if tool.name not in self.ignore_tools
            ]
            ignored_count = len(all_tools) - len(self.mcp_tools)
            logger.info(
                f"Loaded {len(self.mcp_tools)} tools from MCP servers, ignored {ignored_count} tools"
            )
        else:
            self.mcp_tools = all_tools
            logger.info(f"Loaded {len(self.mcp_tools)} tools from MCP servers")
    
        self._initialized = True

    @override
    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT]:
        if not self._initialized:
            import asyncio

            asyncio.run(self._initialize())
        override_request = self._build_overridden_request(request)
        return handler(override_request)

    @override
    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[
            [ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]
        ],
    ) -> ModelResponse[ResponseT]:
        if not self._initialized:
            await self._initialize()
        override_request = self._build_overridden_request(request)
        return await handler(override_request)

    @override
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        override_request = self._build_overridden_tool_request(request)
        return handler(override_request)

    @override
    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        override_request = self._build_overridden_tool_request(request)
        return await handler(override_request)

    def _build_overridden_request(
        self, request: ModelRequest[ContextT]
    ) -> ModelRequest[ContextT]:
        """构建带 MCP tools 的请求"""
        new_tools = [*request.tools, *self.mcp_tools]
        return request.override(tools=new_tools)

    def _build_overridden_tool_request(
        self, request: ToolCallRequest
    ) -> ToolCallRequest:
        """构建工具调用请求"""
        tool_name = request.tool_call["name"]
        for tool in self.mcp_tools:
            if tool.name == tool_name:
                return request.override(tool=tool)
        return request
