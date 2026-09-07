from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pyodbc  # type: ignore[import-not-found]
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.pagination import PageRead
from app.db.session import get_session
from app.modules.parameters.models import LlmConfiguration, Parameter
from app.modules.parameters.providers import test_provider
from app.modules.parameters.schemas import (
    ConnectionTestResponse,
    LlmConfigurationCreate,
    LlmConfigurationRead,
    LlmConfigurationUpdate,
    ParameterRead,
    ParameterUpsert,
)
from app.modules.security.models import User
from app.modules.security.service import add_audit_event, require_permission

router = APIRouter(tags=["parameters"])

_CREDENTIAL_REFERENCES = {
    "gemini": "GEMINI_API_KEY",
    "qwen-cloud": "DASHSCOPE_API_KEY",
    "ollama-local": "none",
}


@router.get("/parameters", response_model=PageRead[ParameterRead])
async def list_parameters(
    _: User = Depends(require_permission("parameters.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[ParameterRead]:
    total = (await session.scalar(select(func.count()).select_from(Parameter))) or 0
    items = (
        await session.execute(select(Parameter).order_by(Parameter.key).limit(limit).offset(offset))
    ).scalars()
    return PageRead(items=list(items), total=total, limit=limit, offset=offset)


@router.put("/parameters/{key}", response_model=ParameterRead)
async def upsert_parameter(
    key: str,
    payload: ParameterUpsert,
    actor: User = Depends(require_permission("parameters.write")),
    session: AsyncSession = Depends(get_session),
) -> Parameter:
    if key != payload.key:
        raise HTTPException(
            status_code=422, detail="La clave de la ruta y del contenido deben coincidir."
        )
    parameter = (
        await session.execute(select(Parameter).where(Parameter.key == key))
    ).scalar_one_or_none()
    action = "parameters.create" if parameter is None else "parameters.update"
    if parameter is None:
        parameter = Parameter(**payload.model_dump())
        session.add(parameter)
    else:
        for field, value in payload.model_dump().items():
            setattr(parameter, field, value)
    await session.flush()
    await add_audit_event(
        session, actor.id, action, "parameter", str(parameter.id), {"key": parameter.key}
    )
    await session.commit()
    return parameter


@router.get("/llm-configurations", response_model=PageRead[LlmConfigurationRead])
async def list_llm_configurations(
    _: User = Depends(require_permission("parameters.llm.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[LlmConfigurationRead]:
    total = (await session.scalar(select(func.count()).select_from(LlmConfiguration))) or 0
    items = (
        await session.execute(
            select(LlmConfiguration).order_by(LlmConfiguration.id).limit(limit).offset(offset)
        )
    ).scalars()
    return PageRead(items=list(items), total=total, limit=limit, offset=offset)


async def _apply_llm_configuration(
    configuration: LlmConfiguration, payload: LlmConfigurationCreate, session: AsyncSession
) -> None:
    if payload.is_active:
        active_items = (
            await session.execute(
                select(LlmConfiguration).where(LlmConfiguration.is_active.is_(True))
            )
        ).scalars()
        for active_item in active_items:
            active_item.is_active = False
    configuration.name = payload.name
    configuration.provider_kind = payload.provider_kind
    configuration.base_url = payload.base_url.rstrip("/")
    configuration.model_id = payload.model_id
    configuration.credential_reference = _CREDENTIAL_REFERENCES[payload.provider_kind]
    configuration.is_active = payload.is_active


@router.post(
    "/llm-configurations", response_model=LlmConfigurationRead, status_code=status.HTTP_201_CREATED
)
async def create_llm_configuration(
    payload: LlmConfigurationCreate,
    actor: User = Depends(require_permission("parameters.llm.write")),
    session: AsyncSession = Depends(get_session),
) -> LlmConfiguration:
    configuration = LlmConfiguration(
        name=payload.name,
        provider_kind=payload.provider_kind,
        base_url=payload.base_url.rstrip("/"),
        model_id=payload.model_id,
        credential_reference=_CREDENTIAL_REFERENCES[payload.provider_kind],
        is_active=False,
    )
    session.add(configuration)
    await _apply_llm_configuration(configuration, payload, session)
    await session.flush()
    await add_audit_event(
        session, actor.id, "parameters.llm.create", "llm_configuration", str(configuration.id)
    )
    await session.commit()
    return configuration


@router.put("/llm-configurations/{configuration_id}", response_model=LlmConfigurationRead)
async def update_llm_configuration(
    configuration_id: int,
    payload: LlmConfigurationUpdate,
    actor: User = Depends(require_permission("parameters.llm.write")),
    session: AsyncSession = Depends(get_session),
) -> LlmConfiguration:
    configuration = (
        await session.execute(
            select(LlmConfiguration).where(LlmConfiguration.id == configuration_id)
        )
    ).scalar_one_or_none()
    if configuration is None:
        raise HTTPException(status_code=404, detail="Configuración LLM no encontrada.")
    await _apply_llm_configuration(configuration, payload, session)
    await add_audit_event(
        session, actor.id, "parameters.llm.update", "llm_configuration", str(configuration.id)
    )
    await session.commit()
    return configuration


@router.post("/llm-configurations/{configuration_id}/test", response_model=ConnectionTestResponse)
async def verify_llm_configuration(
    configuration_id: int,
    actor: User = Depends(require_permission("parameters.llm.write")),
    session: AsyncSession = Depends(get_session),
) -> ConnectionTestResponse:
    configuration = (
        await session.execute(
            select(LlmConfiguration).where(LlmConfiguration.id == configuration_id)
        )
    ).scalar_one_or_none()
    if configuration is None:
        raise HTTPException(status_code=404, detail="Configuración LLM no encontrada.")
    result = await test_provider(configuration)
    configuration.last_test_status = "ok" if result.ok else "error"
    configuration.last_test_message = result.message
    configuration.last_tested_at = datetime.now(UTC)
    await add_audit_event(
        session,
        actor.id,
        "parameters.llm.test",
        "llm_configuration",
        str(configuration.id),
        {"result": configuration.last_test_status},
    )
    await session.commit()
    return ConnectionTestResponse(ok=result.ok, message=result.message)


def _test_adventureworks_read_only() -> None:
    connection = pyodbc.connect(settings.adventureworks_odbc_connection_string, timeout=8)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT TOP (1) name FROM sys.tables")
        cursor.fetchone()
    finally:
        connection.close()


@router.post("/connections/adventureworks/test", response_model=ConnectionTestResponse)
async def verify_adventureworks_connection(
    actor: User = Depends(require_permission("parameters.connections.test")),
    session: AsyncSession = Depends(get_session),
) -> ConnectionTestResponse:
    try:
        await asyncio.to_thread(_test_adventureworks_read_only)
    except pyodbc.Error:
        result = ConnectionTestResponse(
            ok=False, message="No fue posible validar la conexión externa de solo lectura."
        )
    else:
        result = ConnectionTestResponse(
            ok=True, message="Conexión externa de solo lectura validada."
        )
    await add_audit_event(
        session,
        actor.id,
        "parameters.connection.test",
        "external_connection",
        "adventureworks",
        {"result": "ok" if result.ok else "error"},
    )
    await session.commit()
    return result
