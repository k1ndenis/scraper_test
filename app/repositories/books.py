from __future__ import annotations

from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Book, Category
from app.scraper.parser import ParsedBook


class SaveBookResult(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


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
