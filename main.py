import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from config.settings import settings

async def cmd_start(message: Message) -> None:
    await message.answer("📦 <b>Коробка с книгами</b>\n\nЗапусти меня — и найдёшь книгу по душе.")

async def main() -> None:
    logging.basicConfig(level=settings.log_level)
    
    session = AiohttpSession(proxy=settings.proxy_url)
    
    bot = Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    dp = Dispatcher()
    dp.message.register(cmd_start, CommandStart())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())