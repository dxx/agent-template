from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Response, Request, status
from fastapi.responses import PlainTextResponse

from log import get_logger
from web.schemas import AppState, ApiResult, CODE_UNAUTHORIZED
from utils import json_util

logger = get_logger(__name__)

_PUBLIC_PATHS = ["/docs", "/openapi.json", "/health", "/test/chat/stream"]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        user_token = request.headers.get("user-token")

        if not user_token:
            logger.warning(
                "Unauthorized access attempt, path=%s", request.url.path
            )
            return PlainTextResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json;charset=UTF-8",
                content=json_util.to_json(
                    ApiResult(code=CODE_UNAUTHORIZED, message="用户未登录或登录已过期")
                ),
            )

        chat_id = request.headers.get("chat-id")
        
        request.state.app_state = AppState(
            # 假设已经通过 user-token 获取到 user_id
            user_id=user_token,
            # 有些接口不强制要求 chat_id
            chat_id=chat_id if chat_id else ""
        )

        response = await call_next(request)
        return response
