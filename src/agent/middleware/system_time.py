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
## 时间基准（本回合实时采样，权威且最新）

本回合系统时间：{current_time}

说明：上面这个时间是本次对话开始时实时取得的，比本次对话中出现的任何其他时间都新，
包括你之前回复过的时间、历史消息里的日期，以及各种结果里出现的日期。凡有冲突，一律以它为准。

执行要求：
- 用户提到"今天 / 现在 / 明天 / 昨天 / 本周 / 这个月"等相对时间，一律按上面的时间计算。
- 需要填写或描述日期时，先按上面的时间重新推算，不要沿用历史对话里的日期。
- 生成回答前，若涉及时间，先自检一次：所用的时间是否就等于上面的值。
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
