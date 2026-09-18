"""Add web-managed SQL Server connections and approved operational parameters.

Revision ID: 20260918_07
Revises: 20260918_06
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260918_07"
down_revision: str | None = "20260918_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "parameters",
        sa.Column("name", sa.String(length=160), nullable=False, server_default=""),
        schema="app",
    )
    op.add_column(
        "parameters",
        sa.Column("module_code", sa.String(length=80), nullable=False, server_default="general"),
        schema="app",
    )
    op.add_column(
        "parameters",
        sa.Column("value_type", sa.String(length=30), nullable=False, server_default="integer"),
        schema="app",
    )
    op.add_column(
        "parameters",
        sa.Column("default_value", sa.Text(), nullable=False, server_default=""),
        schema="app",
    )
    op.add_column("parameters", sa.Column("min_value", sa.Integer(), nullable=True), schema="app")
    op.add_column("parameters", sa.Column("max_value", sa.Integer(), nullable=True), schema="app")

    op.create_table(
        "data_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("connector_kind", sa.String(length=40), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("database_name", sa.String(length=128), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("encrypt", sa.Boolean(), nullable=False),
        sa.Column("trust_server_certificate", sa.Boolean(), nullable=False),
        sa.Column(
            "secret_id",
            sa.Integer(),
            sa.ForeignKey("app.secrets.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_test_status", sa.String(length=40), nullable=True),
        sa.Column("last_test_message", sa.Text(), nullable=True),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        schema="app",
    )
    op.create_index(
        "ix_app_data_connections_connector_kind",
        "data_connections",
        ["connector_kind"],
        schema="app",
    )
    op.create_index(
        "uq_app_data_connections_single_active",
        "data_connections",
        ["is_active"],
        unique=True,
        schema="app",
        postgresql_where=sa.text("is_active = true"),
    )
    op.execute(
        "UPDATE app.permissions SET code = 'connections.test', "
        "name = 'Probar conexiones', description = 'Permite validar fuentes de solo lectura.' "
        "WHERE code = 'parameters.connections.test'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE app.permissions SET code = 'parameters.connections.test', "
        "name = 'Probar conexiones', "
        "description = 'Permite probar conexiones externas de solo lectura.' "
        "WHERE code = 'connections.test'"
    )
    op.drop_index(
        "uq_app_data_connections_single_active", table_name="data_connections", schema="app"
    )
    op.drop_index(
        "ix_app_data_connections_connector_kind", table_name="data_connections", schema="app"
    )
    op.drop_table("data_connections", schema="app")
    op.drop_column("parameters", "max_value", schema="app")
    op.drop_column("parameters", "min_value", schema="app")
    op.drop_column("parameters", "default_value", schema="app")
    op.drop_column("parameters", "value_type", schema="app")
    op.drop_column("parameters", "module_code", schema="app")
    op.drop_column("parameters", "name", schema="app")
