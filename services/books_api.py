import logging

import httpx
from pydantic import BaseModel, Field
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings

logger = logging.getLogger(__name__)

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
REQUEST_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class Book(BaseModel):
    """Валидированное представление тома Google Books."""

    title: str = "Без названия"
    authors: list[str] = Field(default_factory=list)
    description: str | None = None
    categories: list[str] = Field(default_factory=list)
    published_date: str | None = None
    page_count: int | None = None
    average_rating: float | None = None
    thumbnail: str | None = None
    info_link: str | None = None

    @classmethod
    def from_volume(cls, volume: dict) -> "Book":
        info: dict = volume.get("volumeInfo", {})
        image_links: dict = info.get("imageLinks") or {}
        return cls(
            title=info.get("title") or "Без названия",
            authors=info.get("authors") or [],
            description=info.get("description"),
            categories=info.get("categories") or [],
            published_date=info.get("publishedDate"),
            page_count=info.get("pageCount"),
            average_rating=info.get("averageRating"),
            thumbnail=image_links.get("thumbnail") or image_links.get("smallThumbnail"),
            info_link=info.get("infoLink"),
        )

    @property
    def authors_str(self) -> str:
        return ", ".join(self.authors) if self.authors else "Автор неизвестен"


def _is_transient_error(exc: BaseException) -> bool:
    if isinstance(exc, httpx.RequestError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return False


class GoogleBooksAPI:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception(_is_transient_error),
        reraise=True,
    )
    async def _fetch(self, params: dict) -> dict:
        response = await self._get_client().get(GOOGLE_BOOKS_URL, params=params)
        response.raise_for_status()
        return response.json()

    async def search_books(self, query: str, max_results: int = 5) -> list[Book]:
        params = {
            "q": query,
            "maxResults": max(1, min(max_results, 40)),  
            "key": settings.google_books_api_key,
            "printType": "books",
        }
        try:
            payload = await self._fetch(params)
        except httpx.HTTPError as exc:
            logger.error("Google Books API недоступен (query=%r): %s", query, exc)
            return []

        items = payload.get("items") or []
        books: list[Book] = []
        for volume in items:
            try:
                books.append(Book.from_volume(volume))
            except Exception as exc: 
                logger.warning("Пропущен некорректный том: %s", exc)
        return books

    async def get_books_by_genre(self, genre: str, max_results: int = 5) -> list[Book]:
        return await self.search_books(f'subject:"{genre}"', max_results=max_results)


books_api = GoogleBooksAPI()