"""Record the enabled domain profile on each BI proposal.

Revision ID: 20260919_10
Revises: 20260919_09
Create Date: 2026-09-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_10"
down_revision: str | None = "20260919_09"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "bi_proposals",
        sa.Column(
            "domain_code",
            sa.String(length=40),
            server_default="ventas",
            nullable=False,
        ),
        schema="app",
    )
    op.alter_column("bi_proposals", "domain_code", server_default=None, schema="app")


def downgrade() -> None:
    op.drop_column("bi_proposals", "domain_code", schema="app")
