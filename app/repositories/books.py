from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Book, Category
from app.scraper.parser import ParsedBook


class SaveBookResult(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


@dataclass(frozen=True, slots=True)
class BookListFilters:
    search: str | None = None
    category: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    rating: int | None = None
    in_stock: bool | None = None


class BookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, parsed_book: ParsedBook) -> SaveBookResult:
        category = await self._session.scalar(
            select(Category).where(Category.source_url == parsed_book.category_url)
        )
        category_changed = False

        if category is None:
            category = Category(
                name=parsed_book.category,
                source_url=parsed_book.category_url,
            )
            self._session.add(category)
            category_changed = True
        elif category.name != parsed_book.category:
            category.name = parsed_book.category
            category_changed = True

        book = await self._session.scalar(select(Book).where(Book.upc == parsed_book.upc))
        book_values = {
            "title": parsed_book.title,
            "description": parsed_book.description,
            "price": parsed_book.price,
            "stock_quantity": parsed_book.stock_quantity,
            "rating": parsed_book.rating,
            "product_url": parsed_book.product_url,
            "image_url": parsed_book.image_url,
        }

        if book is None:
            self._session.add(Book(upc=parsed_book.upc, category=category, **book_values))
            result = SaveBookResult.CREATED
        else:
            changed = category_changed
            if book.category_id != category.id:
                book.category = category
                changed = True

            for field_name, value in book_values.items():
                if getattr(book, field_name) != value:
                    setattr(book, field_name, value)
                    changed = True

            result = SaveBookResult.UPDATED if changed else SaveBookResult.UNCHANGED

        await self._session.flush()
        return result

    async def list_books(
        self,
        filters: BookListFilters,
        limit: int,
        offset: int,
    ) -> tuple[list[Book], int]:
        statement = select(Book)
        count_statement = select(func.count()).select_from(Book)
        conditions = []

        if filters.category is not None:
            statement = statement.join(Book.category)
            count_statement = count_statement.join(Book.category)
            conditions.append(Category.name == filters.category)
        if filters.search is not None:
            conditions.append(Book.title.ilike(f"%{filters.search}%"))
        if filters.min_price is not None:
            conditions.append(Book.price >= filters.min_price)
        if filters.max_price is not None:
            conditions.append(Book.price <= filters.max_price)
        if filters.rating is not None:
            conditions.append(Book.rating == filters.rating)
        if filters.in_stock is True:
            conditions.append(Book.stock_quantity > 0)
        elif filters.in_stock is False:
            conditions.append(Book.stock_quantity <= 0)

        if conditions:
            statement = statement.where(*conditions)
            count_statement = count_statement.where(*conditions)

        books = list(
            (
                await self._session.scalars(
                    statement.options(selectinload(Book.category))
                    .order_by(Book.id)
                    .limit(limit)
                    .offset(offset)
                )
            ).all()
        )
        total = await self._session.scalar(count_statement)
        return books, total or 0

    async def get_by_id(self, book_id: int) -> Book | None:
        return await self._session.scalar(
            select(Book).options(selectinload(Book.category)).where(Book.id == book_id)
        )
