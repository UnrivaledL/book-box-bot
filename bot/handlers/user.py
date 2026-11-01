from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repo import UserRepository
from bot.keyboards.reply import get_main_menu

router = Router(name="user")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    user, is_new = await UserRepository.get_or_create_user(
        session=session,
        tg_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if is_new:
        text = (
            "📦 <b>Добро пожаловать в Коробку с книгами!</b>\n\n"
            "Я подберу книгу по душе и проверю твои знания в литературных викторинах.\n\n"
            "Твой уровень: 1, опыт: 0 XP."
        )
    else:
        name = user.first_name or "друг"
        text = (
            f"С возвращением, <b>{name}</b>!\n\n"
            f"Уровень: {user.level} · Опыт: {user.xp} XP"
        )

    await message.answer(text, reply_markup=get_main_menu())