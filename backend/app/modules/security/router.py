from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.pagination import PageRead
from app.db.session import get_session
from app.modules.security.models import (
    AuditEvent,
    Menu,
    Permission,
    Role,
    User,
    menu_permissions,
    role_permissions,
    user_roles,
)
from app.modules.security.schemas import (
    AuditEventRead,
    LoginRequest,
    MenuCreate,
    MenuRead,
    MenuUpdate,
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
    RoleCreate,
    RolePermissionsUpdate,
    RoleRead,
    RoleUpdate,
    SessionRead,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.modules.security.service import (
    RECOVERY_PERMISSION_CODES,
    add_audit_event,
    create_access_token,
    current_user,
    generated_role_code,
    hash_password,
    require_permission,
    user_permission_codes,
    verify_password,
)

router = APIRouter(tags=["security"])


async def _association_count(session: AsyncSession, table: Any, column: Any, value: int) -> int:
    query = select(func.count()).select_from(table).where(column == value)
    return (await session.scalar(query)) or 0


def _delete_blocked(resource: str, dependencies: list[tuple[str, int]]) -> None:
    pending = [f"{count} {label}" for label, count in dependencies if count]
    if pending:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar {resource}: primero resuelva {' y '.join(pending)}.",
        )


def _user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_system_protected=user.is_system_protected,
        roles=[RoleRead.model_validate(role) for role in user.roles],
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    user = (
        await session.execute(select(User).where(User.email == str(payload.email).lower()))
    ).scalar_one_or_none()
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos."
        )
    await add_audit_event(session, user.id, "auth.login", "session", str(user.id))
    await session.commit()
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/auth/me", response_model=SessionRead)
async def get_current_session(
    user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> SessionRead:
    menus = (
        await session.execute(
            select(Menu)
            .where(Menu.is_active.is_(True))
            .options(selectinload(Menu.permissions))
            .order_by(Menu.position)
        )
    ).scalars()
    permission_codes = user_permission_codes(user)
    visible_menus = [
        MenuRead.model_validate(menu)
        for menu in menus
        if not menu.permissions
        or any(permission.code in permission_codes for permission in menu.permissions)
    ]
    return SessionRead(
        user=_user_read(user), permissions=sorted(permission_codes), menus=visible_menus
    )


@router.get("/users", response_model=PageRead[UserRead])
async def list_users(
    _: User = Depends(require_permission("security.users.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[UserRead]:
    total = (await session.scalar(select(func.count()).select_from(User))) or 0
    users = (
        await session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .order_by(User.id)
            .limit(limit)
            .offset(offset)
        )
    ).scalars()
    return PageRead(
        items=[_user_read(user) for user in users], total=total, limit=limit, offset=offset
    )


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    actor: User = Depends(require_permission("security.users.write")),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    if (
        await session.execute(select(User).where(User.email == str(payload.email).lower()))
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El correo ya está registrado.")
    roles = (
        list(
            (
                await session.execute(
                    select(Role).where(Role.id.in_(payload.role_ids), Role.is_active.is_(True))
                )
            ).scalars()
        )
        if payload.role_ids
        else []
    )
    if len(roles) != len(set(payload.role_ids)):
        raise HTTPException(status_code=422, detail="Uno o más roles no existen.")
    user = User(
        email=str(payload.email).lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        roles=roles,
    )
    session.add(user)
    await session.flush()
    await add_audit_event(
        session, actor.id, "security.user.create", "user", str(user.id), {"email": user.email}
    )
    user_id = user.id
    await session.commit()
    saved_user = (
        await session.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
    ).scalar_one()
    return _user_read(saved_user)


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    actor: User = Depends(require_permission("security.users.write")),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    user = (
        await session.execute(
            select(User).where(User.id == user_id).options(selectinload(User.roles))
        )
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if user.is_system_protected and payload.is_active is False:
        await add_audit_event(
            session, actor.id, "security.user.protected_change_rejected", "user", str(user.id)
        )
        await session.commit()
        raise HTTPException(
            status_code=422,
            detail="La cuenta administrativa protegida no puede desactivarse.",
        )
    if user.is_system_protected and payload.role_ids is not None:
        await add_audit_event(
            session, actor.id, "security.user.protected_change_rejected", "user", str(user.id)
        )
        await session.commit()
        raise HTTPException(
            status_code=422,
            detail=(
                "Los roles de la cuenta administrativa protegida no se modifican "
                "desde esta pantalla."
            ),
        )
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role_ids is not None:
        roles = list(
            (
                await session.execute(
                    select(Role).where(Role.id.in_(payload.role_ids), Role.is_active.is_(True))
                )
            ).scalars()
        )
        if len(roles) != len(set(payload.role_ids)):
            raise HTTPException(status_code=422, detail="Uno o más roles no existen.")
        user.roles = roles
    user_id = user.id
    await add_audit_event(session, actor.id, "security.user.update", "user", str(user_id))
    await session.commit()
    saved_user = (
        await session.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
    ).scalar_one()
    return _user_read(saved_user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    actor: User = Depends(require_permission("security.users.write")),
    session: AsyncSession = Depends(get_session),
) -> Response:
    user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if user.is_system_protected:
        raise HTTPException(status_code=422, detail="La cuenta protegida no puede eliminarse.")
    _delete_blocked(
        "el usuario",
        [
            (
                "asignaciones de roles",
                await _association_count(session, user_roles, user_roles.c.user_id, user_id),
            ),
        ],
    )
    await add_audit_event(session, actor.id, "security.user.delete", "user", str(user_id))
    await session.delete(user)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/roles", response_model=PageRead[RoleRead])
async def list_roles(
    _: User = Depends(require_permission("security.roles.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[RoleRead]:
    total = (await session.scalar(select(func.count()).select_from(Role))) or 0
    items = (
        await session.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .order_by(Role.id)
            .limit(limit)
            .offset(offset)
        )
    ).scalars()
    return PageRead(
        items=[RoleRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    actor: User = Depends(require_permission("security.roles.write")),
    session: AsyncSession = Depends(get_session),
) -> RoleRead:
    base_code = generated_role_code(payload.name)
    code = base_code
    suffix = 2
    while (await session.execute(select(Role).where(Role.code == code))).scalar_one_or_none():
        code = f"{base_code[: max(1, 76 - len(str(suffix)))]}-{suffix}"
        suffix += 1
    permissions = (
        list(
            (
                await session.execute(
                    select(Permission).where(Permission.id.in_(payload.permission_ids))
                )
            ).scalars()
        )
        if payload.permission_ids
        else []
    )
    if len(permissions) != len(set(payload.permission_ids)):
        raise HTTPException(status_code=422, detail="Uno o más permisos no existen.")
    role = Role(
        code=code,
        name=payload.name,
        description=payload.description,
        permissions=permissions,
    )
    session.add(role)
    await session.flush()
    await add_audit_event(session, actor.id, "security.role.create", "role", str(role.id))
    await session.commit()
    await session.refresh(role, ["permissions"])
    return RoleRead.model_validate(role)


@router.put("/roles/{role_id}/permissions", response_model=RoleRead)
async def update_role_permissions(
    role_id: int,
    payload: RolePermissionsUpdate,
    actor: User = Depends(require_permission("security.roles.write")),
    session: AsyncSession = Depends(get_session),
) -> RoleRead:
    role = (
        await session.execute(
            select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        )
    ).scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado.")
    permissions = list(
        (
            await session.execute(
                select(Permission).where(Permission.id.in_(payload.permission_ids))
            )
        ).scalars()
    )
    if len(permissions) != len(set(payload.permission_ids)):
        raise HTTPException(status_code=422, detail="Uno o más permisos no existen.")
    if role.is_system_protected and not RECOVERY_PERMISSION_CODES.issubset(
        {permission.code for permission in permissions if permission.is_active}
    ):
        await add_audit_event(
            session, actor.id, "security.role.protected_change_rejected", "role", str(role.id)
        )
        await session.commit()
        raise HTTPException(
            status_code=422,
            detail="El rol administrativo protegido debe conservar los permisos de recuperación.",
        )
    role.permissions = permissions
    await add_audit_event(
        session, actor.id, "security.role.permissions.update", "role", str(role.id)
    )
    await session.commit()
    return RoleRead.model_validate(role)


@router.patch("/roles/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: int,
    payload: RoleUpdate,
    actor: User = Depends(require_permission("security.roles.write")),
    session: AsyncSession = Depends(get_session),
) -> RoleRead:
    role = (
        await session.execute(
            select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        )
    ).scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado.")
    if payload.is_active is False and role.is_system_protected:
        raise HTTPException(
            status_code=422,
            detail="El rol administrativo protegido no puede desactivarse.",
        )
    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    if payload.is_active is not None:
        role.is_active = payload.is_active
    await add_audit_event(session, actor.id, "security.role.update", "role", str(role.id))
    await session.commit()
    return RoleRead.model_validate(role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    actor: User = Depends(require_permission("security.roles.write")),
    session: AsyncSession = Depends(get_session),
) -> Response:
    role = (await session.execute(select(Role).where(Role.id == role_id))).scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado.")
    if role.is_system_protected:
        raise HTTPException(status_code=422, detail="El rol protegido no puede eliminarse.")
    _delete_blocked(
        "el rol",
        [
            (
                "asignaciones a usuarios",
                await _association_count(session, user_roles, user_roles.c.role_id, role_id),
            ),
            (
                "asignaciones de permisos",
                await _association_count(
                    session, role_permissions, role_permissions.c.role_id, role_id
                ),
            ),
        ],
    )
    await add_audit_event(session, actor.id, "security.role.delete", "role", str(role_id))
    await session.delete(role)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/permissions", response_model=PageRead[PermissionRead])
async def list_permissions(
    _: User = Depends(require_permission("security.permissions.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[PermissionRead]:
    total = (await session.scalar(select(func.count()).select_from(Permission))) or 0
    items = (
        await session.execute(
            select(Permission).order_by(Permission.code).limit(limit).offset(offset)
        )
    ).scalars()
    return PageRead(
        items=[PermissionRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/permissions", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
async def create_permission(
    payload: PermissionCreate,
    actor: User = Depends(require_permission("security.permissions.write")),
    session: AsyncSession = Depends(get_session),
) -> Permission:
    await add_audit_event(
        session, actor.id, "security.permission.create_rejected", "permission", payload.code
    )
    await session.commit()
    raise HTTPException(
        status_code=422,
        detail=(
            "Los permisos técnicos se registran al aprobar e implementar un módulo; "
            "no se crean manualmente."
        ),
    )


@router.patch("/permissions/{permission_id}", response_model=PermissionRead)
async def update_permission(
    permission_id: int,
    payload: PermissionUpdate,
    actor: User = Depends(require_permission("security.permissions.write")),
    session: AsyncSession = Depends(get_session),
) -> Permission:
    permission = (
        await session.execute(select(Permission).where(Permission.id == permission_id))
    ).scalar_one_or_none()
    if permission is None:
        raise HTTPException(status_code=404, detail="Permiso no encontrado.")
    if permission.is_system_protected and payload.is_active is False:
        await add_audit_event(
            session,
            actor.id,
            "security.permission.protected_change_rejected",
            "permission",
            str(permission.id),
        )
        await session.commit()
        raise HTTPException(
            status_code=422,
            detail="El permiso de sistema protegido no puede desactivarse.",
        )
    if payload.name is not None:
        permission.name = payload.name
    if payload.description is not None:
        permission.description = payload.description
    if payload.is_active is not None:
        permission.is_active = payload.is_active
    await add_audit_event(
        session, actor.id, "security.permission.update", "permission", str(permission.id)
    )
    await session.commit()
    return permission


@router.get("/menus", response_model=PageRead[MenuRead])
async def list_menus(
    _: User = Depends(require_permission("security.menus.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[MenuRead]:
    total = (await session.scalar(select(func.count()).select_from(Menu))) or 0
    items = (
        await session.execute(
            select(Menu)
            .options(selectinload(Menu.permissions))
            .order_by(Menu.position)
            .limit(limit)
            .offset(offset)
        )
    ).scalars()
    return PageRead(
        items=[MenuRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/menus", response_model=MenuRead, status_code=status.HTTP_201_CREATED)
async def create_menu(
    payload: MenuCreate,
    actor: User = Depends(require_permission("security.menus.write")),
    session: AsyncSession = Depends(get_session),
) -> Menu:
    await add_audit_event(session, actor.id, "security.menu.create_rejected", "menu", payload.code)
    await session.commit()
    raise HTTPException(
        status_code=422,
        detail=(
            "Los menús se registran al aprobar e implementar una pantalla; no se crean manualmente."
        ),
    )


@router.patch("/menus/{menu_id}", response_model=MenuRead)
async def update_menu(
    menu_id: int,
    payload: MenuUpdate,
    actor: User = Depends(require_permission("security.menus.write")),
    session: AsyncSession = Depends(get_session),
) -> Menu:
    menu = (
        await session.execute(
            select(Menu).where(Menu.id == menu_id).options(selectinload(Menu.permissions))
        )
    ).scalar_one_or_none()
    if menu is None:
        raise HTTPException(status_code=404, detail="Menú no encontrado.")
    if menu.is_system_protected and payload.is_active is False:
        await add_audit_event(
            session, actor.id, "security.menu.protected_change_rejected", "menu", str(menu.id)
        )
        await session.commit()
        raise HTTPException(
            status_code=422,
            detail="El menú de sistema protegido no puede desactivarse.",
        )
    if payload.path is not None and payload.path != menu.path:
        duplicate = (
            await session.execute(select(Menu).where(Menu.path == payload.path))
        ).scalar_one_or_none()
        if duplicate is not None:
            raise HTTPException(status_code=409, detail="La ruta del menú ya existe.")
        menu.path = payload.path
    if payload.label is not None:
        menu.label = payload.label
    if payload.position is not None:
        menu.position = payload.position
    if payload.is_active is not None:
        menu.is_active = payload.is_active
    if payload.permission_ids is not None:
        permissions = list(
            (
                await session.execute(
                    select(Permission).where(Permission.id.in_(payload.permission_ids))
                )
            ).scalars()
        )
        if len(permissions) != len(set(payload.permission_ids)):
            raise HTTPException(status_code=422, detail="Uno o más permisos no existen.")
        menu.permissions = permissions
    await add_audit_event(session, actor.id, "security.menu.update", "menu", str(menu.id))
    await session.commit()
    return menu


@router.delete("/menus/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu(
    menu_id: int,
    actor: User = Depends(require_permission("security.menus.write")),
    session: AsyncSession = Depends(get_session),
) -> Response:
    menu = (await session.execute(select(Menu).where(Menu.id == menu_id))).scalar_one_or_none()
    if menu is None:
        raise HTTPException(status_code=404, detail="Menú no encontrado.")
    if menu.is_system_protected:
        raise HTTPException(status_code=422, detail="El menú protegido no puede eliminarse.")
    _delete_blocked(
        "el menú",
        [
            (
                "asignaciones de permisos",
                await _association_count(
                    session, menu_permissions, menu_permissions.c.menu_id, menu_id
                ),
            )
        ],
    )
    await add_audit_event(session, actor.id, "security.menu.delete", "menu", str(menu_id))
    await session.delete(menu)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/audit-events", response_model=PageRead[AuditEventRead])
async def list_audit_events(
    _: User = Depends(require_permission("audit.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[AuditEventRead]:
    total = (await session.scalar(select(func.count()).select_from(AuditEvent))) or 0
    items = (
        await session.execute(
            select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit).offset(offset)
        )
    ).scalars()
    return PageRead(items=list(items), total=total, limit=limit, offset=offset)
