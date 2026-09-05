from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Book, Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_categories(self, limit: int, offset: int) -> tuple[list[tuple[Category, int]], int]:
        statement = (
            select(Category, func.count(Book.id))
            .outerjoin(Category.books)
            .group_by(Category.id, Category.name, Category.source_url)
            .order_by(Category.name, Category.id)
            .limit(limit)
            .offset(offset)
        )
        categories = [
            (category, books_count)
            for category, books_count in (await self._session.execute(statement)).all()
        ]
        total = await self._session.scalar(select(func.count()).select_from(Category))
        return categories, total or 0
