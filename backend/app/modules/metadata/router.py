from __future__ import annotations

import asyncio
from typing import Any

import pyodbc  # type: ignore[import-not-found]
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.pagination import PageRead
from app.db.session import get_session
from app.modules.metadata.introspection import CONTRACT_VERSION, introspect_sqlserver
from app.modules.metadata.models import MetadataSnapshot
from app.modules.metadata.schemas import (
    ActiveConnectionSummary,
    ActiveSourceRead,
    SnapshotCaptureResponse,
    SnapshotDetail,
    SnapshotSummary,
    TableDetail,
    TableSummary,
)
from app.modules.metadata.service import flattened_tables
from app.modules.parameters.models import DataConnection, Parameter, Secret
from app.modules.parameters.secrets import SecretCipher, SecretDecryptionError
from app.modules.parameters.service import APPROVED_PARAMETERS
from app.modules.security.models import User
from app.modules.security.service import add_audit_event, require_permission

router = APIRouter(tags=["metadata"])
_secret_cipher = SecretCipher(settings.secrets_key_path)


async def _active_connection(session: AsyncSession) -> DataConnection | None:
    return (
        await session.execute(select(DataConnection).where(DataConnection.is_active.is_(True)))
    ).scalar_one_or_none()


async def _latest_snapshot(
    session: AsyncSession, connection_id: int | None = None
) -> MetadataSnapshot | None:
    statement = select(MetadataSnapshot)
    if connection_id is not None:
        statement = statement.where(MetadataSnapshot.data_connection_id == connection_id)
    return (
        await session.execute(statement.order_by(MetadataSnapshot.captured_at.desc()).limit(1))
    ).scalar_one_or_none()


async def _timeout_seconds(session: AsyncSession) -> int:
    value = await session.scalar(
        select(Parameter.value).where(Parameter.key == "CONNECTION_TIMEOUT_SECONDS")
    )
    return int(value or APPROVED_PARAMETERS["CONNECTION_TIMEOUT_SECONDS"]["default_value"])


async def _snapshot_or_404(snapshot_id: int, session: AsyncSession) -> MetadataSnapshot:
    snapshot = await session.get(MetadataSnapshot, snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Instantánea de metadatos no encontrada.")
    return snapshot


@router.get("/sources/active", response_model=ActiveSourceRead)
async def get_active_source(
    _: User = Depends(require_permission("metadata.read")),
    session: AsyncSession = Depends(get_session),
) -> ActiveSourceRead:
    connection = await _active_connection(session)
    if connection is None:
        return ActiveSourceRead(status="missing")
    snapshot = await _latest_snapshot(session, connection.id)
    return ActiveSourceRead(
        status="ready",
        connection=ActiveConnectionSummary.model_validate(connection, from_attributes=True),
        latest_snapshot=(
            SnapshotSummary.model_validate(snapshot, from_attributes=True) if snapshot else None
        ),
    )


@router.post(
    "/metadata/snapshots",
    response_model=SnapshotCaptureResponse,
    status_code=status.HTTP_200_OK,
)
async def capture_metadata_snapshot(
    actor: User = Depends(require_permission("metadata.refresh")),
    session: AsyncSession = Depends(get_session),
) -> SnapshotCaptureResponse:
    connection = await _active_connection(session)
    if connection is None:
        raise HTTPException(
            status_code=422,
            detail="Active y pruebe una conexión de datos antes de actualizar metadatos.",
        )
    if connection.last_test_status != "ok":
        raise HTTPException(
            status_code=422,
            detail="La fuente activa debe superar nuevamente la prueba de sólo lectura.",
        )
    lock_acquired = await session.scalar(select(func.pg_try_advisory_xact_lock(connection.id)))
    if not lock_acquired:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una actualización de metadatos en curso para esta fuente.",
        )

    secret = await session.get(Secret, connection.secret_id)
    try:
        if secret is None:
            raise SecretDecryptionError("missing secret")
        password = _secret_cipher.decrypt(secret.ciphertext)
        timeout = await _timeout_seconds(session)
        result = await asyncio.to_thread(introspect_sqlserver, connection, password, timeout)
    except (pyodbc.Error, SecretDecryptionError, OSError):
        await add_audit_event(
            session,
            actor.id,
            "metadata.snapshot.failed",
            "data_connection",
            str(connection.id),
            {"category": "source_unavailable"},
        )
        await session.commit()
        raise HTTPException(
            status_code=503,
            detail=(
                "No fue posible leer la estructura de la fuente. "
                "La última instantánea válida se conserva sin cambios."
            ),
        ) from None

    previous = await _latest_snapshot(session, connection.id)
    if (
        previous is not None
        and previous.contract_version == CONTRACT_VERSION
        and previous.content_hash == result.content_hash
    ):
        await add_audit_event(
            session,
            actor.id,
            "metadata.snapshot.unchanged",
            "metadata_snapshot",
            str(previous.id),
            {"hash": previous.content_hash[:12]},
        )
        await session.commit()
        return SnapshotCaptureResponse(
            created=False,
            message="La estructura no cambió; se mantiene la instantánea vigente.",
            snapshot=SnapshotSummary.model_validate(previous, from_attributes=True),
        )

    snapshot = MetadataSnapshot(
        data_connection_id=connection.id,
        connector_code=connection.connector_kind,
        database_name=connection.database_name,
        contract_version=CONTRACT_VERSION,
        content_hash=result.content_hash,
        schema_document=result.document,
        schema_count=result.schema_count,
        table_count=result.table_count,
        column_count=result.column_count,
        relationship_count=result.relationship_count,
        captured_by_user_id=actor.id,
        captured_by_label=f"{actor.full_name} <{actor.email}>",
    )
    session.add(snapshot)
    await session.flush()
    await add_audit_event(
        session,
        actor.id,
        "metadata.snapshot.create",
        "metadata_snapshot",
        str(snapshot.id),
        {
            "hash": snapshot.content_hash[:12],
            "schemas": snapshot.schema_count,
            "tables": snapshot.table_count,
            "columns": snapshot.column_count,
            "relationships": snapshot.relationship_count,
        },
    )
    await session.commit()
    return SnapshotCaptureResponse(
        created=True,
        message="La estructura se leyó correctamente y se creó una nueva instantánea.",
        snapshot=SnapshotSummary.model_validate(snapshot, from_attributes=True),
    )


@router.get("/metadata/snapshots", response_model=PageRead[SnapshotSummary])
async def list_metadata_snapshots(
    _: User = Depends(require_permission("metadata.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[SnapshotSummary]:
    total = (await session.scalar(select(func.count()).select_from(MetadataSnapshot))) or 0
    items = (
        await session.execute(
            select(MetadataSnapshot)
            .order_by(MetadataSnapshot.captured_at.desc(), MetadataSnapshot.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars()
    return PageRead(items=list(items), total=total, limit=limit, offset=offset)


@router.get("/metadata/snapshots/{snapshot_id}", response_model=SnapshotDetail)
async def get_metadata_snapshot(
    snapshot_id: int,
    _: User = Depends(require_permission("metadata.read")),
    session: AsyncSession = Depends(get_session),
) -> MetadataSnapshot:
    return await _snapshot_or_404(snapshot_id, session)


def _matching_tables(
    document: dict[str, Any], search: str | None, schema_name: str | None
) -> list[dict[str, Any]]:
    search_value = (search or "").strip().casefold()
    schema_value = (schema_name or "").strip().casefold()
    matches: list[dict[str, Any]] = []
    for table in flattened_tables(document):
        if schema_value and str(table["schema_name"]).casefold() != schema_value:
            continue
        haystack = " ".join(
            [
                str(table["schema_name"]),
                str(table.get("name", "")),
                *[str(column.get("name", "")) for column in table.get("columns", [])],
            ]
        ).casefold()
        if search_value and search_value not in haystack:
            continue
        matches.append(table)
    return sorted(matches, key=lambda item: (item["schema_name"], item["name"]))


@router.get("/metadata/snapshots/{snapshot_id}/tables", response_model=PageRead[TableSummary])
async def list_snapshot_tables(
    snapshot_id: int,
    _: User = Depends(require_permission("metadata.read")),
    session: AsyncSession = Depends(get_session),
    search: str | None = Query(default=None, max_length=120),
    schema_name: str | None = Query(default=None, max_length=128),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[TableSummary]:
    snapshot = await _snapshot_or_404(snapshot_id, session)
    matches = _matching_tables(snapshot.schema_document, search, schema_name)
    items = [
        TableSummary(
            schema_name=str(table["schema_name"]),
            table_name=str(table["name"]),
            column_count=len(table.get("columns", [])),
            relationship_count=len(table.get("foreign_keys", [])),
        )
        for table in matches[offset : offset + limit]
    ]
    return PageRead(items=items, total=len(matches), limit=limit, offset=offset)


@router.get(
    "/metadata/snapshots/{snapshot_id}/tables/{schema_name}/{table_name}",
    response_model=TableDetail,
)
async def get_snapshot_table(
    snapshot_id: int,
    schema_name: str,
    table_name: str,
    _: User = Depends(require_permission("metadata.read")),
    session: AsyncSession = Depends(get_session),
) -> TableDetail:
    snapshot = await _snapshot_or_404(snapshot_id, session)
    tables = flattened_tables(snapshot.schema_document)
    table = next(
        (
            item
            for item in tables
            if item["schema_name"] == schema_name and item.get("name") == table_name
        ),
        None,
    )
    if table is None:
        raise HTTPException(status_code=404, detail="Tabla no encontrada en la instantánea.")
    incoming: list[dict[str, Any]] = []
    for source in tables:
        for relation in source.get("foreign_keys", []):
            if (
                relation.get("referenced_schema") == schema_name
                and relation.get("referenced_table") == table_name
            ):
                incoming.append(
                    {
                        "name": relation.get("name"),
                        "source_schema": source["schema_name"],
                        "source_table": source.get("name"),
                        "source_columns": relation.get("columns", []),
                        "referenced_columns": relation.get("referenced_columns", []),
                    }
                )
    return TableDetail(
        schema_name=schema_name,
        table_name=table_name,
        columns=table.get("columns", []),
        foreign_keys=table.get("foreign_keys", []),
        incoming_relationships=incoming,
    )
