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

def get_quiz_options_keyboard(question_id: int, options: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, option in enumerate([opt for opt in options if opt][:4]):
        builder.button(
            text=f"{index + 1}. {option}"[:64],
            callback_data=f"quiz_ans:{question_id}:{index}",
        )
    builder.adjust(1)  
    return builder.as_markup()


def get_next_question_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Следующий вопрос ➡️", callback_data="quiz_next")
        ]]
    )


def get_quiz_result_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Играть ещё", callback_data="quiz_restart")
    builder.button(text="🔙 В меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🐱 Коллекция", callback_data="show_collection")
    builder.adjust(1)
    return builder.as_markup()


def get_collection_keyboard(owned_codes: set[str] | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for level in range(2, 11):
        code = f"level_{level}"
        if owned_codes and code in owned_codes:
            builder.button(text=f"🐱 Уровень {level}", callback_data=f"ach_card:{code}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад в профиль", callback_data="back_to_profile"))
    return builder.as_markup()