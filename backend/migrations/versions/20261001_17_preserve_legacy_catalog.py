"""Preserve the pre-multisource analysis catalog on its original connection.

Revision ID: 20261001_17
Revises: 20260930_16
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261001_17"
down_revision: str | None = "20260930_16"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_MIGRATION_LABEL = "Migración automática del catálogo analítico legado"


def upgrade() -> None:
    # Before source-scoped catalogs existed, the editable catalog lived in one
    # parameter and therefore belonged to the original (earliest) connection.
    # Copy it once without relying on a database name or vendor sample.
    op.execute(
        sa.text(
            """
            INSERT INTO app.analysis_catalogs (
                data_connection_id,
                domain_code,
                version,
                configuration_document,
                updated_by_user_id,
                updated_by_label
            )
            SELECT
                original_connection.id,
                'ventas',
                COALESCE(NULLIF(legacy.value::jsonb ->> 'version', '')::integer, 2),
                legacy.value::jsonb,
                NULL,
                :migration_label
            FROM app.parameters AS legacy
            CROSS JOIN LATERAL (
                SELECT id
                FROM app.data_connections
                ORDER BY id
                LIMIT 1
            ) AS original_connection
            WHERE legacy.key = 'COPILOT_SALES_NEEDS_CATALOG'
              AND legacy.value IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM app.analysis_catalogs AS scoped
                  WHERE scoped.data_connection_id = original_connection.id
                    AND scoped.domain_code = 'ventas'
              )
            """
        ).bindparams(migration_label=_MIGRATION_LABEL)
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM app.analysis_catalogs
            WHERE domain_code = 'ventas'
              AND updated_by_label = :migration_label
            """
        ).bindparams(migration_label=_MIGRATION_LABEL)
    )
