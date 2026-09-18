from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pyodbc  # type: ignore[import-not-found]
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.pagination import PageRead
from app.db.session import get_session
from app.modules.parameters.connections import test_sqlserver_read_only
from app.modules.parameters.models import DataConnection, LlmConfiguration, Parameter, Secret
from app.modules.parameters.providers import test_provider
from app.modules.parameters.schemas import (
    ConnectionTestResponse,
    DataConnectionCreate,
    DataConnectionRead,
    DataConnectionUpdate,
    LlmConfigurationCreate,
    LlmConfigurationRead,
    LlmConfigurationUpdate,
    LlmCredentialStatus,
    LlmCredentialWrite,
    ParameterRead,
    ParameterUpdate,
)
from app.modules.parameters.secrets import SecretCipher, SecretDecryptionError
from app.modules.parameters.service import APPROVED_PARAMETERS
from app.modules.security.models import User
from app.modules.security.service import add_audit_event, require_permission

router = APIRouter(tags=["parameters"])

_CREDENTIAL_REFERENCES = {
    "gemini": "encrypted-store",
    "qwen-cloud": "encrypted-store",
    "ollama-local": "none",
}
_secret_cipher = SecretCipher(settings.secrets_key_path)

_PARAMETER_CATALOG = APPROVED_PARAMETERS


def _validated_parameter_value(key: str, value: str) -> str:
    definition = _PARAMETER_CATALOG.get(key)
    if definition is None:
        raise HTTPException(
            status_code=422,
            detail="No existe un parámetro operativo aprobado para esta clave.",
        )
    try:
        parsed = int(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="El valor debe ser un número entero.") from exc
    minimum = int(definition["min_value"])
    maximum = int(definition["max_value"])
    if parsed < minimum or parsed > maximum:
        raise HTTPException(
            status_code=422,
            detail=f"El valor debe estar entre {minimum} y {maximum}.",
        )
    return str(parsed)


async def _parameter_integer(session: AsyncSession, key: str) -> int:
    value = await session.scalar(select(Parameter.value).where(Parameter.key == key))
    fallback = str(_PARAMETER_CATALOG[key]["default_value"])
    return int(value or fallback)


@router.get("/parameters", response_model=PageRead[ParameterRead])
async def list_parameters(
    _: User = Depends(require_permission("parameters.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[ParameterRead]:
    if not _PARAMETER_CATALOG:
        return PageRead(items=[], total=0, limit=limit, offset=offset)
    total = (
        await session.scalar(
            select(func.count()).select_from(Parameter).where(Parameter.key.in_(_PARAMETER_CATALOG))
        )
    ) or 0
    items = (
        await session.execute(
            select(Parameter)
            .where(Parameter.key.in_(_PARAMETER_CATALOG))
            .order_by(Parameter.key)
            .limit(limit)
            .offset(offset)
        )
    ).scalars()
    return PageRead(items=list(items), total=total, limit=limit, offset=offset)


@router.put("/parameters/{key}", response_model=ParameterRead)
async def upsert_parameter(
    key: str,
    payload: ParameterUpdate,
    actor: User = Depends(require_permission("parameters.write")),
    session: AsyncSession = Depends(get_session),
) -> Parameter:
    value = _validated_parameter_value(key, payload.value)
    parameter = (
        await session.execute(select(Parameter).where(Parameter.key == key))
    ).scalar_one_or_none()
    if parameter is None:
        definition = _PARAMETER_CATALOG[key]
        parameter = Parameter(key=key, value=value, is_active=True, **definition)
        session.add(parameter)
    else:
        parameter.value = value
    await session.flush()
    await add_audit_event(
        session,
        actor.id,
        "parameters.update",
        "parameter",
        str(parameter.id),
        {"key": parameter.key, "value": parameter.value},
    )
    await session.commit()
    return parameter


@router.post("/parameters/{key}/reset", response_model=ParameterRead)
async def reset_parameter(
    key: str,
    actor: User = Depends(require_permission("parameters.write")),
    session: AsyncSession = Depends(get_session),
) -> Parameter:
    definition = _PARAMETER_CATALOG.get(key)
    parameter = (
        await session.execute(select(Parameter).where(Parameter.key == key))
    ).scalar_one_or_none()
    if definition is None or parameter is None:
        raise HTTPException(status_code=404, detail="Parámetro operativo no encontrado.")
    parameter.value = str(definition["default_value"])
    await add_audit_event(
        session,
        actor.id,
        "parameters.reset",
        "parameter",
        str(parameter.id),
        {"key": parameter.key, "value": parameter.value},
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
    provider_changed = bool(configuration.id) and (
        configuration.provider_kind != payload.provider_kind
    )
    if provider_changed and configuration.is_active:
        raise HTTPException(
            status_code=422,
            detail="Desactive la configuración antes de cambiar el proveedor.",
        )
    if provider_changed and configuration.secret_id is not None:
        old_secret = await session.get(Secret, configuration.secret_id)
        configuration.secret_id = None
        await session.flush()
        if old_secret is not None:
            await session.delete(old_secret)
    if (
        payload.is_active
        and payload.provider_kind != "ollama-local"
        and configuration.secret_id is None
    ):
        raise HTTPException(
            status_code=422,
            detail="Registre y pruebe la credencial antes de activar esta configuración.",
        )
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


async def _credential_for_configuration(
    configuration: LlmConfiguration, session: AsyncSession
) -> str | None:
    if configuration.provider_kind == "ollama-local" or configuration.secret_id is None:
        return None
    secret = await session.get(Secret, configuration.secret_id)
    if secret is None:
        return None
    try:
        return _secret_cipher.decrypt(secret.ciphertext)
    except (SecretDecryptionError, OSError):
        return None


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


@router.delete("/llm-configurations/{configuration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_configuration(
    configuration_id: int,
    actor: User = Depends(require_permission("parameters.llm.write")),
    session: AsyncSession = Depends(get_session),
) -> Response:
    configuration = (
        await session.execute(
            select(LlmConfiguration).where(LlmConfiguration.id == configuration_id)
        )
    ).scalar_one_or_none()
    if configuration is None:
        raise HTTPException(status_code=404, detail="Configuración LLM no encontrada.")
    if configuration.is_active:
        raise HTTPException(
            status_code=422,
            detail="Desactive la configuración LLM antes de eliminarla definitivamente.",
        )
    stored_secret = (
        await session.get(Secret, configuration.secret_id)
        if configuration.secret_id is not None
        else None
    )
    await add_audit_event(
        session, actor.id, "parameters.llm.delete", "llm_configuration", str(configuration_id)
    )
    await session.delete(configuration)
    await session.flush()
    if stored_secret is not None:
        await session.delete(stored_secret)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/llm-configurations/{configuration_id}/secret",
    response_model=LlmCredentialStatus,
)
async def save_llm_credential(
    configuration_id: int,
    payload: LlmCredentialWrite,
    actor: User = Depends(require_permission("parameters.llm.write")),
    session: AsyncSession = Depends(get_session),
) -> LlmCredentialStatus:
    configuration = (
        await session.execute(
            select(LlmConfiguration).where(LlmConfiguration.id == configuration_id)
        )
    ).scalar_one_or_none()
    if configuration is None:
        raise HTTPException(status_code=404, detail="Configuración LLM no encontrada.")
    if configuration.provider_kind == "ollama-local":
        raise HTTPException(status_code=422, detail="Ollama local no requiere una credencial.")

    api_key = payload.api_key.strip()
    if len(api_key) < 8:
        raise HTTPException(status_code=422, detail="La credencial ingresada no es válida.")
    try:
        ciphertext = _secret_cipher.encrypt(api_key)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="No fue posible proteger la credencial en esta instalación.",
        ) from exc

    secret = (
        await session.get(Secret, configuration.secret_id)
        if configuration.secret_id is not None
        else None
    )
    action = "parameters.llm.credential.register"
    if secret is None:
        secret = Secret(kind="llm", ciphertext=ciphertext)
        session.add(secret)
        await session.flush()
        configuration.secret_id = secret.id
    else:
        action = "parameters.llm.credential.replace"
        secret.ciphertext = ciphertext
    configuration.credential_reference = "encrypted-store"
    configuration.last_test_status = None
    configuration.last_test_message = None
    configuration.last_tested_at = None
    await add_audit_event(
        session,
        actor.id,
        action,
        "llm_configuration",
        str(configuration.id),
        {"provider": configuration.provider_kind},
    )
    await session.commit()
    return LlmCredentialStatus(
        credential_configured=True,
        message="Credencial protegida correctamente. Ya puede probar la conexión.",
    )


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
    credential = await _credential_for_configuration(configuration, session)
    timeout = await _parameter_integer(session, "LLM_TIMEOUT_SECONDS")
    result = await test_provider(configuration, credential, timeout)
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


async def _get_data_connection(connection_id: int, session: AsyncSession) -> DataConnection:
    connection = (
        await session.execute(select(DataConnection).where(DataConnection.id == connection_id))
    ).scalar_one_or_none()
    if connection is None:
        raise HTTPException(status_code=404, detail="Conexión de datos no encontrada.")
    return connection


@router.get("/connections", response_model=PageRead[DataConnectionRead])
async def list_data_connections(
    _: User = Depends(require_permission("connections.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[DataConnectionRead]:
    total = (await session.scalar(select(func.count()).select_from(DataConnection))) or 0
    items = (
        await session.execute(
            select(DataConnection).order_by(DataConnection.id).limit(limit).offset(offset)
        )
    ).scalars()
    return PageRead(items=list(items), total=total, limit=limit, offset=offset)


@router.post("/connections", response_model=DataConnectionRead, status_code=status.HTTP_201_CREATED)
async def create_data_connection(
    payload: DataConnectionCreate,
    actor: User = Depends(require_permission("connections.write")),
    session: AsyncSession = Depends(get_session),
) -> DataConnection:
    try:
        ciphertext = _secret_cipher.encrypt(payload.password)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="No fue posible proteger la contraseña en esta instalación.",
        ) from exc
    secret = Secret(kind="data_source", ciphertext=ciphertext)
    session.add(secret)
    await session.flush()
    connection = DataConnection(
        name=payload.name,
        connector_kind=payload.connector_kind,
        host=payload.host,
        port=payload.port,
        database_name=payload.database_name,
        username=payload.username,
        encrypt=payload.encrypt,
        trust_server_certificate=payload.trust_server_certificate,
        secret_id=secret.id,
    )
    session.add(connection)
    await session.flush()
    await add_audit_event(
        session,
        actor.id,
        "connections.create",
        "data_connection",
        str(connection.id),
        {"connector": connection.connector_kind, "database": connection.database_name},
    )
    await session.commit()
    return connection


@router.put("/connections/{connection_id}", response_model=DataConnectionRead)
async def update_data_connection(
    connection_id: int,
    payload: DataConnectionUpdate,
    actor: User = Depends(require_permission("connections.write")),
    session: AsyncSession = Depends(get_session),
) -> DataConnection:
    connection = await _get_data_connection(connection_id, session)
    if connection.is_active:
        raise HTTPException(status_code=422, detail="Desactive la conexión antes de editarla.")
    connection.name = payload.name
    connection.connector_kind = payload.connector_kind
    connection.host = payload.host
    connection.port = payload.port
    connection.database_name = payload.database_name
    connection.username = payload.username
    connection.encrypt = payload.encrypt
    connection.trust_server_certificate = payload.trust_server_certificate
    if payload.password:
        secret = await session.get(Secret, connection.secret_id)
        if secret is None:
            raise HTTPException(status_code=409, detail="La credencial de la conexión no existe.")
        try:
            secret.ciphertext = _secret_cipher.encrypt(payload.password)
        except OSError as exc:
            raise HTTPException(
                status_code=500,
                detail="No fue posible proteger la contraseña en esta instalación.",
            ) from exc
    connection.last_test_status = None
    connection.last_test_message = None
    connection.last_tested_at = None
    await add_audit_event(
        session,
        actor.id,
        "connections.update",
        "data_connection",
        str(connection.id),
        {"connector": connection.connector_kind, "database": connection.database_name},
    )
    await session.commit()
    return connection


@router.post("/connections/{connection_id}/test", response_model=ConnectionTestResponse)
async def verify_data_connection(
    connection_id: int,
    actor: User = Depends(require_permission("connections.test")),
    session: AsyncSession = Depends(get_session),
) -> ConnectionTestResponse:
    connection = await _get_data_connection(connection_id, session)
    secret = await session.get(Secret, connection.secret_id)
    try:
        if secret is None:
            raise SecretDecryptionError("missing secret")
        password = _secret_cipher.decrypt(secret.ciphertext)
        timeout = await _parameter_integer(session, "CONNECTION_TIMEOUT_SECONDS")
        test_result = await asyncio.to_thread(
            test_sqlserver_read_only, connection, password, timeout
        )
        result = ConnectionTestResponse(ok=test_result.ok, message=test_result.message)
    except (pyodbc.Error, SecretDecryptionError, OSError):
        result = ConnectionTestResponse(
            ok=False,
            message="No fue posible validar la conexión SQL Server con los datos registrados.",
        )
    connection.last_test_status = "ok" if result.ok else "error"
    connection.last_test_message = result.message
    connection.last_tested_at = datetime.now(UTC)
    await add_audit_event(
        session,
        actor.id,
        "connections.test",
        "data_connection",
        str(connection.id),
        {"result": "ok" if result.ok else "error"},
    )
    await session.commit()
    return result


@router.post("/connections/{connection_id}/activate", response_model=DataConnectionRead)
async def activate_data_connection(
    connection_id: int,
    actor: User = Depends(require_permission("connections.write")),
    session: AsyncSession = Depends(get_session),
) -> DataConnection:
    connection = await _get_data_connection(connection_id, session)
    if connection.last_test_status != "ok":
        raise HTTPException(
            status_code=422, detail="Pruebe correctamente la conexión antes de activarla."
        )
    await session.execute(
        update(DataConnection)
        .where(DataConnection.id != connection.id, DataConnection.is_active.is_(True))
        .values(is_active=False)
    )
    connection.is_active = True
    await add_audit_event(
        session, actor.id, "connections.activate", "data_connection", str(connection.id)
    )
    await session.commit()
    return connection


@router.post("/connections/{connection_id}/deactivate", response_model=DataConnectionRead)
async def deactivate_data_connection(
    connection_id: int,
    actor: User = Depends(require_permission("connections.write")),
    session: AsyncSession = Depends(get_session),
) -> DataConnection:
    connection = await _get_data_connection(connection_id, session)
    connection.is_active = False
    await add_audit_event(
        session, actor.id, "connections.deactivate", "data_connection", str(connection.id)
    )
    await session.commit()
    return connection


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_connection(
    connection_id: int,
    actor: User = Depends(require_permission("connections.write")),
    session: AsyncSession = Depends(get_session),
) -> Response:
    connection = await _get_data_connection(connection_id, session)
    if connection.is_active:
        raise HTTPException(status_code=422, detail="Desactive la conexión antes de eliminarla.")
    secret = await session.get(Secret, connection.secret_id)
    await add_audit_event(
        session, actor.id, "connections.delete", "data_connection", str(connection.id)
    )
    await session.delete(connection)
    await session.flush()
    if secret is not None:
        await session.delete(secret)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
