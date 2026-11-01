from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_RECOMMEND = "📚 Подобрать книгу"
BTN_QUIZ = "🎮 Викторина"
BTN_WISHLIST = "❤️ Хочу прочитать"
BTN_PROFILE = "👤 Профиль"


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_RECOMMEND), KeyboardButton(text=BTN_QUIZ)],
            [KeyboardButton(text=BTN_WISHLIST), KeyboardButton(text=BTN_PROFILE)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие…",
    )