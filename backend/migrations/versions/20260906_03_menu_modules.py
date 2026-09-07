"""Add administrable module grouping to navigation menus.

Revision ID: 20260906_03
Revises: 20260906_02
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260906_03"
down_revision: str | None = "20260906_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "menus",
        sa.Column("module_code", sa.String(length=80), nullable=False, server_default="general"),
        schema="app",
    )
    op.add_column(
        "menus",
        sa.Column("module_label", sa.String(length=120), nullable=False, server_default="General"),
        schema="app",
    )
    op.execute(
        "UPDATE app.menus SET module_code = 'security', module_label = 'Seguridad' "
        "WHERE code IN ('users', 'roles', 'permissions', 'menus', 'audit')"
    )
    op.execute(
        "UPDATE app.menus SET module_code = 'parameters', module_label = 'Parámetros generales' "
        "WHERE code IN ('parameters', 'llm')"
    )
    op.execute(
        "UPDATE app.menus SET module_code = 'home', module_label = 'Principal' WHERE code = 'home'"
    )


def downgrade() -> None:
    op.drop_column("menus", "module_label", schema="app")
    op.drop_column("menus", "module_code", schema="app")
