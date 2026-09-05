import asyncio
import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Book, ScrapeRun, ScrapeStatus
from app.services.scraping import run_scraping

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "book_page.html"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"


@pytest.mark.integration
def test_run_scraping_persists_books_and_counters() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")

    identifier = uuid4().hex
    product_urls = [
        f"https://books.toscrape.com/catalogue/book-one_{identifier}/index.html",
        f"https://books.toscrape.com/catalogue/book-two_{identifier}/index.html",
        f"https://books.toscrape.com/catalogue/broken-book_{identifier}/index.html",
    ]
    catalog_html = "".join(
        f'<article class="product_pod"><h3><a href="{url}">Book</a></h3></article>'
        for url in product_urls
    )

    class MockScraperHttpClient:
        def __init__(self) -> None:
            self.pages = {
                START_URL: catalog_html,
                product_urls[0]: FIXTURE_PATH.read_text().replace("a897fe39b1053632", f"one{identifier}"),
                product_urls[1]: (
                    FIXTURE_PATH.read_text()
                    .replace("A Light in the Attic", "Second Book")
                    .replace("a897fe39b1053632", f"two{identifier}")
                ),
                product_urls[2]: "<html><body></body></html>",
            }

        async def get_text(self, url: str) -> str:
            return self.pages[url]

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
                    scrape_run = await run_scraping(
                        MockScraperHttpClient(),
                        start_url=START_URL,
                        session_factory=session_factory,
                    )

                    assert scrape_run.status == ScrapeStatus.SUCCESS
                    assert scrape_run.books_processed == 2
                    assert scrape_run.books_created == 2
                    assert scrape_run.books_updated == 0
                    assert scrape_run.errors_count == 1
                    assert scrape_run.categories_processed == 1
                    assert scrape_run.started_at is not None
                    assert scrape_run.finished_at is not None

                    async with session_factory() as session:
                        saved_books = (await session.scalars(select(Book))).all()
                        saved_run = await session.get(ScrapeRun, scrape_run.id)

                    assert len(saved_books) == 2
                    assert saved_run is not None
                    assert saved_run.status == ScrapeStatus.SUCCESS
                finally:
                    await transaction.rollback()

            async with AsyncSession(engine) as session:
                assert await session.get(ScrapeRun, scrape_run.id) is None
        finally:
            await engine.dispose()

    asyncio.run(scenario())


@pytest.mark.integration
def test_run_scraping_records_failed_run_after_unexpected_error() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")

    class FailingScraperHttpClient:
        async def get_text(self, url: str) -> str:
            raise RuntimeError("Catalog is unavailable")

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
                    with pytest.raises(RuntimeError, match="Catalog is unavailable"):
                        await run_scraping(
                            FailingScraperHttpClient(),
                            start_url=START_URL,
                            session_factory=session_factory,
                        )

                    async with session_factory() as session:
                        failed_run = await session.scalar(
                            select(ScrapeRun).where(ScrapeRun.status == ScrapeStatus.FAILED)
                        )

                    assert failed_run is not None
                    assert failed_run.started_at is not None
                    assert failed_run.finished_at is not None
                    assert failed_run.error_message == "Catalog is unavailable"
                finally:
                    await transaction.rollback()
        finally:
            await engine.dispose()

    asyncio.run(scenario())
