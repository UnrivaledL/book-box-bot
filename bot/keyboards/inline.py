from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

GENRES: list[str] = [
    "Фэнтези",
    "Фантастика",
    "Детектив",
    "Роман",
    "Ужасы",
    "Приключения",
    "Триллер",
    "Биография",
    "Поэзия",
    "Научпоп",
]

GENRE_TO_SUBJECT: dict[str, str] = {
    "Фэнтези": "fantasy",
    "Фантастика": "science fiction",
    "Детектив": "detective",
    "Роман": "romance",
    "Ужасы": "horror",
    "Приключения": "adventure",
    "Триллер": "thriller",
    "Биография": "biography",
    "Поэзия": "poetry",
    "Научпоп": "science",
}


def get_genres_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for genre in GENRES:
        builder.button(text=genre, callback_data=f"genre:{genre}")

    builder.adjust(2) 
    builder.row(InlineKeyboardButton(text="🔙 В меню", callback_data="main_menu"))
    return builder.as_markup()


def get_book_card_keyboard(book_index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❤️ Хочу прочитать", callback_data=f"wishlist_add:{book_index}")
    builder.button(text="▶️ Следующая", callback_data="next_book")
    builder.button(text="🔙 К жанрам", callback_data="back_to_genres")
    builder.adjust(2, 1)
    return builder.as_markup()