"""Restore approvals invalidated by the former verification side effect.

Revision ID: 20261001_18
Revises: 20261001_17
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261001_18"
down_revision: str | None = "20261001_17"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_AUTOMATIC_COMMENT = (
    "Aprobación retirada automáticamente: la versión no supera las reglas determinísticas vigentes."
)
_RESTORE_LABEL = "Corrección auditable de compatibilidad histórica"
_RESTORE_COMMENT = (
    "Aprobación restaurada: la retirada automática fue un falso positivo de "
    "reconstrucción histórica y existe una ejecución ETL conciliada."
)
_AUDIT_ACTION = "copilot.proposal.approval_restored"


def upgrade() -> None:
    connection = op.get_bind()
    restored_ids = [
        row[0]
        for row in connection.execute(
            sa.text(
                """
                UPDATE app.bi_proposals AS proposal
                SET status = 'approved',
                    review_comment = :restore_comment,
                    warnings_confirmed = TRUE,
                    reviewed_by_user_id = NULL,
                    reviewed_by_label = :restore_label,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE proposal.status = 'invalidated'
                  AND proposal.review_comment = :old_comment
                  AND EXISTS (
                      SELECT 1
                      FROM app.etl_executions AS execution
                      WHERE execution.proposal_id = proposal.id
                        AND execution.status IN ('succeeded', 'validation_warning')
                        AND execution.metrics_document #>> '{reconciliation,passed}' = 'true'
                  )
                RETURNING proposal.id
                """
            ).bindparams(
                restore_comment=_RESTORE_COMMENT,
                restore_label=_RESTORE_LABEL,
                old_comment=_OLD_AUTOMATIC_COMMENT,
            )
        )
    ]
    for proposal_id in restored_ids:
        connection.execute(
            sa.text(
                """
                INSERT INTO app.audit_events (
                    actor_user_id,
                    actor_label,
                    action,
                    resource_type,
                    resource_id,
                    detail
                ) VALUES (
                    NULL,
                    :restore_label,
                    :audit_action,
                    'bi_proposal',
                    :resource_id,
                    CAST(:detail AS json)
                )
                """
            ).bindparams(
                restore_label=_RESTORE_LABEL,
                audit_action=_AUDIT_ACTION,
                resource_id=str(proposal_id),
                detail=(
                    '{"reason":"false_positive_read_only_verification",'
                    '"reconciled_execution_required":true}'
                ),
            )
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            DELETE FROM app.audit_events
            WHERE action = :audit_action
              AND actor_label = :restore_label
            """
        ).bindparams(audit_action=_AUDIT_ACTION, restore_label=_RESTORE_LABEL)
    )
    connection.execute(
        sa.text(
            """
            UPDATE app.bi_proposals
            SET status = 'invalidated',
                review_comment = :old_comment,
                warnings_confirmed = FALSE,
                reviewed_by_user_id = NULL,
                reviewed_by_label = NULL,
                reviewed_at = NULL
            WHERE status = 'approved'
              AND review_comment = :restore_comment
              AND reviewed_by_label = :restore_label
            """
        ).bindparams(
            old_comment=_OLD_AUTOMATIC_COMMENT,
            restore_comment=_RESTORE_COMMENT,
            restore_label=_RESTORE_LABEL,
        )
    )
