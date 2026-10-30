import hashlib
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.cache_repo import CacheRepository
from services.books_api import Book, GoogleBooksAPI, books_api

logger = logging.getLogger(__name__)


class BookService:
    """Google Books API + сквозное кэширование в БД."""

    CACHE_TTL_SECONDS = 24 * 60 * 60  

    def __init__(self, api: GoogleBooksAPI | None = None) -> None:
        self._api = api or books_api

    @staticmethod
    def _genre_key(genre: str) -> str:
        return f"genre_{genre.strip().lower()}"

    @staticmethod
    def _query_key(query: str) -> str:
       
        digest = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()
        return f"search_{digest}"

    async def get_books(self, session: AsyncSession, genre: str) -> list[Book]:
        cache_key = self._genre_key(genre)

        cached = await CacheRepository.get_valid_cache(session, cache_key)
        if cached is not None:
            logger.debug("Кэш-хит: %s", cache_key)
            return [Book.model_validate(item) for item in cached]

        books = await self._api.get_books_by_genre(genre)

        if books:
            await CacheRepository.set_cache(
                session,
                key=cache_key,
                data=[book.model_dump() for book in books],
                ttl_seconds=self.CACHE_TTL_SECONDS,
            )
        return books

    async def search(self, session: AsyncSession, query: str) -> list[Book]:
        cache_key = self._query_key(query)

        cached = await CacheRepository.get_valid_cache(session, cache_key)
        if cached is not None:
            return [Book.model_validate(item) for item in cached]

        books = await self._api.search_books(query)
        if books:
            await CacheRepository.set_cache(
                session,
                key=cache_key,
                data=[book.model_dump() for book in books],
                ttl_seconds=self.CACHE_TTL_SECONDS,
            )
        return books


book_service = BookService()