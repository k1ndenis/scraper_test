import asyncio
import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import get_session
from app.db.models import Book, Category, ScrapeRun, ScrapeStatus
from app.main import app


@pytest.mark.integration
def test_categories_and_scrape_runs_endpoints() -> None:
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
                        fiction = Category(
                            name=f"Fiction {identifier}",
                            source_url=f"https://books.toscrape.com/fiction/{identifier}",
                        )
                        poetry = Category(
                            name=f"Poetry {identifier}",
                            source_url=f"https://books.toscrape.com/poetry/{identifier}",
                        )
                        first_run = ScrapeRun(
                            status=ScrapeStatus.SUCCESS,
                            started_at=datetime(2026, 1, 1, tzinfo=UTC),
                        )
                        second_run = ScrapeRun(
                            status=ScrapeStatus.FAILED,
                            started_at=datetime(2026, 1, 2, tzinfo=UTC),
                            error_message="Source is unavailable",
                        )
                        session.add_all(
                            [
                                fiction,
                                poetry,
                                Book(
                                    upc=f"one{identifier}",
                                    category=poetry,
                                    title="First Poetry Book",
                                    description=None,
                                    price=Decimal("10.00"),
                                    stock_quantity=1,
                                    rating=3,
                                    product_url=f"https://books.toscrape.com/book-one/{identifier}",
                                    image_url=None,
                                ),
                                Book(
                                    upc=f"two{identifier}",
                                    category=poetry,
                                    title="Second Poetry Book",
                                    description=None,
                                    price=Decimal("20.00"),
                                    stock_quantity=1,
                                    rating=4,
                                    product_url=f"https://books.toscrape.com/book-two/{identifier}",
                                    image_url=None,
                                ),
                                first_run,
                                second_run,
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
                            categories_response = await client.get("/categories", params={"limit": "10"})
                            runs_response = await client.get("/scrape-runs", params={"limit": "1"})
                            run_response = await client.get(f"/scrape-runs/{second_run.id}")
                            missing_run_response = await client.get("/scrape-runs/999999")
                            invalid_run_response = await client.get("/scrape-runs/0")
                    finally:
                        app.dependency_overrides.pop(get_session, None)

                    category_counts = {
                        category["name"]: category["books_count"]
                        for category in categories_response.json()["items"]
                    }
                    assert categories_response.status_code == 200
                    assert categories_response.json()["total"] == 2
                    assert category_counts[fiction.name] == 0
                    assert category_counts[poetry.name] == 2
                    assert runs_response.status_code == 200
                    assert runs_response.json()["total"] == 2
                    assert runs_response.json()["items"][0]["id"] == second_run.id
                    assert run_response.status_code == 200
                    assert run_response.json()["status"] == "failed"
                    assert missing_run_response.status_code == 404
                    assert invalid_run_response.status_code == 422
                finally:
                    await transaction.rollback()
        finally:
            await engine.dispose()

    asyncio.run(scenario())
