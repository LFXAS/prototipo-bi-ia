"""Persist contextual semantic advice conversations.

Revision ID: 20260923_15
Revises: 20260922_14
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260923_15"
down_revision: str | None = "20260922_14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "semantic_advice",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "proposal_id",
            sa.Integer(),
            sa.ForeignKey("app.bi_proposals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("concept_code", sa.String(length=80), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("response_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("provider_kind", sa.String(length=40), nullable=False),
        sa.Column("model_id", sa.String(length=160), nullable=False),
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
        schema="app",
    )
    op.create_index(
        "ix_app_semantic_advice_proposal_id",
        "semantic_advice",
        ["proposal_id"],
        schema="app",
    )
    op.create_index(
        "ix_app_semantic_advice_concept_code",
        "semantic_advice",
        ["concept_code"],
        schema="app",
    )
    op.create_index(
        "ix_app_semantic_advice_created_at",
        "semantic_advice",
        ["created_at"],
        schema="app",
    )


def downgrade() -> None:
    op.drop_index("ix_app_semantic_advice_created_at", table_name="semantic_advice", schema="app")
    op.drop_index("ix_app_semantic_advice_concept_code", table_name="semantic_advice", schema="app")
    op.drop_index("ix_app_semantic_advice_proposal_id", table_name="semantic_advice", schema="app")
    op.drop_table("semantic_advice", schema="app")
