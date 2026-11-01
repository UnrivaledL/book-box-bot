from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.wishlist import WishlistItem


class WishlistRepository:
    @staticmethod
    async def add_book(session: AsyncSession, user_id: int, book_data: dict) -> bool:
        authors = book_data.get("authors") or []
        item = WishlistItem(
            user_id=user_id,
            title=(book_data.get("title") or "Без названия")[:512],
            authors=", ".join(authors)[:512],
            thumbnail=book_data.get("thumbnail"),
            info_link=book_data.get("info_link"),
        )
        session.add(item)
        try:
            await session.commit()
            return True
        except IntegrityError:
            await session.rollback()
            return False

    @staticmethod
    async def get_wishlist(session: AsyncSession, user_id: int) -> list[WishlistItem]:
        result = await session.execute(
            select(WishlistItem)
            .where(WishlistItem.user_id == user_id)
            .order_by(WishlistItem.added_at.desc())
        )
        return list(result.scalars().all())