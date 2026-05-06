"""create_checkouts

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-06 00:01:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "checkouts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("taxes", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_checkouts_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_checkouts"),
    )
    op.create_index("ix_checkouts_user_id", "checkouts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_checkouts_user_id", table_name="checkouts")
    op.drop_table("checkouts")
