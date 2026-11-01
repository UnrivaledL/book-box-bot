from bot.handlers.menu import router as menu_router
from bot.handlers.recommendations import router as recommendations_router
from bot.handlers.user import router as user_router

__all__ = ["menu_router", "recommendations_router", "user_router"]