from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import pyodbc  # type: ignore[import-not-found]

from app.modules.parameters.connections import build_connection_string
from app.modules.parameters.models import DataConnection

CONTRACT_VERSION = 1


@dataclass(frozen=True)
class IntrospectionResult:
    document: dict[str, Any]
    content_hash: str
    schema_count: int
    table_count: int
    column_count: int
    relationship_count: int


_COLUMN_QUERY = """
SELECT
    schema_name = schemas.name,
    table_name = tables.name,
    column_name = columns.name,
    ordinal = columns.column_id,
    data_type = types.name,
    max_length = columns.max_length,
    numeric_precision = columns.precision,
    numeric_scale = columns.scale,
    nullable = columns.is_nullable,
    primary_key = CASE WHEN primary_keys.column_id IS NULL THEN 0 ELSE 1 END
FROM sys.tables AS tables
JOIN sys.schemas AS schemas ON schemas.schema_id = tables.schema_id
JOIN sys.columns AS columns ON columns.object_id = tables.object_id
JOIN sys.types AS types
  ON types.user_type_id = columns.system_type_id
 AND types.user_type_id = types.system_type_id
LEFT JOIN (
    SELECT index_columns.object_id, index_columns.column_id
    FROM sys.indexes AS indexes
    JOIN sys.index_columns AS index_columns
      ON index_columns.object_id = indexes.object_id
     AND index_columns.index_id = indexes.index_id
    WHERE indexes.is_primary_key = 1
) AS primary_keys
  ON primary_keys.object_id = columns.object_id
 AND primary_keys.column_id = columns.column_id
WHERE tables.is_ms_shipped = 0
ORDER BY schemas.name, tables.name, columns.column_id
"""

_FOREIGN_KEY_QUERY = """
SELECT
    foreign_key_name = foreign_keys.name,
    source_schema = source_schemas.name,
    source_table = source_tables.name,
    ordinal = foreign_key_columns.constraint_column_id,
    source_column = source_columns.name,
    referenced_schema = referenced_schemas.name,
    referenced_table = referenced_tables.name,
    referenced_column = referenced_columns.name
FROM sys.foreign_keys AS foreign_keys
JOIN sys.foreign_key_columns AS foreign_key_columns
  ON foreign_key_columns.constraint_object_id = foreign_keys.object_id
JOIN sys.tables AS source_tables
  ON source_tables.object_id = foreign_key_columns.parent_object_id
JOIN sys.schemas AS source_schemas
  ON source_schemas.schema_id = source_tables.schema_id
JOIN sys.columns AS source_columns
  ON source_columns.object_id = source_tables.object_id
 AND source_columns.column_id = foreign_key_columns.parent_column_id
JOIN sys.tables AS referenced_tables
  ON referenced_tables.object_id = foreign_key_columns.referenced_object_id
JOIN sys.schemas AS referenced_schemas
  ON referenced_schemas.schema_id = referenced_tables.schema_id
JOIN sys.columns AS referenced_columns
  ON referenced_columns.object_id = referenced_tables.object_id
 AND referenced_columns.column_id = foreign_key_columns.referenced_column_id
WHERE source_tables.is_ms_shipped = 0
  AND referenced_tables.is_ms_shipped = 0
ORDER BY source_schemas.name, source_tables.name, foreign_keys.name,
         foreign_key_columns.constraint_column_id
"""


def _text(value: object) -> str:
    return str(value)


def _integer(value: object) -> int:
    return int(str(value))


def normalize_metadata(
    configuration: DataConnection,
    column_rows: Sequence[Sequence[object]],
    foreign_key_rows: Sequence[Sequence[object]],
) -> IntrospectionResult:
    """Build a stable metadata-only document from SQL Server catalog rows."""
    tables: dict[tuple[str, str], dict[str, Any]] = {}
    for row in sorted(
        column_rows, key=lambda item: (_text(item[0]), _text(item[1]), _integer(item[3]))
    ):
        schema_name, table_name = _text(row[0]), _text(row[1])
        table = tables.setdefault(
            (schema_name, table_name),
            {"name": table_name, "columns": [], "foreign_keys": []},
        )
        table["columns"].append(
            {
                "name": _text(row[2]),
                "ordinal": _integer(row[3]),
                "data_type": _text(row[4]),
                "max_length": _integer(row[5]),
                "precision": _integer(row[6]),
                "scale": _integer(row[7]),
                "nullable": bool(row[8]),
                "primary_key": bool(row[9]),
            }
        )

    foreign_keys: dict[tuple[str, str, str], dict[str, Any]] = {}
    sorted_foreign_keys = sorted(
        foreign_key_rows,
        key=lambda item: (
            _text(item[1]),
            _text(item[2]),
            _text(item[0]),
            _integer(item[3]),
        ),
    )
    for row in sorted_foreign_keys:
        source_schema, source_table, name = _text(row[1]), _text(row[2]), _text(row[0])
        source_table_metadata = tables.get((source_schema, source_table))
        if source_table_metadata is None:
            continue
        key = (source_schema, source_table, name)
        relation = foreign_keys.setdefault(
            key,
            {
                "name": name,
                "columns": [],
                "referenced_schema": _text(row[5]),
                "referenced_table": _text(row[6]),
                "referenced_columns": [],
            },
        )
        relation["columns"].append(_text(row[4]))
        relation["referenced_columns"].append(_text(row[7]))

    for (schema_name, table_name, _), relation in foreign_keys.items():
        tables[(schema_name, table_name)]["foreign_keys"].append(relation)

    schemas: list[dict[str, Any]] = []
    for schema_name in sorted({key[0] for key in tables}):
        schemas.append(
            {
                "name": schema_name,
                "tables": [tables[key] for key in sorted(tables) if key[0] == schema_name],
            }
        )

    document: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "source": {
            "connection_id": configuration.id,
            "connector": configuration.connector_kind,
            "database": configuration.database_name,
        },
        "schemas": schemas,
    }
    canonical = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return IntrospectionResult(
        document=document,
        content_hash=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        schema_count=len(schemas),
        table_count=len(tables),
        column_count=sum(len(table["columns"]) for table in tables.values()),
        relationship_count=len(foreign_keys),
    )


def introspect_sqlserver(
    configuration: DataConnection, password: str, timeout_seconds: int
) -> IntrospectionResult:
    connection = pyodbc.connect(
        build_connection_string(configuration, password),
        timeout=timeout_seconds,
    )
    try:
        connection.timeout = timeout_seconds
        cursor = connection.cursor()
        cursor.execute(_COLUMN_QUERY)
        column_rows = cursor.fetchall()
        cursor.execute(_FOREIGN_KEY_QUERY)
        foreign_key_rows = cursor.fetchall()
        return normalize_metadata(configuration, column_rows, foreign_key_rows)
    finally:
        connection.close()
