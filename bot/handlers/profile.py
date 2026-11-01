import html
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import get_collection_keyboard, get_profile_keyboard
from bot.keyboards.reply import BTN_PROFILE, BTN_TOP
from repositories.achievement_repo import AchievementRepository
from repositories.user_repo import UserRepository
from repositories.wishlist_repo import WishlistRepository
from services.achievement_service import ACHIEVEMENT_TITLES, MIN_LEVEL, send_achievement_cat
from models.user import User

logger = logging.getLogger(__name__)
router = Router(name="profile")

MAX_ACHIEVEMENTS = len(ACHIEVEMENT_TITLES)


# ---------- вспомогательные ----------

def progress_bar(current: int, total: int, width: int = 5) -> str:
    total = max(total, 1)
    filled = min(width, round(current / total * width))
    return "▰" * filled + "▱" * (width - filled)


async def build_profile(
    session: AsyncSession, db_user: User
) -> tuple[str, InlineKeyboardMarkup]:
    books = await WishlistRepository.count(session, db_user.id)
    codes = await AchievementRepository.get_user_achievements(session, db_user.id)

    name = html.escape(db_user.first_name or "друг")
    handle = f"@{html.escape(db_user.username)}" if db_user.username else "—"
    threshold = max(db_user.level, 1) * 100

    text = (
        f"👤 <b>{name}</b>  ·  {handle}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⭐ Уровень: <b>{db_user.level}</b>\n"
        f"✨ Опыт: <b>{db_user.xp} / {threshold} XP</b>\n"
        f"{progress_bar(db_user.xp, threshold)} {round(db_user.xp / threshold * 100)}%\n"
        f"❤️ В избранном: <b>{books}</b>\n"
        f"🏅 Ачивок: <b>{len(codes)} / {MAX_ACHIEVEMENTS}</b>"
    )
    return text, get_profile_keyboard()


def build_collection(codes: list[str]) -> str:
    owned = set(codes)
    lines = ["🐱 <b>Коллекция достижений</b>\n"]
    for level in range(MIN_LEVEL, MIN_LEVEL + MAX_ACHIEVEMENTS):
        code = f"level_{level}"
        if code in owned:
            lines.append(f"✅ {ACHIEVEMENT_TITLES[code]} — открыт")
        else:
            lines.append(f"🔒 {ACHIEVEMENT_TITLES[code]} — закрыт")
    lines.append(
        f"\nОткрыто: <b>{len(owned & set(ACHIEVEMENT_TITLES))} / {MAX_ACHIEVEMENTS}</b>"
    )
    if owned & set(ACHIEVEMENT_TITLES):
        lines.append("Нажми на открытую ачивку, чтобы увидеть котика 🐱")
    return "\n".join(lines)


def build_leaderboard(users: list, current_tg_id: int) -> str:
    if not users:
        return "🏆 Таблица лидеров пока пуста — сыграй в викторину и стань первым!"

    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    lines = ["🏆 <b>Таблица лидеров</b>\n"]
    for position, user in enumerate(users):
        mark = medals.get(position, f"{position + 1}.")
        name = f"@{user.username}" if user.username else (user.first_name or "Аноним")
        name = html.escape(name)
        you = " <i>← ты</i>" if user.tg_id == current_tg_id else ""
        lines.append(f"{mark} {name} — ур. {user.level}, {user.xp} XP{you}")
    return "\n".join(lines)



async def safe_edit(
    message: Message, text: str, keyboard: InlineKeyboardMarkup | None
) -> None:
    try:
        await message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return
        await message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)


# ---------- профиль ----------

@router.message(Command("profile"))
@router.message(F.text == BTN_PROFILE)
async def cmd_profile(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    await state.clear()
    if db_user is None:
        await message.answer("Не удалось загрузить профиль, попробуй ещё раз")
        return
    text, keyboard = await build_profile(session, db_user)
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data == "back_to_profile")
async def cb_back_to_profile(
    callback: CallbackQuery, session: AsyncSession, db_user: User | None = None
) -> None:
    await callback.answer()
    if db_user is None:
        await callback.answer("Профиль недоступен", show_alert=True)
        return
    text, keyboard = await build_profile(session, db_user)
    await safe_edit(callback.message, text, keyboard)

# ---------- коллекция ----------

@router.callback_query(F.data == "show_collection")
async def cb_show_collection(
    callback: CallbackQuery, session: AsyncSession, db_user: User | None = None
) -> None:
    await callback.answer()
    if db_user is None:
        return
    codes = await AchievementRepository.get_user_achievements(session, db_user.id)
    await safe_edit(
        callback.message, build_collection(codes), get_collection_keyboard(set(codes))
    )

@router.callback_query(F.data.startswith("ach_card:"))
async def cb_achievement_card(
    callback: CallbackQuery, session: AsyncSession, db_user: User | None = None
) -> None:
    if db_user is None:
        return
    code = callback.data.split(":", 1)[1]

    codes = await AchievementRepository.get_user_achievements(session, db_user.id)
    if code not in codes:
        await callback.answer("Эта ачивка ещё не открыта 🔒", show_alert=True)
        return

    await callback.answer()
    await send_achievement_cat(callback.message, code)
# ---------- таблица лидеров ----------

@router.message(Command("leaderboard"))
@router.message(F.text == BTN_TOP)
async def cmd_leaderboard(message: Message, session: AsyncSession) -> None:
    users = await UserRepository.get_top_users(session, limit=10)
    await message.answer(build_leaderboard(users, message.from_user.id))


# ---------- настройки ----------

@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    await message.answer(
        "⚙️ <b>Настройки</b>\n\n"
        "Уведомления: <b>Вкл</b>\n"
        "Сброс прогресса: <i>в разработке</i>"
    )