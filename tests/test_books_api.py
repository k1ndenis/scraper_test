import asyncio
import os
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import get_session
from app.db.models import Book, Category
from app.main import app


@pytest.mark.integration
def test_list_books_filters_results() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")

    identifier = uuid4().hex

    async def scenario() -> None:
        engine = create_async_engine(database_url)
        try:
            async with engine.connect() as connection:
                transaction = await connection.begin()
                session_factory = async_sessionmaker(
                    bind=connection,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=False,
                )
                try:
                    async with session_factory() as session:
                        poetry = Category(
                            name=f"Poetry {identifier}",
                            source_url=f"https://books.toscrape.com/poetry/{identifier}",
                        )
                        fiction = Category(
                            name=f"Fiction {identifier}",
                            source_url=f"https://books.toscrape.com/fiction/{identifier}",
                        )
                        session.add_all(
                            [
                                Book(
                                    upc=f"light{identifier}",
                                    category=poetry,
                                    title="A Light in the Attic",
                                    description=None,
                                    price=Decimal("51.77"),
                                    stock_quantity=2,
                                    rating=3,
                                    product_url=f"https://books.toscrape.com/light/{identifier}",
                                    image_url=None,
                                ),
                                Book(
                                    upc=f"fiction{identifier}",
                                    category=fiction,
                                    title="A Dark Novel",
                                    description=None,
                                    price=Decimal("10.00"),
                                    stock_quantity=0,
                                    rating=1,
                                    product_url=f"https://books.toscrape.com/dark/{identifier}",
                                    image_url=None,
                                ),
                            ]
                        )
                        await session.flush()

                    async def get_test_session():
                        async with session_factory() as session:
                            yield session

                    app.dependency_overrides[get_session] = get_test_session
                    try:
                        async with httpx.AsyncClient(
                            transport=httpx.ASGITransport(app=app),
                            base_url="http://test",
                        ) as client:
                            response = await client.get(
                                "/books",
                                params={
                                    "search": "Light",
                                    "category": poetry.name,
                                    "min_price": "50",
                                    "max_price": "60",
                                    "rating": "3",
                                    "in_stock": "true",
                                    "limit": "10",
                                    "offset": "0",
                                },
                            )
                            missing_response = await client.get("/books/999999")
                            invalid_book_id_response = await client.get("/books/0")
                            invalid_response = await client.get("/books", params={"limit": "0"})
                    finally:
                        app.dependency_overrides.pop(get_session, None)

                    assert response.status_code == 200
                    assert response.json()["total"] == 1
                    assert response.json()["limit"] == 10
                    assert response.json()["offset"] == 0
                    assert response.json()["items"][0]["title"] == "A Light in the Attic"
                    assert response.json()["items"][0]["category"]["name"] == poetry.name
                    assert missing_response.status_code == 404
                    assert invalid_book_id_response.status_code == 422
                    assert invalid_book_id_response.json()["detail"][0]["loc"] == ["path", "book_id"]
                    assert invalid_response.status_code == 422
                finally:
                    await transaction.rollback()
        finally:
            await engine.dispose()

    asyncio.run(scenario())
