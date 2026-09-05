from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.db.models import ScrapeRun, ScrapeStatus
from app.schemas.scrape_runs import ScrapeStartResponse
from app.services.scraping import run_scraping

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("", response_model=ScrapeStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scraping(
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScrapeStartResponse:
    scrape_run = ScrapeRun(status=ScrapeStatus.PENDING)
    session.add(scrape_run)
    await session.commit()

    background_tasks.add_task(run_scraping, scrape_run.id)
    return ScrapeStartResponse(run_id=scrape_run.id, status=scrape_run.status)
