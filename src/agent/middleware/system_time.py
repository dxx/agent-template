from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import override
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from langchain.agents.middleware.types import (
    AgentMiddleware,
    ContextT,
    ResponseT,
    StateT,
)

_SYSTEM_TIME_PROMPT = """
## 当前系统时间（最高优先级）
{current_time}

规则：
- 用户问"今天/明天/昨天/本周"等相对时间，一律以上述系统时间为基准计算。
- 调用工具时，需要填写的日期必须基于上述系统时间重新计算，不要照抄历史对话里的日期。
- 历史对话中出现的任何日期、星期（包括你自己之前的回复、工具结果里的日期）都可能已经过期，
  禁止用它们推断"今天"。两者冲突时，永远以上述系统时间为准。
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
