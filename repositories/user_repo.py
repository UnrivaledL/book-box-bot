from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class UserRepository:
    @staticmethod
    async def get_or_create_user(
        session: AsyncSession,
        tg_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> tuple[User, bool]:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()

        if user is not None:
            changed = False
            if username is not None and user.username != username:
                user.username = username
                changed = True
            if first_name is not None and user.first_name != first_name:
                user.first_name = first_name
                changed = True
            if changed:
                await session.commit()
            return user, False

        user = User(tg_id=tg_id, username=username, first_name=first_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user, True
    
    @staticmethod
    async def add_xp(
        session: AsyncSession, tg_id: int, xp: int
    ) -> tuple[User | None, int]:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if user is None:
            return None, 0

        user.xp += xp
        levels_gained = 0
        while user.xp >= max(user.level, 1) * 100:
            user.xp -= max(user.level, 1) * 100
            user.level += 1
            levels_gained += 1

        await session.commit()
        return user, levels_gained
    
    @staticmethod
    async def get_top_users(session: AsyncSession, limit: int = 10) -> list[User]:
        result = await session.execute(
            select(User)
            .order_by(User.level.desc(), User.xp.desc(), User.id.asc())
            .limit(limit)
        )
        return list(result.scalars().all())