from web.api.health import router as health_router
from web.api.chat import router as chat_router
from web.api.message import router as message_router

__all__ = ["health_router", "chat_router", "message_router"]
