"""Enable concurrent data sources and source-scoped analysis catalogs.

Revision ID: 20260930_16
Revises: 20260923_15
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260930_16"
down_revision: str | None = "20260923_15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(
        "uq_app_data_connections_single_active",
        table_name="data_connections",
        schema="app",
    )
    op.create_table(
        "analysis_catalogs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "data_connection_id",
            sa.Integer(),
            sa.ForeignKey("app.data_connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("domain_code", sa.String(length=40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="2"),
        sa.Column(
            "configuration_document",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "updated_by_user_id",
            sa.Integer(),
            sa.ForeignKey("app.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("updated_by_label", sa.String(length=320), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "data_connection_id",
            "domain_code",
            name="uq_app_analysis_catalog_source_domain",
        ),
        schema="app",
    )
    op.create_index(
        "ix_app_analysis_catalogs_data_connection_id",
        "analysis_catalogs",
        ["data_connection_id"],
        schema="app",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_app_analysis_catalogs_data_connection_id",
        table_name="analysis_catalogs",
        schema="app",
    )
    op.drop_table("analysis_catalogs", schema="app")
    op.create_index(
        "uq_app_data_connections_single_active",
        "data_connections",
        ["is_active"],
        unique=True,
        schema="app",
        postgresql_where=sa.text("is_active = true"),
    )
