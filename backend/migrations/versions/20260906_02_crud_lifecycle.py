"""Add permission lifecycle flag for Sprint 2 CRUD.

Revision ID: 20260906_02
Revises: 20260906_01
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260906_02"
down_revision: str | None = "20260906_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "permissions",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        schema="app",
    )


def downgrade() -> None:
    op.drop_column("permissions", "is_active", schema="app")
