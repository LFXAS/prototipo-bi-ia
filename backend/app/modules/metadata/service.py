from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.metadata.models import MetadataSnapshot


async def count_snapshots_for_connection(session: AsyncSession, connection_id: int) -> int:
    return int(
        await session.scalar(
            select(func.count())
            .select_from(MetadataSnapshot)
            .where(MetadataSnapshot.data_connection_id == connection_id)
        )
        or 0
    )


def flattened_tables(document: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for schema in document.get("schemas", []):
        if not isinstance(schema, dict):
            continue
        schema_name = str(schema.get("name", ""))
        for table in schema.get("tables", []):
            if isinstance(table, dict):
                items.append({"schema_name": schema_name, **table})
    return items
