from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.db.models import ScrapeRun, ScrapeStatus
from app.db.session import async_session_factory
from app.repositories.books import BookRepository, SaveBookResult
from app.scraper.catalog import collect_product_urls
from app.scraper.http_client import ScraperHttpClient
from app.scraper.runner import load_product_pages


async def run_scraping(
    client: ScraperHttpClient | None = None,
    *,
    start_url: str | None = None,
    session_factory: async_sessionmaker[AsyncSession] = async_session_factory,
) -> ScrapeRun:
    scraper_client = client or ScraperHttpClient()

    try:
        return await _run_scraping(
            scraper_client,
            start_url or get_settings().scraper_start_url,
            session_factory,
        )
    finally:
        if client is None:
            await scraper_client.aclose()


async def _run_scraping(
    client: ScraperHttpClient,
    start_url: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> ScrapeRun:
    async with session_factory() as session:
        scrape_run = ScrapeRun(
            status=ScrapeStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        session.add(scrape_run)
        await session.commit()
        scrape_run_id = scrape_run.id

        try:
            product_urls = await collect_product_urls(start_url, client)
            load_result = await load_product_pages(product_urls, client)
            repository = BookRepository(session)
            created_count = 0
            updated_count = 0

            for book in load_result.books:
                save_result = await repository.save(book)
                if save_result == SaveBookResult.CREATED:
                    created_count += 1
                elif save_result == SaveBookResult.UPDATED:
                    updated_count += 1

            scrape_run.books_processed = len(load_result.books)
            scrape_run.books_created = created_count
            scrape_run.books_updated = updated_count
            scrape_run.errors_count = len(load_result.errors)
            scrape_run.categories_processed = len(
                {book.category_url for book in load_result.books}
            )
            scrape_run.status = ScrapeStatus.SUCCESS
            scrape_run.finished_at = datetime.now(UTC)
            await session.commit()
            return scrape_run
        except Exception as error:
            await session.rollback()
            await _mark_scrape_run_failed(session_factory, scrape_run_id, str(error))
            raise


async def _mark_scrape_run_failed(
    session_factory: async_sessionmaker[AsyncSession],
    scrape_run_id: int,
    error_message: str,
) -> None:
    async with session_factory() as session:
        scrape_run = await session.get(ScrapeRun, scrape_run_id)
        if scrape_run is None:
            return

        scrape_run.status = ScrapeStatus.FAILED
        scrape_run.finished_at = datetime.now(UTC)
        scrape_run.error_message = error_message
        await session.commit()
