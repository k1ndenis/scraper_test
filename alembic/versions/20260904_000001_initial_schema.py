"""initial schema

Revision ID: 20260904_000001
Revises:
Create Date: 2026-09-04 00:00:01
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260904_000001"
down_revision = None
branch_labels = None
depends_on = None


scrape_status = sa.Enum("pending", "running", "success", "failed", name="scrape_status")


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("name", name=op.f("uq_categories_name")),
        sa.UniqueConstraint("source_url", name=op.f("uq_categories_source_url")),
    )

    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("status", scrape_status, server_default="pending", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("categories_processed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("books_processed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("books_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("books_updated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("errors_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scrape_runs")),
    )

    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("upc", sa.String(length=64), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("product_url", sa.String(length=500), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_books_category_id_categories"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_books")),
        sa.UniqueConstraint("product_url", name=op.f("uq_books_product_url")),
        sa.UniqueConstraint("upc", name=op.f("uq_books_upc")),
    )
    op.create_index(op.f("ix_books_title"), "books", ["title"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_books_title"), table_name="books")
    op.drop_table("books")
    op.drop_table("scrape_runs")
    op.drop_table("categories")
