from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: int
    name: str
    source_url: str
    books_count: int


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]
    total: int
    limit: int
    offset: int
