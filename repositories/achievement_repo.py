from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.achievement import UserAchievement


class AchievementRepository:
    @staticmethod
    async def unlock(session: AsyncSession, user_id: int, code: str) -> bool:
        session.add(UserAchievement(user_id=user_id, achievement_code=code))
        try:
            await session.commit()
            return True
        except IntegrityError:
            await session.rollback()
            return False

    @staticmethod
    async def get_user_achievements(session: AsyncSession, user_id: int) -> list[str]:
        result = await session.execute(
            select(UserAchievement.achievement_code)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.unlocked_at)
        )
        return list(result.scalars().all())