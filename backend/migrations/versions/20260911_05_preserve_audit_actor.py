"""Preserve audit events when a non-protected user is deleted.

Revision ID: 20260911_05
Revises: 20260910_04
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260911_05"
down_revision: str | None = "20260910_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audit_events", sa.Column("actor_label", sa.String(length=320), nullable=True), schema="app"
    )
    op.execute(
        "UPDATE app.audit_events AS audit "
        "SET actor_label = users.full_name || ' <' || users.email || '>' "
        "FROM app.users AS users WHERE audit.actor_user_id = users.id"
    )
    op.drop_constraint(
        "audit_events_actor_user_id_fkey", "audit_events", schema="app", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_audit_events_actor_user_id_users",
        "audit_events",
        "users",
        ["actor_user_id"],
        ["id"],
        source_schema="app",
        referent_schema="app",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_audit_events_actor_user_id_users", "audit_events", schema="app", type_="foreignkey"
    )
    op.create_foreign_key(
        "audit_events_actor_user_id_fkey",
        "audit_events",
        "users",
        ["actor_user_id"],
        ["id"],
        source_schema="app",
        referent_schema="app",
    )
    op.drop_column("audit_events", "actor_label", schema="app")
