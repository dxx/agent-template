from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Response, Request
from fastapi import Response, Request, status
from fastapi.responses import PlainTextResponse

from web.schemas import ApiResult, CODE_VALIDATION_ERROR, AppState
from web.service.message_service import is_chat_id_exists

from utils import json_util

_NEED_CHAT_ID_PATHS = ["/chat/stream"]


def _validation_error_response(message: str) -> PlainTextResponse:
    return PlainTextResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        media_type="application/json;charset=UTF-8",
        content=json_util.to_json(
            ApiResult(code=CODE_VALIDATION_ERROR, message=message)
        ),
    )


class ChatMiddleware(BaseHTTPMiddleware):
    """聊天对话中间件。处理 chat-id"""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path not in _NEED_CHAT_ID_PATHS:
            return await call_next(request)

        chat_id = request.headers.get("chat-id")

        if not chat_id:
            return _validation_error_response("缺少 chat-id 请求头")

        app_state: AppState = getattr(request.state, "app_state")
        if app_state:
            user_id = app_state.user_id
            if not await is_chat_id_exists(user_id, chat_id):
                return _validation_error_response("chat-id 无效")

        return await call_next(request)
