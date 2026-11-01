import html
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    get_next_question_keyboard,
    get_quiz_options_keyboard,
    get_quiz_result_keyboard,
)
from bot.keyboards.reply import BTN_QUIZ
from bot.states.quiz import QuizStates
from models.quiz import QuizQuestion
from repositories.quiz_repo import QuizRepository
from repositories.user_repo import UserRepository
from services.achievement_service import check_level_achievements

logger = logging.getLogger(__name__)
router = Router(name="quiz")

QUIZ_SIZE = 5
ANSWER_ALERT_LIMIT = 180


# ---------- вспомогательные функции ----------

def format_question(question: QuizQuestion, index: int, total: int) -> str:
    return (
        f"🎮 <b>Вопрос {index + 1}/{total}</b>\n"
        f"<i>{html.escape(question.category)}</i>\n\n"
        f"{html.escape(question.question_text)}"
    )


async def safe_edit(
    message: Message, text: str, keyboard: InlineKeyboardMarkup | None
) -> None:
    try:
        await message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return
        await message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)


async def show_question(
    target: Message,
    question: QuizQuestion,
    index: int,
    total: int,
    edit: bool = False,
) -> None:
    text = format_question(question, index, total)
    keyboard = get_quiz_options_keyboard(question.id, question.options)
    if edit:
        await safe_edit(target, text, keyboard)
    else:
        await target.answer(text, reply_markup=keyboard, disable_web_page_preview=True)


async def start_quiz(
    target: Message, state: FSMContext, session: AsyncSession, edit: bool = False
) -> None:
    try:
        questions = await QuizRepository.get_random_questions(session, limit=QUIZ_SIZE)
    except Exception:
        logger.exception("Не удалось получить вопросы викторины")
        questions = []

    if not questions:
        await state.clear()
        text = "😕 Викторина пока пуста, загляни позже"
        if edit:
            await safe_edit(target, text, None)
        else:
            await target.answer(text)
        return

    await state.set_state(QuizStates.in_progress)
    await state.update_data(
        question_ids=[q.id for q in questions],
        current_index=0,
        correct_answers_count=0,
        earned_xp=0,
    )
    await show_question(target, questions[0], 0, len(questions), edit=edit)


async def finish_quiz(
    message: Message, state: FSMContext, session: AsyncSession, user_id: int
) -> None:
    data = await state.get_data()
    total = len(data.get("question_ids") or [])
    correct = data.get("correct_answers_count", 0)
    earned = data.get("earned_xp", 0)

    user, levels_gained = await UserRepository.add_xp(session, user_id, earned)
    await state.clear()

    lines = [
        "🏁 <b>Викторина окончена!</b>",
        f"Правильных ответов: <b>{correct}/{total}</b>",
        f"Получено: <b>{earned} XP</b>",
    ]
    if user is not None:
        lines.append(f"Твой уровень: <b>{user.level}</b> (всего {user.xp} XP)")
    if levels_gained:
        lines.append(f"🎉 Новый уровень! +{levels_gained}")

    await safe_edit(message, "\n".join(lines), get_quiz_result_keyboard())

    if user is not None:
        await check_level_achievements(session, user, message)    


# ---------- вход ----------

@router.message(Command("quiz"))
@router.message(F.text == BTN_QUIZ)
async def cmd_quiz(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await start_quiz(message, state, session)


@router.callback_query(F.data == "quiz_restart")
async def cb_quiz_restart(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await callback.answer("Погнали заново! 🎲")
    await state.clear()
    await start_quiz(callback.message, state, session, edit=True)


# ---------- ответ на вопрос ----------

@router.callback_query(QuizStates.in_progress, F.data.startswith("quiz_ans:"))
async def cb_answer(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    try:
        _, question_id_raw, option_raw = callback.data.split(":")
        question_id, option_index = int(question_id_raw), int(option_raw)
    except ValueError:
        await callback.answer("Некорректная кнопка", show_alert=True)
        return

    data = await state.get_data()
    question_ids: list[int] = data.get("question_ids") or []
    index: int = data.get("current_index", 0)

    # Кнопка от вопроса, который уже пройден (или состояние потеряно)
    if not question_ids or index >= len(question_ids) or question_ids[index] != question_id:
        await callback.answer("Этот вопрос уже неактуален", show_alert=True)
        return

    question = await QuizRepository.get_question_by_id(session, question_id)
    if question is None or not 0 <= option_index < len(question.options):
        await callback.answer("Вопрос не найден", show_alert=True)
        return

    total = len(question_ids)
    is_correct = option_index + 1 == question.correct_option  # 0-based → 1-based
    chosen_text = html.escape(question.options[option_index])
    correct_text = html.escape(question.options[question.correct_option - 1])

    if is_correct:
        correct = data.get("correct_answers_count", 0) + 1
        earned = data.get("earned_xp", 0) + question.points
        await state.update_data(correct_answers_count=correct, earned_xp=earned)
        await callback.answer(f"✅ Верно! +{question.points} XP")
    else:
        await callback.answer(
            f"❌ Неверно. Правильный ответ: {correct_text[:ANSWER_ALERT_LIMIT]}",
            show_alert=True,
        )

    verdict = "✅ Верно" if is_correct else "❌ Неверно"
    text = (
        f"{format_question(question, index, total)}\n\n"
        f"Твой ответ: {chosen_text} ({verdict})"
    )
    if not is_correct:
        text += f"\nПравильный ответ: <b>{correct_text}</b>"

    await safe_edit(callback.message, text, get_next_question_keyboard())


# ---------- следующий вопрос ----------

@router.callback_query(QuizStates.in_progress, F.data == "quiz_next")
async def cb_next(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    question_ids: list[int] = data.get("question_ids") or []
    next_index = data.get("current_index", 0) + 1

    if next_index >= len(question_ids):
        await callback.answer("Считаю результаты…")
        await finish_quiz(callback.message, state, session, callback.from_user.id)
        return

    question = await QuizRepository.get_question_by_id(session, question_ids[next_index])
    if question is None:
        # Вопрос удалили из базы посреди сессии — не зацикливаемся, закрываем викторину
        logger.warning("Вопрос id=%s исчез из базы", question_ids[next_index])
        await callback.answer()
        await finish_quiz(callback.message, state, session, callback.from_user.id)
        return

    await state.update_data(current_index=next_index)
    await callback.answer()
    await show_question(callback.message, question, next_index, len(question_ids), edit=True)


# ---------- протухшие кнопки ----------

@router.callback_query(F.data.startswith("quiz_ans:") | (F.data == "quiz_next"))
async def cb_stale_quiz(callback: CallbackQuery) -> None:
    await callback.answer(
        "Эта викторина уже завершена. Нажми /quiz, чтобы начать новую",
        show_alert=True,
    )