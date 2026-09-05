from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.repositories.categories import CategoryRepository
from app.schemas.categories import CategoryListResponse, CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CategoryListResponse:
    categories, total = await CategoryRepository(session).list_categories(limit, offset)
    return CategoryListResponse(
        items=[
            CategoryResponse(
                id=category.id,
                name=category.name,
                source_url=category.source_url,
                books_count=books_count,
            )
            for category, books_count in categories
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
