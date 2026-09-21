"""Link each analyst revision to its source proposal.

Revision ID: 20260919_11
Revises: 20260919_10
Create Date: 2026-09-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_11"
down_revision: str | None = "20260919_10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "bi_proposals",
        sa.Column("source_proposal_id", sa.Integer(), nullable=True),
        schema="app",
    )
    op.create_foreign_key(
        "fk_bi_proposals_source_proposal_id",
        "bi_proposals",
        "bi_proposals",
        ["source_proposal_id"],
        ["id"],
        source_schema="app",
        referent_schema="app",
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_bi_proposals_source_proposal_id",
        "bi_proposals",
        ["source_proposal_id"],
        schema="app",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_bi_proposals_source_proposal_id",
        table_name="bi_proposals",
        schema="app",
    )
    op.drop_constraint(
        "fk_bi_proposals_source_proposal_id",
        "bi_proposals",
        schema="app",
        type_="foreignkey",
    )
    op.drop_column("bi_proposals", "source_proposal_id", schema="app")
