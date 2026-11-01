import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from database.engine import async_session_maker
from repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


def _extract_tg_user(event: TelegramObject) -> Any | None:
    if isinstance(event, Update):
        event = event.event          
    return getattr(event, "from_user", None)


class DbSessionMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session_maker() as session:
            data["session"] = session

            tg_user = data.get("event_from_user") or _extract_tg_user(event)

            if tg_user is not None and not tg_user.is_bot:
                db_user, _ = await UserRepository.get_or_create_user(
                    session=session,
                    tg_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                )
                data["db_user"] = db_user

            return await handler(event, data)