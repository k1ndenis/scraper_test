from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models import ScrapeStatus


class ScrapeRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ScrapeStatus
    started_at: datetime | None
    finished_at: datetime | None
    categories_processed: int
    books_processed: int
    books_created: int
    books_updated: int
    errors_count: int
    error_message: str | None


class ScrapeRunListResponse(BaseModel):
    items: list[ScrapeRunResponse]
    total: int
    limit: int
    offset: int


class ScrapeStartResponse(BaseModel):
    run_id: int
    status: ScrapeStatus
