import jwt

from app.core.config import settings
from app.modules.security.models import AuditEvent
from app.modules.security.service import (
    DEFAULT_MENUS,
    DEFAULT_PERMISSIONS,
    RECOVERY_PERMISSION_CODES,
    create_access_token,
    generated_role_code,
    hash_password,
    verify_password,
)


def test_password_is_hashed_and_verified() -> None:
    encoded = hash_password("ClaveDePruebaSegura2026")

    assert encoded != "ClaveDePruebaSegura2026"
    assert verify_password("ClaveDePruebaSegura2026", encoded)
    assert not verify_password("OtraClaveDePrueba2026", encoded)


def test_access_token_contains_subject() -> None:
    token = create_access_token(42)
    payload = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "42"


def test_generated_role_code_is_stable_and_human_name_does_not_need_a_technical_value() -> None:
    assert generated_role_code("Analista de Ventas") == "analista-de-ventas"
    assert generated_role_code("Gestión Ñandú") == "gestion-nandu"


def test_audit_actor_reference_is_cleared_when_a_user_is_deleted() -> None:
    foreign_key = next(iter(AuditEvent.__table__.c.actor_user_id.foreign_keys))

    assert foreign_key.ondelete == "SET NULL"


def test_seed_catalog_is_consistent_and_has_the_recovery_permissions() -> None:
    permission_codes = {code for code, _, _ in DEFAULT_PERMISSIONS}

    assert len(permission_codes) == len(DEFAULT_PERMISSIONS)
    assert RECOVERY_PERMISSION_CODES.issubset(permission_codes)
    assert all(
        set(menu_permissions).issubset(permission_codes) for *_, menu_permissions in DEFAULT_MENUS
    )
