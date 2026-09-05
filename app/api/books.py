from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.db.models import Book
from app.repositories.books import BookListFilters, BookRepository
from app.schemas.books import BookListResponse, BookResponse

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=BookListResponse)
async def list_books(
    session: Annotated[AsyncSession, Depends(get_session)],
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    category: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    min_price: Annotated[Decimal | None, Query(ge=0)] = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    rating: Annotated[int | None, Query(ge=1, le=5)] = None,
    in_stock: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> BookListResponse:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="min_price must not exceed max_price",
        )

    books, total = await BookRepository(session).list_books(
        BookListFilters(
            search=search,
            category=category,
            min_price=min_price,
            max_price=max_price,
            rating=rating,
            in_stock=in_stock,
        ),
        limit,
        offset,
    )
    return BookListResponse(items=books, total=total, limit=limit, offset=offset)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: Annotated[int, Path(ge=1)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Book:
    book = await BookRepository(session).get_by_id(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book
