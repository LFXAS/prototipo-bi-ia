from __future__ import annotations

from collections.abc import Callable

from app.modules.metadata.introspection import IntrospectionResult, introspect_sqlserver
from app.modules.parameters.models import DataConnection

MetadataReader = Callable[[DataConnection, str, int], IntrospectionResult]

CONNECTOR_READERS: dict[str, MetadataReader] = {
    "sqlserver": introspect_sqlserver,
}


def read_metadata(
    configuration: DataConnection, password: str, timeout_seconds: int
) -> IntrospectionResult:
    """Dispatch through an explicit connector registry.

    The canonical metadata contract remains independent from the source engine.
    New engines add an adapter here without changing the copilot contract.
    """
    reader = CONNECTOR_READERS.get(configuration.connector_kind)
    if reader is None:
        raise ValueError("El motor configurado todavía no tiene un adaptador de metadatos.")
    return reader(configuration, password, timeout_seconds)
