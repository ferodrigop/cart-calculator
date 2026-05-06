from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, Numeric
from sqlmodel import Field, SQLModel


class Checkout(SQLModel, table=True):
    __tablename__ = "checkouts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
    items: list[dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False))
    subtotal: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    taxes: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    discount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    total: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
