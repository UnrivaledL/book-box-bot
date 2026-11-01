import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.reply import BTN_WISHLIST, get_main_menu 
from repositories.wishlist_repo import WishlistRepository
from models.user import User

router = Router(name="menu")

MENU_TEXT = (
    "📦 <b>Коробка с книгами</b>\n\n"
    "📚 Подобрать книгу — рекомендации по жанрам\n"
    "🎮 Викторина — проверь себя и получи XP\n"
    "❤️ Хочу прочитать — твой список избранного\n"
    "👤 Профиль — уровень, опыт и коллекция\n"
    "🏆 Топ-10 — лучшие читатели"
)


@router.message(Command("menu", "help"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(MENU_TEXT, reply_markup=get_main_menu())


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(MENU_TEXT, reply_markup=get_main_menu())


@router.message(F.text == BTN_WISHLIST)
async def show_wishlist(message: Message, session: AsyncSession, db_user: User | None = None) -> None:
    if db_user is None:
        await message.answer("Ошибка: пользователь не найден")
        return
        
    items = await WishlistRepository.get_wishlist(session, db_user.id)

    if not items:
        await message.answer(
            "Твой список пока пуст 📭\n"
            "Нажми «📚 Подобрать книгу» и добавь что-нибудь интересное!"
        )
        return

    lines = ["❤️ <b>Хочу прочитать:</b>\n"]
    for i, item in enumerate(items, 1):
        title = html.escape(item.title)
        if item.info_link:
            lines.append(f'{i}. <a href="{item.info_link}">{title}</a> — {html.escape(item.authors)}')
        else:
            lines.append(f"{i}. <b>{title}</b> — {html.escape(item.authors)}")

    await message.answer("\n".join(lines), disable_web_page_preview=True)