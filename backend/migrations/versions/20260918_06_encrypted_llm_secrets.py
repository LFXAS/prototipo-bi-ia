"""Store LLM credentials encrypted outside environment configuration.

Revision ID: 20260918_06
Revises: 20260911_05
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260918_06"
down_revision: str | None = "20260911_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "secrets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        schema="app",
    )
    op.create_index("ix_app_secrets_kind", "secrets", ["kind"], schema="app")
    op.add_column(
        "llm_configurations", sa.Column("secret_id", sa.Integer(), nullable=True), schema="app"
    )
    op.create_unique_constraint(
        "uq_llm_configurations_secret_id", "llm_configurations", ["secret_id"], schema="app"
    )
    op.create_foreign_key(
        "fk_llm_configurations_secret_id_secrets",
        "llm_configurations",
        "secrets",
        ["secret_id"],
        ["id"],
        source_schema="app",
        referent_schema="app",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_llm_configurations_secret_id_secrets",
        "llm_configurations",
        schema="app",
        type_="foreignkey",
    )
    op.drop_constraint(
        "uq_llm_configurations_secret_id",
        "llm_configurations",
        schema="app",
        type_="unique",
    )
    op.drop_column("llm_configurations", "secret_id", schema="app")
    op.drop_index("ix_app_secrets_kind", table_name="secrets", schema="app")
    op.drop_table("secrets", schema="app")
