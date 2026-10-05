"""Persist metadata-grounded, non-executable need reviews."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261003_19"
down_revision: str | None = "20261001_18"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "business_need_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "metadata_snapshot_id",
            sa.Integer(),
            sa.ForeignKey("app.metadata_snapshots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("assessment_hash", sa.String(64), nullable=False),
        sa.Column("assessment_document", postgresql.JSONB(), nullable=False),
        sa.Column("provider_kind", sa.String(40), nullable=False),
        sa.Column("model_id", sa.String(160), nullable=False),
        sa.Column(
            "created_by_user_id", sa.Integer(), sa.ForeignKey("app.users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        schema="app",
    )
    for name in ("input_hash", "assessment_hash"):
        op.create_index(
            f"ix_app_business_need_reviews_{name}", "business_need_reviews", [name], schema="app"
        )


def downgrade() -> None:
    op.drop_table("business_need_reviews", schema="app")
