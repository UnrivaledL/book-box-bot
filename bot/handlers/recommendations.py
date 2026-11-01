import html
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    GENRE_TO_SUBJECT,
    get_book_card_keyboard,
    get_genres_keyboard,
)
from bot.keyboards.reply import BTN_RECOMMEND
from bot.states.recommendation import RecommendationStates
from repositories.user_repo import UserRepository
from repositories.wishlist_repo import WishlistRepository
from services.book_service import book_service

logger = logging.getLogger(__name__)
router = Router(name="recommendations")

DESCRIPTION_LIMIT = 400


# ---------- вспомогательные функции ----------

def format_book_card(book: dict) -> str:
    title = html.escape(book.get("title") or "Без названия")
    authors = html.escape(", ".join(book.get("authors") or []) or "Автор неизвестен")

    description = (book.get("description") or "Описание отсутствует").strip()
    if len(description) > DESCRIPTION_LIMIT:
        description = description[:DESCRIPTION_LIMIT].rstrip() + "..."
    description = html.escape(description)

    lines = [f"📖 <b>{title}</b>", f"✍️ {authors}", "", description]
    if book.get("info_link"):
        lines += ["", f'🔗 <a href="{book["info_link"]}">Подробнее в Google Books</a>']
    return "\n".join(lines)


async def send_book_card(message: Message, book: dict, index: int) -> None:
    text = format_book_card(book)
    keyboard = get_book_card_keyboard(index)

    thumbnail: str | None = book.get("thumbnail")
    if thumbnail:
        thumbnail = thumbnail.replace("http://", "https://", 1)  
        try:
            await message.answer_photo(
                photo=thumbnail,
                caption=text[:1024], 
                reply_markup=keyboard,
            )
            return
        except TelegramBadRequest as exc:
            logger.warning("Не удалось отправить обложку %s: %s", thumbnail, exc)

    await message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)


async def delete_silently(message: Message | None) -> None:
    if message is None:
        return
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


# ---------- вход в сценарий ----------

@router.message(Command("recommendations"))
@router.message(F.text == BTN_RECOMMEND)
async def cmd_recommendations(message: Message, state: FSMContext) -> None:
    await state.set_state(RecommendationStates.choosing_genre)
    await message.answer("Выбери жанр:", reply_markup=get_genres_keyboard())


# ---------- выбор жанра ----------

@router.callback_query(
    RecommendationStates.choosing_genre, F.data.startswith("genre:")
)
async def cb_genre_chosen(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    genre = callback.data.split(":", 1)[1]
    await callback.answer("Ищу книги… 🔎")

    subject = GENRE_TO_SUBJECT.get(genre, genre)
    books = await book_service.get_books(session, subject)

    if not books:
        await callback.message.edit_text(
            "😕 Ничего не нашлось, попробуй другой жанр:",
            reply_markup=get_genres_keyboard(),
        )
        return

    await state.update_data(
        books=[b.model_dump() for b in books],
        current_index=0,
        genre=genre,
    )
    await state.set_state(RecommendationStates.viewing_books)

    await delete_silently(callback.message)
    await send_book_card(callback.message, books[0].model_dump(), 0)


# ---------- листание ----------

@router.callback_query(RecommendationStates.viewing_books, F.data == "next_book")
async def cb_next_book(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    books: list[dict] = data.get("books", [])
    if not books:
        await callback.answer("Список пуст, выбери жанр заново", show_alert=True)
        return

    next_index = data.get("current_index", 0) + 1
    if next_index >= len(books):
        next_index = 0
        await callback.answer("Это все книги, начинаем сначала 🔁")
    else:
        await callback.answer()

    await state.update_data(current_index=next_index)
    await delete_silently(callback.message)
    await send_book_card(callback.message, books[next_index], next_index)


# ---------- избранное ----------

@router.callback_query(
    RecommendationStates.viewing_books, F.data.startswith("wishlist_add:")
)
async def cb_wishlist_add(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    index = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    books: list[dict] = data.get("books", [])

    if not books or index >= len(books):
        await callback.answer("Книга не найдена, выбери жанр заново", show_alert=True)
        return

    user, _ = await UserRepository.get_or_create_user(
        session=session,
        tg_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    added = await WishlistRepository.add_book(session, user.id, books[index])
    await callback.answer(
        "❤️ Добавлено в избранное!" if added else "Эта книга уже в твоём списке 😉"
    )


# ---------- назад к жанрам ----------

@router.callback_query(RecommendationStates.viewing_books, F.data == "back_to_genres")
async def cb_back_to_genres(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RecommendationStates.choosing_genre)
    await callback.answer()
    await delete_silently(callback.message)
    await callback.message.answer("Выбери жанр:", reply_markup=get_genres_keyboard())


# ---------- протухшие кнопки ----------

@router.callback_query(
    StateFilter(None),
    F.data.startswith(("genre:", "wishlist_add:")) | F.data.in_({"next_book", "back_to_genres"}),
)
async def cb_stale(callback: CallbackQuery) -> None:
    await callback.answer(
        "Эта карточка устарела. Нажми /recommendations, чтобы начать заново",
        show_alert=True,
    )