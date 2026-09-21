from __future__ import annotations

import json
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.copilot.domains import default_needs_catalog_configuration
from app.modules.parameters.models import Parameter


class ParameterDefinition(TypedDict):
    name: str
    description: str
    module_code: str
    value_type: str
    default_value: str
    min_value: int | None
    max_value: int | None


APPROVED_PARAMETERS: dict[str, ParameterDefinition] = {
    "UI_PAGE_SIZE": {
        "name": "Registros por página",
        "description": "Cantidad predeterminada de registros mostrados en los listados.",
        "module_code": "ui",
        "value_type": "integer",
        "default_value": "10",
        "min_value": 10,
        "max_value": 100,
    },
    "CONNECTION_TIMEOUT_SECONDS": {
        "name": "Tiempo máximo de conexión",
        "description": "Segundos máximos para probar una fuente de datos.",
        "module_code": "connections",
        "value_type": "integer",
        "default_value": "8",
        "min_value": 3,
        "max_value": 30,
    },
    "LLM_TIMEOUT_SECONDS": {
        "name": "Tiempo máximo del asistente",
        "description": "Segundos máximos para una solicitud al proveedor LLM.",
        "module_code": "llm",
        "value_type": "integer",
        "default_value": "600",
        "min_value": 10,
        "max_value": 900,
    },
    "METADATA_BLOCK_MAX_ITEMS": {
        "name": "Elementos por bloque de metadatos",
        "description": "Cantidad máxima de elementos técnicos enviados al LLM por bloque.",
        "module_code": "metadata",
        "value_type": "integer",
        "default_value": "100",
        "min_value": 25,
        "max_value": 200,
    },
    "COPILOT_SALES_NEEDS_CATALOG": {
        "name": "Catálogo analítico de ventas",
        "description": (
            "Configura preguntas de negocio y periodicidades que orientan a la IA. "
            "No define el objetivo ni el modelo dimensional."
        ),
        "module_code": "copilot",
        "value_type": "analysis_catalog",
        "default_value": json.dumps(
            default_needs_catalog_configuration(), ensure_ascii=False, separators=(",", ":")
        ),
        "min_value": None,
        "max_value": None,
    },
}


async def seed_parameters(session: AsyncSession) -> None:
    existing = {item.key: item for item in (await session.execute(select(Parameter))).scalars()}
    for key, definition in APPROVED_PARAMETERS.items():
        parameter = existing.get(key)
        if parameter is None:
            session.add(
                Parameter(
                    key=key,
                    name=str(definition["name"]),
                    description=str(definition["description"]),
                    module_code=str(definition["module_code"]),
                    value_type=str(definition["value_type"]),
                    value=str(definition["default_value"]),
                    default_value=str(definition["default_value"]),
                    min_value=(
                        int(definition["min_value"])
                        if definition["min_value"] is not None
                        else None
                    ),
                    max_value=(
                        int(definition["max_value"])
                        if definition["max_value"] is not None
                        else None
                    ),
                    is_active=True,
                )
            )
            continue
        parameter.name = str(definition["name"])
        parameter.description = str(definition["description"])
        parameter.module_code = str(definition["module_code"])
        parameter.value_type = str(definition["value_type"])
        parameter.default_value = str(definition["default_value"])
        parameter.min_value = (
            int(definition["min_value"]) if definition["min_value"] is not None else None
        )
        parameter.max_value = (
            int(definition["max_value"]) if definition["max_value"] is not None else None
        )
        parameter.is_active = True
    await session.commit()
