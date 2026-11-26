from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import jwt
import pytest
from fastapi import HTTPException
from pytest import MonkeyPatch

from app.core.config import settings
from app.modules.security.models import AuditEvent
from app.modules.security.service import (
    DEFAULT_MENUS,
    DEFAULT_PERMISSIONS,
    RECOVERY_PERMISSION_CODES,
    create_access_token,
    generated_role_code,
    hash_password,
    session_duration_minutes,
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


@pytest.mark.parametrize(
    "configured_minutes, expected_seconds", [(15, 900), (60, 3600), (120, 7200)]
)
def test_access_token_uses_the_configured_absolute_duration(
    monkeypatch: MonkeyPatch, configured_minutes: int, expected_seconds: int
) -> None:
    monkeypatch.setattr(settings, "jwt_access_token_minutes", configured_minutes)
    token = create_access_token(42)
    payload = jwt.decode(
        token, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_algorithm]
    )

    assert payload["exp"] - payload["iat"] == expected_seconds


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stored, expected",
    [
        ("15", 15),
        ("60", 60),
        ("120", 120),
        ("240", 240),
        ("9999", 240),
        ("0", 15),
        ("invalid", 60),
        (None, 60),
    ],
)
async def test_session_duration_reads_the_parameter_with_safe_bounds_and_fallback(
    monkeypatch: MonkeyPatch, stored: str | None, expected: int
) -> None:
    monkeypatch.setattr(settings, "jwt_access_token_minutes", 60)
    session = SimpleNamespace(scalar=AsyncMock(return_value=stored))

    assert await session_duration_minutes(session) == expected


@pytest.mark.asyncio
async def test_login_issues_the_duration_chosen_in_parameters(monkeypatch: MonkeyPatch) -> None:
    from app.modules.security import router
    from app.modules.security.schemas import LoginRequest

    user = SimpleNamespace(id=42, is_active=True, password_hash="test-only")
    session = SimpleNamespace(
        execute=AsyncMock(return_value=Mock(scalar_one_or_none=Mock(return_value=user))),
        scalar=AsyncMock(return_value="120"),
        commit=AsyncMock(),
    )
    monkeypatch.setattr(router, "verify_password", lambda *_: True)
    monkeypatch.setattr(router, "add_audit_event", AsyncMock())
    result = await router.login(
        LoginRequest(email="qa@example.com", password="test-only-password"), session
    )
    payload = jwt.decode(
        result.access_token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["exp"] - payload["iat"] == 7200
    session.scalar.assert_awaited_once()


@pytest.mark.parametrize("value", ["15", "60", "120", "240"])
def test_session_parameter_accepts_the_supported_operational_range(value: str) -> None:
    from app.modules.parameters.router import _PUBLIC_PARAMETER_KEYS, _validated_parameter_value

    assert "AUTH_SESSION_MINUTES" in _PUBLIC_PARAMETER_KEYS
    assert _validated_parameter_value("AUTH_SESSION_MINUTES", value) == value


@pytest.mark.parametrize("value", ["14", "241", "60.5"])
def test_session_parameter_rejects_values_outside_the_supported_range(value: str) -> None:
    from app.modules.parameters.router import _validated_parameter_value

    with pytest.raises(HTTPException) as error:
        _validated_parameter_value("AUTH_SESSION_MINUTES", value)
    assert error.value.status_code == 422


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
