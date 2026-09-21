"""Allow auditable proposal invalidation and discard states.

Revision ID: 20260920_13
Revises: 20260919_12
Create Date: 2026-09-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260920_13"
down_revision: str | None = "20260919_12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_bi_proposals_status",
        "bi_proposals",
        schema="app",
        type_="check",
    )
    op.create_check_constraint(
        "ck_bi_proposals_status",
        "bi_proposals",
        "status IN ('generating', 'provider_failed', 'validation_failed', "
        "'ready_for_review', 'approved', 'rejected', 'invalidated', 'discarded')",
        schema="app",
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE app.bi_proposals SET status = 'rejected' "
            "WHERE status IN ('invalidated', 'discarded')"
        )
    )
    op.drop_constraint(
        "ck_bi_proposals_status",
        "bi_proposals",
        schema="app",
        type_="check",
    )
    op.create_check_constraint(
        "ck_bi_proposals_status",
        "bi_proposals",
        "status IN ('generating', 'provider_failed', 'validation_failed', "
        "'ready_for_review', 'approved', 'rejected')",
        schema="app",
    )
