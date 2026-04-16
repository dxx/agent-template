from collections.abc import Awaitable
from datetime import datetime
from typing import Callable, override
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from langchain.agents.middleware.types import (
    AgentMiddleware,
    ContextT,
    ResponseT,
    StateT,
)

_SYSTEM_TIME_PROMPT = """
**当前系统时间:**
{current_time}

请根据当前时间提供准确的回答，例如：
- 如果用户问"今天"的事情，基于上述时间回复
- 如果涉及日期、时间相关的计算，使用上述时间作为基准
"""


class SystemTimeMiddleware(AgentMiddleware[StateT, ContextT, ResponseT]):
    """动态注入系统当前时间到系统提示词"""

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
    ) -> ModelResponse:
        override_request = self._build_overridden_request(request)
        return await handler(override_request)
    
    def _get_time_prompt(self) -> str:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")
        return _SYSTEM_TIME_PROMPT.format(current_time=current_time)

    def _build_overridden_request(self, request: ModelRequest[ContextT]) -> ModelRequest[ContextT]:
        time_prompt = self._get_time_prompt()
        new_content = list(
            request.system_message.content_blocks if request.system_message else []
        ) + [{"type": "text", "text": "\n\n" + time_prompt}]
        new_system_message = SystemMessage(content_blocks=new_content)
        return request.override(system_message=new_system_message)
