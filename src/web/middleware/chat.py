from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Response, Request
from fastapi import Response, Request, status
from fastapi.responses import PlainTextResponse

from web.schemas import ApiResult, CODE_VALIDATION_ERROR
from utils import json_util

_NEED_CHAT_ID_PATHS = ["/chat/stream"]


class ChatMiddleware(BaseHTTPMiddleware):
    """聊天对话中间件。处理 chat-id"""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path not in _NEED_CHAT_ID_PATHS:
            return await call_next(request)

        chat_id = request.headers.get("chat-id")

        if not chat_id:
            return PlainTextResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                media_type="application/json;charset=UTF-8",
                content=json_util.to_json(
                    ApiResult(code=CODE_VALIDATION_ERROR, message="缺少 chat-id 请求头")
                ),
            )

        return await call_next(request)
