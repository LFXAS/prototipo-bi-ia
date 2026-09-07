from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, Header, HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import get_session
from app.modules.security.models import AuditEvent, Menu, Permission, Role, User

password_hash = PasswordHash.recommended()

DEFAULT_PERMISSIONS: tuple[tuple[str, str, str], ...] = (
    ("security.users.read", "Consultar usuarios", "Permite consultar usuarios."),
    ("security.users.write", "Administrar usuarios", "Permite crear y modificar usuarios."),
    ("security.roles.read", "Consultar roles", "Permite consultar roles."),
    ("security.roles.write", "Administrar roles", "Permite crear roles y asignar permisos."),
    ("security.permissions.read", "Consultar permisos", "Permite consultar permisos."),
    ("security.permissions.write", "Administrar permisos", "Permite crear permisos."),
    ("security.menus.read", "Consultar menús", "Permite consultar la navegación."),
    ("security.menus.write", "Administrar menús", "Permite crear y parametrizar menús."),
    ("parameters.read", "Consultar parámetros", "Permite consultar parámetros operativos."),
    ("parameters.write", "Administrar parámetros", "Permite crear y modificar parámetros."),
    ("parameters.llm.read", "Consultar configuración LLM", "Permite consultar proveedores LLM."),
    (
        "parameters.llm.write",
        "Administrar configuración LLM",
        "Permite parametrizar proveedores LLM.",
    ),
    (
        "parameters.connections.test",
        "Probar conexiones",
        "Permite probar conexiones externas de solo lectura.",
    ),
    ("audit.read", "Consultar auditoría", "Permite consultar eventos de auditoría."),
)

DEFAULT_MENUS: tuple[tuple[str, str, str, int, str, str, tuple[str, ...]], ...] = (
    ("home", "Inicio", "/", 0, "home", "Principal", ()),
    ("users", "Usuarios", "/usuarios", 10, "security", "Seguridad", ("security.users.read",)),
    ("roles", "Roles", "/roles", 20, "security", "Seguridad", ("security.roles.read",)),
    (
        "permissions",
        "Permisos",
        "/permisos",
        30,
        "security",
        "Seguridad",
        ("security.permissions.read",),
    ),
    ("menus", "Menús", "/menus", 40, "security", "Seguridad", ("security.menus.read",)),
    (
        "parameters",
        "Parámetros",
        "/parametros",
        50,
        "parameters",
        "Parámetros generales",
        ("parameters.read",),
    ),
    (
        "llm",
        "Configuración LLM",
        "/llm",
        60,
        "parameters",
        "Parámetros generales",
        ("parameters.llm.read",),
    ),
    ("audit", "Auditoría", "/auditoria", 70, "security", "Seguridad", ("audit.read",)),
)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_password: str) -> bool:
    return password_hash.verify(password, encoded_password)


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at},
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


async def load_user(session: AsyncSession, user_id: int) -> User | None:
    statement = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    return (await session.execute(statement)).scalar_one_or_none()


async def current_user(
    session: AsyncSession = Depends(get_session),
    authorization: str | None = Header(default=None),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión no autenticada."
        )
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(
            token, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_algorithm]
        )
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o vencido."
        ) from exc
    user = await load_user(session, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo o inexistente."
        )
    return user


def user_permission_codes(user: User) -> set[str]:
    return {
        permission.code
        for role in user.roles
        if role.is_active
        for permission in role.permissions
        if permission.is_active
    }


def require_permission(code: str) -> Callable[[User], Awaitable[User]]:
    async def dependency(user: User = Depends(current_user)) -> User:
        if code not in user_permission_codes(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permiso para esta acción."
            )
        return user

    return dependency


async def add_audit_event(
    session: AsyncSession,
    actor_user_id: int | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    detail: dict[str, object] | None = None,
) -> None:
    session.add(
        AuditEvent(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail or {},
        )
    )


async def seed_security(session: AsyncSession) -> None:
    """Creates only the minimum safe bootstrap configuration on an empty installation."""
    existing_permissions = {
        item.code for item in (await session.execute(select(Permission))).scalars()
    }
    for code, name, description in DEFAULT_PERMISSIONS:
        if code not in existing_permissions:
            session.add(Permission(code=code, name=name, description=description))
    await session.flush()

    permissions = {
        item.code: item for item in (await session.execute(select(Permission))).scalars()
    }
    administrator = (
        await session.execute(
            select(Role).where(Role.code == "administrator").options(selectinload(Role.permissions))
        )
    ).scalar_one_or_none()
    if administrator is None:
        administrator = Role(
            code="administrator", name="Administrador", description="Rol inicial de administración."
        )
        session.add(administrator)
    administrator.permissions = list(permissions.values())
    await session.flush()

    existing_menus = {item.code for item in (await session.execute(select(Menu))).scalars()}
    for code, label, path, position, module_code, module_label, permission_codes in DEFAULT_MENUS:
        if code not in existing_menus:
            session.add(
                Menu(
                    code=code,
                    label=label,
                    path=path,
                    position=position,
                    module_code=module_code,
                    module_label=module_label,
                    permissions=[permissions[item] for item in permission_codes],
                )
            )
    admin = (
        await session.execute(
            select(User)
            .where(User.email == settings.bootstrap_admin_email)
            .options(selectinload(User.roles))
        )
    ).scalar_one_or_none()
    if admin is None:
        session.add(
            User(
                email=settings.bootstrap_admin_email,
                full_name="Administrador inicial",
                password_hash=hash_password(settings.bootstrap_admin_password.get_secret_value()),
                roles=[administrator],
            )
        )
    await session.commit()
