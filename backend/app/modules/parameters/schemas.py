from __future__ import annotations

from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

ProviderKind = Literal["gemini", "qwen-cloud", "ollama-local"]
ReasoningLevel = Literal["automatic", "minimal", "low", "medium", "high"]


class ParameterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    module_code: str
    value_type: str
    value: str
    default_value: str
    min_value: int | None = None
    max_value: int | None = None
    description: str | None = None
    is_active: bool


class ParameterUpdate(BaseModel):
    value: str = Field(min_length=1, max_length=10000)


class LlmConfigurationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    provider_kind: ProviderKind
    base_url: str
    model_id: str
    reasoning_level: ReasoningLevel
    credential_configured: bool
    is_active: bool
    last_test_status: str | None = None
    last_test_message: str | None = None
    last_tested_at: datetime | None = None


class LlmConfigurationCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    provider_kind: ProviderKind
    base_url: str = Field(min_length=10, max_length=300)
    model_id: str = Field(min_length=2, max_length=160)
    reasoning_level: ReasoningLevel = "minimal"
    is_active: bool = False

    @model_validator(mode="after")
    def validate_provider_endpoint(self) -> LlmConfigurationCreate:
        expected: dict[ProviderKind, set[tuple[str, str, int | None]]] = {
            "gemini": {("https", "generativelanguage.googleapis.com", None)},
            "qwen-cloud": {
                ("https", "dashscope.aliyuncs.com", None),
                ("https", "dashscope-intl.aliyuncs.com", None),
            },
            "ollama-local": {("http", "ollama", 11434)},
        }
        parsed = urlsplit(self.base_url.rstrip("/"))
        endpoint = (parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port)
        if (
            endpoint not in expected[self.provider_kind]
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "La URL no corresponde al proveedor seleccionado o no es una URL interna permitida."
            )
        return self


class LlmConfigurationUpdate(LlmConfigurationCreate):
    pass


class LlmCredentialWrite(BaseModel):
    api_key: str = Field(min_length=8, max_length=4096)


class LlmCredentialStatus(BaseModel):
    credential_configured: bool
    message: str


class ConnectionTestResponse(BaseModel):
    ok: bool
    message: str


class DataConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    connector_kind: Literal["sqlserver"]
    host: str
    port: int
    database_name: str
    username: str
    encrypt: bool
    trust_server_certificate: bool
    is_active: bool
    last_test_status: str | None = None
    last_test_message: str | None = None
    last_tested_at: datetime | None = None


class DataConnectionCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    connector_kind: Literal["sqlserver"] = "sqlserver"
    host: str = Field(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9._-]+$")
    port: int = Field(default=1433, ge=1, le=65535)
    database_name: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.$-]+$")
    username: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_@.$\\-]+$")
    password: str = Field(min_length=8, max_length=4096)
    encrypt: bool = True
    trust_server_certificate: bool = True


class DataConnectionUpdate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    connector_kind: Literal["sqlserver"] = "sqlserver"
    host: str = Field(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9._-]+$")
    port: int = Field(default=1433, ge=1, le=65535)
    database_name: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.$-]+$")
    username: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_@.$\\-]+$")
    password: str | None = Field(default=None, min_length=8, max_length=4096)
    encrypt: bool = True
    trust_server_certificate: bool = True
