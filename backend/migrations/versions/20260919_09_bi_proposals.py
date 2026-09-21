"""Add supervised BI proposals generated from immutable metadata.

Revision ID: 20260919_09
Revises: 20260918_08
Create Date: 2026-09-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260919_09"
down_revision: str | None = "20260918_08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bi_proposals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "metadata_snapshot_id",
            sa.Integer(),
            sa.ForeignKey("app.metadata_snapshots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("business_goal", sa.Text(), nullable=False),
        sa.Column("business_questions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("requested_dimensions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("periodicity", sa.String(length=20), nullable=False),
        sa.Column("scope_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("semantic_map_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=30), nullable=False),
        sa.Column("contract_version", sa.Integer(), nullable=False),
        sa.Column("provider_kind", sa.String(length=40), nullable=False),
        sa.Column("model_id", sa.String(length=160), nullable=False),
        sa.Column("proposal_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("validation_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("warnings_confirmed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            sa.ForeignKey("app.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_by_label", sa.String(length=320), nullable=False),
        sa.Column(
            "reviewed_by_user_id",
            sa.Integer(),
            sa.ForeignKey("app.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_by_label", sa.String(length=320), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('generating', 'provider_failed', 'validation_failed', "
            "'ready_for_review', 'approved', 'rejected')",
            name="ck_bi_proposals_status",
        ),
        sa.CheckConstraint("contract_version > 0", name="ck_bi_proposals_contract_version"),
        schema="app",
    )
    op.create_index(
        "ix_app_bi_proposals_metadata_snapshot_id",
        "bi_proposals",
        ["metadata_snapshot_id"],
        schema="app",
    )
    op.create_index("ix_app_bi_proposals_status", "bi_proposals", ["status"], schema="app")
    op.create_index("ix_app_bi_proposals_input_hash", "bi_proposals", ["input_hash"], schema="app")
    op.create_index("ix_app_bi_proposals_created_at", "bi_proposals", ["created_at"], schema="app")


def downgrade() -> None:
    op.drop_index("ix_app_bi_proposals_created_at", table_name="bi_proposals", schema="app")
    op.drop_index("ix_app_bi_proposals_input_hash", table_name="bi_proposals", schema="app")
    op.drop_index("ix_app_bi_proposals_status", table_name="bi_proposals", schema="app")
    op.drop_index(
        "ix_app_bi_proposals_metadata_snapshot_id",
        table_name="bi_proposals",
        schema="app",
    )
    op.drop_table("bi_proposals", schema="app")
