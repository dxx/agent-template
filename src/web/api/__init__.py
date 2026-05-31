from web.api.health import router as health_router
from web.api.chat import router as main_chat_router
from web.api.chat_router import router as route_chat_router
from web.api.message import router as message_router

__all__ = ["health_router", "main_chat_router", "route_chat_router", "message_router"]
