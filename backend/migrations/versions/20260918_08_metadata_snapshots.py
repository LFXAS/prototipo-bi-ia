"""Add immutable metadata snapshots for the active SQL Server source.

Revision ID: 20260918_08
Revises: 20260918_07
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260918_08"
down_revision: str | None = "20260918_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "metadata_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "data_connection_id",
            sa.Integer(),
            sa.ForeignKey("app.data_connections.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("connector_code", sa.String(length=40), nullable=False),
        sa.Column("database_name", sa.String(length=128), nullable=False),
        sa.Column("contract_version", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("schema_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("schema_count", sa.Integer(), nullable=False),
        sa.Column("table_count", sa.Integer(), nullable=False),
        sa.Column("column_count", sa.Integer(), nullable=False),
        sa.Column("relationship_count", sa.Integer(), nullable=False),
        sa.Column(
            "captured_by_user_id",
            sa.Integer(),
            sa.ForeignKey("app.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("captured_by_label", sa.String(length=320), nullable=False),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("schema_count >= 0", name="ck_metadata_snapshots_schema_count"),
        sa.CheckConstraint("table_count >= 0", name="ck_metadata_snapshots_table_count"),
        sa.CheckConstraint("column_count >= 0", name="ck_metadata_snapshots_column_count"),
        sa.CheckConstraint(
            "relationship_count >= 0", name="ck_metadata_snapshots_relationship_count"
        ),
        sa.UniqueConstraint(
            "data_connection_id",
            "contract_version",
            "content_hash",
            name="uq_metadata_snapshots_source_contract_hash",
        ),
        schema="app",
    )
    op.create_index(
        "ix_app_metadata_snapshots_data_connection_id",
        "metadata_snapshots",
        ["data_connection_id"],
        schema="app",
    )
    op.create_index(
        "ix_app_metadata_snapshots_content_hash",
        "metadata_snapshots",
        ["content_hash"],
        schema="app",
    )
    op.create_index(
        "ix_app_metadata_snapshots_captured_at",
        "metadata_snapshots",
        ["captured_at"],
        schema="app",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_app_metadata_snapshots_captured_at",
        table_name="metadata_snapshots",
        schema="app",
    )
    op.drop_index(
        "ix_app_metadata_snapshots_content_hash",
        table_name="metadata_snapshots",
        schema="app",
    )
    op.drop_index(
        "ix_app_metadata_snapshots_data_connection_id",
        table_name="metadata_snapshots",
        schema="app",
    )
    op.drop_table("metadata_snapshots", schema="app")
