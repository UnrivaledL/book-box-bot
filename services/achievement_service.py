import logging
from pathlib import Path

from aiogram.types import FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.achievement_repo import AchievementRepository

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

MIN_LEVEL, MAX_LEVEL = 2, 10

ACHIEVEMENT_TITLES: dict[str, str] = {
    f"level_{level}": f"Уровень {level}" for level in range(MIN_LEVEL, MAX_LEVEL + 1)
}


async def _send_cat(
    message: Message, level: int, code: str, extra_codes: list[str]
) -> None:
    title = ACHIEVEMENT_TITLES.get(code, code)
    caption = f"🐱 Новая ачивка: <b>{title}</b>!"
    if extra_codes:
        others = ", ".join(ACHIEVEMENT_TITLES.get(c, c) for c in extra_codes)
        caption += f"\n\nЗаодно открыты: {others}"

    path = ASSETS_DIR / f"cat_level_{level}.jpg"
    if path.exists():
        try:
            await message.answer_photo(FSInputFile(path), caption=caption)
            return
        except Exception as exc: 
            logger.warning("Не удалось отправить котика %s: %s", path, exc)
    else:
        logger.warning("Нет картинки котика для уровня %s (ожидался %s)", level, path)

    await message.answer(caption + "\n\n<i>(картинка для этого уровня ещё не нарисована)</i>")


async def check_level_achievements(
    session: AsyncSession, user: User, message: Message
) -> list[str]:
    new_codes: list[str] = []
    for level in range(MIN_LEVEL, min(user.level, MAX_LEVEL) + 1):
        code = f"level_{level}"
        if await AchievementRepository.unlock(session, user.id, code):
            new_codes.append(code)

    if new_codes:
        await send_achievement_cat(message, new_codes[-1], extra=new_codes[:-1])
    return new_codes

def cat_path(level: int) -> Path:
    return ASSETS_DIR / f"cat_level_{level}.jpg"


async def send_achievement_cat(
    message: Message, code: str, extra: list[str] | None = None
) -> bool:
    level_raw = code.split("_", 1)[1] if "_" in code else ""
    if not level_raw.isdigit():
        logger.warning("Неизвестный код ачивки: %s", code)
        return False

    level = int(level_raw)
    caption = f"🐱 <b>{ACHIEVEMENT_TITLES.get(code, code)}</b>"

    if extra:
        others = ", ".join(ACHIEVEMENT_TITLES.get(c, c) for c in extra)
        caption += f"\n\nЗаодно открыты: {others}"

    path = cat_path(level)
    if path.exists():
        try:
            await message.answer_photo(FSInputFile(path), caption=caption)
            return True
        except Exception as exc:
            logger.warning("Не удалось отправить котика %s: %s", path, exc)
    else:
        logger.warning("Нет картинки котика для уровня %s (ожидался %s)", level, path)

    await message.answer(
        caption + "\n\n<i>Картинка для этого уровня ещё не нарисована.</i>"
    )
    return False