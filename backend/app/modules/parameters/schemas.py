from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ProviderKind = Literal["gemini", "qwen-cloud", "ollama-local"]


class ParameterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: str
    description: str | None = None
    is_active: bool


class ParameterUpsert(BaseModel):
    key: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,99}$")
    value: str = Field(min_length=1, max_length=4000)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = True


class LlmConfigurationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    provider_kind: ProviderKind
    base_url: str
    model_id: str
    credential_reference: str
    is_active: bool
    last_test_status: str | None = None
    last_test_message: str | None = None
    last_tested_at: datetime | None = None


class LlmConfigurationCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    provider_kind: ProviderKind
    base_url: str = Field(min_length=10, max_length=300)
    model_id: str = Field(min_length=2, max_length=160)
    is_active: bool = False

    @model_validator(mode="after")
    def validate_provider_endpoint(self) -> LlmConfigurationCreate:
        expected = {
            "gemini": ("https://generativelanguage.googleapis.com",),
            "qwen-cloud": ("https://dashscope.aliyuncs.com", "https://dashscope-intl.aliyuncs.com"),
            "ollama-local": ("http://ollama:11434",),
        }
        if not self.base_url.rstrip("/").startswith(expected[self.provider_kind]):
            raise ValueError(
                "La URL no corresponde al proveedor seleccionado o no es una URL interna permitida."
            )
        return self


class LlmConfigurationUpdate(LlmConfigurationCreate):
    pass


class ConnectionTestResponse(BaseModel):
    ok: bool
    message: str
