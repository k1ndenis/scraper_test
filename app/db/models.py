from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ScrapeStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Category(TimestampMixin, Base):

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    source_url: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
    )

    books: Mapped[list[Book]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Book(TimestampMixin, Base):

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)

    upc: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    product_url: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    category: Mapped[Category] = relationship(
        back_populates="books",
    )


class ScrapeRun(Base):

    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    status: Mapped[ScrapeStatus] = mapped_column(
        SqlEnum(
            ScrapeStatus,
            name="scrape_status",
            values_callable=lambda statuses: [
                status.value for status in statuses
            ],
        ),
        default=ScrapeStatus.PENDING,
        server_default=ScrapeStatus.PENDING.value,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    categories_processed: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )
    books_processed: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )
    books_created: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )
    books_updated: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )
    errors_count: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )