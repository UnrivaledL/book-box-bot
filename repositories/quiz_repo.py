from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.quiz import QuizQuestion


class QuizRepository:
    @staticmethod
    async def get_random_questions(
        session: AsyncSession, limit: int = 5
    ) -> list[QuizQuestion]:
        result = await session.execute(
            select(QuizQuestion).order_by(func.random()).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_question_by_id(
        session: AsyncSession, question_id: int
    ) -> QuizQuestion | None:
        return await session.get(QuizQuestion, question_id)