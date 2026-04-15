from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Response, Request

from web.session import generate_chat_id

class ChatMiddleware(BaseHTTPMiddleware):
    """聊天对话中间件。处理 chat-id"""
    async def dispatch(self, request: Request, call_next) -> Response:

        chat_id = request.headers.get("chat-id")

        if not chat_id:
            # 生成 Chat id
            chat_id = generate_chat_id()
            # 向 header 中增加 chat-id
            request.scope["headers"].append((b"chat-id", chat_id.encode()))
        
        response = await call_next(request)

        # 返回 chat-id
        response.headers["chat-id"] = chat_id
        return response
