import asyncio
import os
from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.models import Book
from app.repositories.books import BookRepository, SaveBookResult
from app.scraper.parser import ParsedBook


@pytest.mark.integration
def test_save_book_creates_updates_and_avoids_duplicates() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")

    identifier = uuid4().hex
    book = ParsedBook(
        title="A Light in the Attic",
        upc=identifier,
        price=Decimal("51.77"),
        stock_quantity=22,
        rating=3,
        category="Poetry",
        category_url=f"https://books.toscrape.com/catalogue/category/books/poetry_{identifier}/index.html",
        description="A description",
        product_url=f"https://books.toscrape.com/catalogue/a-light-in-the-attic_{identifier}/index.html",
        image_url="https://books.toscrape.com/media/cache/2c/da/2cda5a10.jpg",
    )

    async def scenario() -> None:
        engine = create_async_engine(database_url)
        try:
            async with engine.connect() as connection:
                transaction = await connection.begin()
                session = AsyncSession(connection, expire_on_commit=False, autoflush=False)
                try:
                    repository = BookRepository(session)

                    assert await repository.save(book) == SaveBookResult.CREATED
                    assert await repository.save(book) == SaveBookResult.UNCHANGED
                    assert await repository.save(replace(book, price=Decimal("52.77"))) == SaveBookResult.UPDATED

                    books_count = await session.scalar(
                        select(func.count()).select_from(Book).where(Book.upc == book.upc)
                    )
                    saved_book = await session.scalar(select(Book).where(Book.upc == book.upc))

                    assert books_count == 1
                    assert saved_book is not None
                    assert saved_book.price == Decimal("52.77")
                finally:
                    await session.close()
                    await transaction.rollback()

            async with AsyncSession(engine) as session:
                saved_book = await session.scalar(select(Book).where(Book.upc == book.upc))

                assert saved_book is None
        finally:
            await engine.dispose()

    asyncio.run(scenario())
