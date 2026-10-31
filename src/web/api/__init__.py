from web.api.health import router as health_router
from web.api.chat import router as main_chat_router
from web.api.router_chat import router as router_chat_router
from web.api.message import router as message_router

__all__ = ["health_router", "main_chat_router", "router_chat_router", "message_router"]
