from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.modules.security.models import AuditEvent, Menu, Permission, Role, User
from app.modules.security.schemas import (
    AuditEventRead,
    LoginRequest,
    MenuCreate,
    MenuRead,
    PermissionCreate,
    PermissionRead,
    RoleCreate,
    RolePermissionsUpdate,
    RoleRead,
    SessionRead,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.modules.security.service import (
    add_audit_event,
    create_access_token,
    current_user,
    hash_password,
    require_permission,
    user_permission_codes,
    verify_password,
)

router = APIRouter(tags=["security"])


def _user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
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


@router.get("/users", response_model=list[UserRead])
async def list_users(
    _: User = Depends(require_permission("security.users.read")),
    session: AsyncSession = Depends(get_session),
) -> list[UserRead]:
    users = (
        await session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .order_by(User.id)
        )
    ).scalars()
    return [_user_read(user) for user in users]


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
        list((await session.execute(select(Role).where(Role.id.in_(payload.role_ids)))).scalars())
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
    await session.commit()
    await session.refresh(user, ["roles"])
    return _user_read(user)


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
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role_ids is not None:
        roles = list(
            (await session.execute(select(Role).where(Role.id.in_(payload.role_ids)))).scalars()
        )
        if len(roles) != len(set(payload.role_ids)):
            raise HTTPException(status_code=422, detail="Uno o más roles no existen.")
        user.roles = roles
    await add_audit_event(session, actor.id, "security.user.update", "user", str(user.id))
    await session.commit()
    return _user_read(user)


@router.get("/roles", response_model=list[RoleRead])
async def list_roles(
    _: User = Depends(require_permission("security.roles.read")),
    session: AsyncSession = Depends(get_session),
) -> list[RoleRead]:
    items = (
        await session.execute(
            select(Role).options(selectinload(Role.permissions)).order_by(Role.id)
        )
    ).scalars()
    return [RoleRead.model_validate(item) for item in items]


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    actor: User = Depends(require_permission("security.roles.write")),
    session: AsyncSession = Depends(get_session),
) -> RoleRead:
    if (await session.execute(select(Role).where(Role.code == payload.code))).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El código del rol ya existe.")
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
        code=payload.code,
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
    role.permissions = permissions
    await add_audit_event(
        session, actor.id, "security.role.permissions.update", "role", str(role.id)
    )
    await session.commit()
    return RoleRead.model_validate(role)


@router.get("/permissions", response_model=list[PermissionRead])
async def list_permissions(
    _: User = Depends(require_permission("security.permissions.read")),
    session: AsyncSession = Depends(get_session),
) -> list[PermissionRead]:
    items = (await session.execute(select(Permission).order_by(Permission.code))).scalars()
    return [PermissionRead.model_validate(item) for item in items]


@router.post("/permissions", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
async def create_permission(
    payload: PermissionCreate,
    actor: User = Depends(require_permission("security.permissions.write")),
    session: AsyncSession = Depends(get_session),
) -> Permission:
    if (
        await session.execute(select(Permission).where(Permission.code == payload.code))
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El código del permiso ya existe.")
    permission = Permission(**payload.model_dump())
    session.add(permission)
    await session.flush()
    await add_audit_event(
        session, actor.id, "security.permission.create", "permission", str(permission.id)
    )
    await session.commit()
    return permission


@router.get("/menus", response_model=list[MenuRead])
async def list_menus(
    _: User = Depends(require_permission("security.menus.read")),
    session: AsyncSession = Depends(get_session),
) -> list[MenuRead]:
    items = (
        await session.execute(
            select(Menu).options(selectinload(Menu.permissions)).order_by(Menu.position)
        )
    ).scalars()
    return [MenuRead.model_validate(item) for item in items]


@router.post("/menus", response_model=MenuRead, status_code=status.HTTP_201_CREATED)
async def create_menu(
    payload: MenuCreate,
    actor: User = Depends(require_permission("security.menus.write")),
    session: AsyncSession = Depends(get_session),
) -> Menu:
    if (
        await session.execute(
            select(Menu).where((Menu.code == payload.code) | (Menu.path == payload.path))
        )
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El código o la ruta del menú ya existe.")
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
    menu = Menu(**payload.model_dump(exclude={"permission_ids"}), permissions=permissions)
    session.add(menu)
    await session.flush()
    await add_audit_event(session, actor.id, "security.menu.create", "menu", str(menu.id))
    await session.commit()
    await session.refresh(menu, ["permissions"])
    return menu


@router.get("/audit-events", response_model=list[AuditEventRead])
async def list_audit_events(
    _: User = Depends(require_permission("audit.read")),
    session: AsyncSession = Depends(get_session),
) -> list[AuditEvent]:
    return list(
        (
            await session.execute(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(200))
        ).scalars()
    )
