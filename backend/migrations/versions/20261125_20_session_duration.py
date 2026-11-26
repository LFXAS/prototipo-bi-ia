"""Add the editable duration for newly issued sessions without changing existing data."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261125_20"
down_revision: str | None = "20261003_19"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "INSERT INTO app.parameters "
            "(key, name, module_code, value_type, value, default_value, min_value, max_value, "
            "description, is_active) VALUES "
            "('AUTH_SESSION_MINUTES', 'Duración de la sesión (minutos)', 'security', 'integer', "
            "'60', '60', 15, 240, "
            "'Duración absoluta de las sesiones nuevas, entre 15 y 240 minutos. "
            "El cambio se aplica al volver a iniciar sesión; no renueva tokens existentes.', true) "
            "ON CONFLICT (key) DO NOTHING"
        )
    )


def downgrade() -> None:
    # This is an additive data setting. Older code ignores it; preserve an
    # administrator's chosen value when rolling the application back.
    pass
