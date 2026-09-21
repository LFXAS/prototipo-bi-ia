"""Add a configurable reasoning level to LLM configurations.

Revision ID: 20260919_12
Revises: 20260919_11
Create Date: 2026-09-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_12"
down_revision: str | None = "20260919_11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "llm_configurations",
        sa.Column(
            "reasoning_level",
            sa.String(length=20),
            nullable=False,
            server_default="minimal",
        ),
        schema="app",
    )
    op.create_check_constraint(
        "ck_llm_configurations_reasoning_level",
        "llm_configurations",
        "reasoning_level IN ('automatic', 'minimal', 'low', 'medium', 'high')",
        schema="app",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_llm_configurations_reasoning_level",
        "llm_configurations",
        schema="app",
        type_="check",
    )
    op.drop_column("llm_configurations", "reasoning_level", schema="app")
