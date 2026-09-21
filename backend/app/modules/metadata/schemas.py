from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SnapshotSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_connection_id: int
    connector_code: str
    database_name: str
    contract_version: int
    content_hash: str
    schema_count: int
    table_count: int
    column_count: int
    relationship_count: int
    captured_by_label: str
    captured_at: datetime


class SnapshotDetail(SnapshotSummary):
    schema_document: dict[str, Any]


class SnapshotCaptureResponse(BaseModel):
    created: bool
    message: str
    snapshot: SnapshotSummary


class ActiveConnectionSummary(BaseModel):
    id: int
    name: str
    connector_kind: str
    database_name: str
    last_test_status: str | None = None
    last_tested_at: datetime | None = None


class ActiveSourceRead(BaseModel):
    status: Literal["ready", "missing"]
    connection: ActiveConnectionSummary | None = None
    latest_snapshot: SnapshotSummary | None = None


class TableSummary(BaseModel):
    schema_name: str
    table_name: str
    column_count: int = Field(ge=0)
    relationship_count: int = Field(ge=0)


class TableDetail(BaseModel):
    schema_name: str
    table_name: str
    columns: list[dict[str, Any]]
    foreign_keys: list[dict[str, Any]]
    incoming_relationships: list[dict[str, Any]]
