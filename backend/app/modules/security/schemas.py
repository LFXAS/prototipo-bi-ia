from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

EmailAddress = str


class LoginRequest(BaseModel):
    email: EmailAddress = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None = None
    is_active: bool


class PermissionCreate(BaseModel):
    code: str = Field(pattern=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$", max_length=120)
    name: str = Field(min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=1000)


class PermissionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None = None
    is_active: bool
    permissions: list[PermissionRead] = []


class RoleCreate(BaseModel):
    code: str = Field(pattern=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$", max_length=80)
    name: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    permission_ids: list[int] = []


class RolePermissionsUpdate(BaseModel):
    permission_ids: list[int]


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


class UserRead(BaseModel):
    id: int
    email: EmailAddress
    full_name: str
    is_active: bool
    roles: list[RoleRead] = []


class UserCreate(BaseModel):
    email: EmailAddress = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str = Field(min_length=3, max_length=160)
    password: str = Field(min_length=12, max_length=128)
    role_ids: list[int] = []


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=160)
    password: str | None = Field(default=None, min_length=12, max_length=128)
    is_active: bool | None = None
    role_ids: list[int] | None = None


class MenuRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    label: str
    path: str
    position: int
    module_code: str
    module_label: str
    is_active: bool
    permissions: list[PermissionRead] = []


class MenuCreate(BaseModel):
    code: str = Field(pattern=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$", max_length=100)
    label: str = Field(min_length=2, max_length=120)
    path: str = Field(pattern=r"^/.*", max_length=160)
    position: int = Field(default=0, ge=0)
    module_code: str = Field(
        default="general", pattern=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$", max_length=80
    )
    module_label: str = Field(default="General", min_length=2, max_length=120)
    permission_ids: list[int] = []


class MenuUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=2, max_length=120)
    path: str | None = Field(default=None, pattern=r"^/.*", max_length=160)
    position: int | None = Field(default=None, ge=0)
    module_code: str | None = Field(
        default=None, pattern=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$", max_length=80
    )
    module_label: str | None = Field(default=None, min_length=2, max_length=120)
    is_active: bool | None = None
    permission_ids: list[int] | None = None


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: int | None
    action: str
    resource_type: str
    resource_id: str | None
    detail: dict[str, object]
    created_at: datetime


class SessionRead(BaseModel):
    user: UserRead
    permissions: list[str]
    menus: list[MenuRead]
