from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.db.models import ScrapeRun
from app.repositories.scrape_runs import ScrapeRunRepository
from app.schemas.scrape_runs import ScrapeRunListResponse, ScrapeRunResponse

router = APIRouter(prefix="/scrape-runs", tags=["scrape-runs"])


@router.get("", response_model=ScrapeRunListResponse)
async def list_scrape_runs(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ScrapeRunListResponse:
    runs, total = await ScrapeRunRepository(session).list_runs(limit, offset)
    return ScrapeRunListResponse(items=runs, total=total, limit=limit, offset=offset)


@router.get("/{run_id}", response_model=ScrapeRunResponse)
async def get_scrape_run(
    run_id: Annotated[int, Path(ge=1)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScrapeRun:
    scrape_run = await ScrapeRunRepository(session).get_by_id(run_id)
    if scrape_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scrape run not found")
    return scrape_run
