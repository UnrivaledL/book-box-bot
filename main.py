import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.handlers.user import router as user_router
from bot.middlewares.db import DbSessionMiddleware
from config.settings import settings
from database.engine import engine, init_db


async def main() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    await init_db()

    session = AiohttpSession(proxy=settings.proxy_url)

    bot = Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.message.middleware(DbSessionMiddleware())
    dp.include_router(user_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())