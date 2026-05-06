from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String, Uuid, func
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(Uuid(), primary_key=True, nullable=False),
    )
    email: str = Field(
        sa_column=Column(String(255), nullable=False, unique=True, index=True),
    )
    password_hash: str = Field(
        sa_column=Column(String(255), nullable=False),
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )
