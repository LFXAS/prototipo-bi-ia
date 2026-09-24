"""Add immutable ETL execution preparation records.

Revision ID: 20260922_14
Revises: 20260920_13
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260922_14"
down_revision: str | None = "20260920_13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "etl_executions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "proposal_id",
            sa.Integer(),
            sa.ForeignKey("app.bi_proposals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "metadata_snapshot_id",
            sa.Integer(),
            sa.ForeignKey("app.metadata_snapshots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("domain_code", sa.String(length=40), nullable=False),
        sa.Column("builder_version", sa.String(length=40), nullable=False),
        sa.Column("proposal_hash", sa.String(length=64), nullable=False),
        sa.Column("snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("selection_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("plan_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("validation_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metrics_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            sa.ForeignKey("app.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_by_label", sa.String(length=320), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('prepared', 'running', 'succeeded', 'validation_warning', 'failed')",
            name="ck_etl_executions_status",
        ),
        schema="app",
    )
    op.create_index(
        "ix_app_etl_executions_proposal_id", "etl_executions", ["proposal_id"], schema="app"
    )
    op.create_index(
        "ix_app_etl_executions_metadata_snapshot_id",
        "etl_executions",
        ["metadata_snapshot_id"],
        schema="app",
    )
    op.create_index("ix_app_etl_executions_status", "etl_executions", ["status"], schema="app")
    op.create_index(
        "ix_app_etl_executions_created_at", "etl_executions", ["created_at"], schema="app"
    )


def downgrade() -> None:
    op.drop_index("ix_app_etl_executions_created_at", table_name="etl_executions", schema="app")
    op.drop_index("ix_app_etl_executions_status", table_name="etl_executions", schema="app")
    op.drop_index(
        "ix_app_etl_executions_metadata_snapshot_id", table_name="etl_executions", schema="app"
    )
    op.drop_index("ix_app_etl_executions_proposal_id", table_name="etl_executions", schema="app")
    op.drop_table("etl_executions", schema="app")
