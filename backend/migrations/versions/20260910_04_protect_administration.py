"""Protect bootstrap security records from unsafe administrative changes.

Revision ID: 20260910_04
Revises: 20260906_03
Create Date: 2026-09-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_04"
down_revision: str | None = "20260906_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table in ("users", "roles", "permissions", "menus"):
        op.add_column(
            table,
            sa.Column(
                "is_system_protected", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
            schema="app",
        )
    op.execute("UPDATE app.roles SET is_system_protected = true WHERE code = 'administrator'")
    op.execute(
        "UPDATE app.permissions SET is_system_protected = true "
        "WHERE code LIKE 'security.%' OR code IN "
        "('audit.read', 'parameters.read', 'parameters.write', "
        "'parameters.llm.read', 'parameters.llm.write', 'parameters.connections.test')"
    )
    op.execute("UPDATE app.menus SET is_system_protected = true")


def downgrade() -> None:
    for table in ("menus", "permissions", "roles", "users"):
        op.drop_column(table, "is_system_protected", schema="app")
