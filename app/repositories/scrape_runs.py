from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ScrapeRun


class ScrapeRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_runs(self, limit: int, offset: int) -> tuple[list[ScrapeRun], int]:
        runs = list(
            (
                await self._session.scalars(
                    select(ScrapeRun).order_by(ScrapeRun.id.desc()).limit(limit).offset(offset)
                )
            ).all()
        )
        total = await self._session.scalar(select(func.count()).select_from(ScrapeRun))
        return runs, total or 0

    async def get_by_id(self, run_id: int) -> ScrapeRun | None:
        return await self._session.scalar(select(ScrapeRun).where(ScrapeRun.id == run_id))
