import asyncio
import os

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import get_session
from app.db.models import ScrapeRun, ScrapeStatus
from app.main import app


@pytest.mark.integration
def test_start_scrape_creates_one_pending_run(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")

    started_run_ids: list[int] = []

    async def fake_run_scraping(run_id: int) -> None:
        started_run_ids.append(run_id)

    monkeypatch.setattr("app.api.scrape.run_scraping", fake_run_scraping)

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
                    async def get_test_session():
                        async with session_factory() as session:
                            yield session

                    app.dependency_overrides[get_session] = get_test_session
                    try:
                        async with httpx.AsyncClient(
                            transport=httpx.ASGITransport(app=app),
                            base_url="http://test",
                        ) as client:
                            response = await client.post("/scrape")
                    finally:
                        app.dependency_overrides.pop(get_session, None)

                    assert response.status_code == 202
                    response_data = response.json()
                    run_id = response_data["run_id"]
                    assert response_data["status"] == "pending"
                    assert started_run_ids == [run_id]

                    async with session_factory() as session:
                        runs_count = await session.scalar(select(func.count()).select_from(ScrapeRun))
                        scrape_run = await session.get(ScrapeRun, run_id)

                    assert runs_count == 1
                    assert scrape_run is not None
                    assert scrape_run.status == ScrapeStatus.PENDING
                finally:
                    await transaction.rollback()
        finally:
            await engine.dispose()

    asyncio.run(scenario())
