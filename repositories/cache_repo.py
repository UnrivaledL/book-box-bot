from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.cache import ApiCache


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CacheRepository:
    @staticmethod
    async def get_valid_cache(session: AsyncSession, key: str) -> Any | None:
        entry = await session.get(ApiCache, key)
        if entry is None:
            return None

        if entry.expires_at <= utcnow():
            await session.delete(entry)
            await session.commit()
            return None

        return entry.value

    @staticmethod
    async def set_cache(
        session: AsyncSession,
        key: str,
        data: Any,
        ttl_seconds: int,
    ) -> None:
        entry = ApiCache(
            key=key,
            value=data,
            expires_at=utcnow() + timedelta(seconds=ttl_seconds),
        )
        await session.merge(entry)  
        await session.commit()