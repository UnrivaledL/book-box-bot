from aiogram.fsm.state import State, StatesGroup


class RecommendationStates(StatesGroup):
    choosing_genre = State()
    viewing_books = State()