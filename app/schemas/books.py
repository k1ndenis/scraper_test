from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source_url: str


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    upc: str
    title: str
    description: str | None
    price: Decimal
    stock_quantity: int
    rating: int
    product_url: str
    image_url: str | None
    category: CategoryResponse


class BookListResponse(BaseModel):
    items: list[BookResponse]
    total: int
    limit: int
    offset: int
