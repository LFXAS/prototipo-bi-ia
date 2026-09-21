from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any

from app.modules.copilot.domains import SALES_PROFILE

PROMPT_VERSION = "sales-bi-v3"
CONTRACT_VERSION = 1
ALLOWED_OPERATIONS = {"extract", "join", "filter", "derive", "aggregate", "load"}
ALLOWED_AGGREGATIONS = {"sum", "count", "count_distinct", "average", "min", "max"}
ALLOWED_DESTINATIONS = SALES_PROFILE.destination_names
PROPOSAL_SCOPE_MAX_TABLES = 8

SEMANTIC_SYSTEM_INSTRUCTION = (
    "Eres un asistente de modelado dimensional de ventas. Interpreta exclusivamente los "
    "metadatos recibidos. No inventes tablas ni columnas, no produzcas SQL y no uses "
    "conocimiento externo de la base. Devuelve solo JSON válido con contract_version=1, "
    "candidates y ambiguities. Cada candidato debe incluir business_concept, "
    "business_name_es, description_es, technical_refs (nombres exactos esquema.tabla "
    "presentes), confidence (high, medium o low) y reason. Devuelve como máximo seis "
    "candidatos. Prioriza hechos de venta, fecha, producto, cliente y territorio relacionados "
    "con la necesidad. Las explicaciones deben estar en español. Sigue exactamente esta forma: "
    '{"contract_version":1,"candidates":[{"business_concept":"sale_line",'
    '"business_name_es":"Detalle de venta","description_es":"Línea vendida",'
    '"technical_refs":["Sales.SalesOrderDetail"],"confidence":"high",'
    '"reason":"Contiene cantidades e importes"}],"ambiguities":[]}.'
)

PROPOSAL_SYSTEM_INSTRUCTION = (
    "Eres un asistente de inteligencia de negocios. Propón un único datamart de ventas "
    "usando solamente los objetos del alcance recibido. No generes SQL, Python ni código. "
    "Devuelve solo JSON válido con contract_version, domain, summary, business_explanation, "
    "semantic_mapping, grain, fact, dimensions, joins, kpis, etl_plan, quality_rules, "
    "assumptions y warnings. El hecho debe llamarse fact_ventas y las únicas dimensiones "
    "destino posibles son dim_fecha, dim_producto, dim_cliente y dim_territorio. "
    "source_tables y technical_refs usan esquema.tabla exacto. Las columnas conservan su "
    "nombre técnico exacto. joins usa left_table, right_table, left_columns y right_columns "
    "y sólo relaciones declaradas. Las medidas usan source_columns y aggregation del catálogo "
    "sum, count, count_distinct, average, min o max. Los KPI usan formula con operation y "
    "measure. etl_plan sólo usa extract, join, filter, derive, aggregate o load. Explica en "
    "español y reconoce incertidumbres. Cada medida tiene name, source_columns y aggregation; "
    "cada dimensión tiene name, source_tables, business_key y attributes; cada KPI tiene code, "
    "name, formula con operation y measure, y unit. Cada paso ETL tiene order, operation, inputs, "
    "output y description. Usa arreglos para joins, dimensions, kpis, etl_plan, quality_rules, "
    "assumptions y warnings. Sé conciso: máximo tres medidas, cuatro dimensiones, seis uniones, "
    "cuatro KPI y seis pasos ETL; cada explicación debe tener menos de 160 caracteres."
)

TEXT_SCHEMA: dict[str, Any] = {"type": "string", "maxLength": 160}
STRING_ARRAY_SCHEMA: dict[str, Any] = {
    "type": "array",
    "maxItems": 8,
    "items": TEXT_SCHEMA,
}
SHORT_STRING_ARRAY_SCHEMA: dict[str, Any] = {
    "type": "array",
    "maxItems": 4,
    "items": TEXT_SCHEMA,
}
SEMANTIC_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["contract_version", "candidates", "ambiguities"],
    "properties": {
        "contract_version": {"type": "integer", "enum": [CONTRACT_VERSION]},
        "candidates": {
            "type": "array",
            "maxItems": 6,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "business_concept",
                    "business_name_es",
                    "description_es",
                    "technical_refs",
                    "confidence",
                    "reason",
                ],
                "properties": {
                    "business_concept": TEXT_SCHEMA,
                    "business_name_es": TEXT_SCHEMA,
                    "description_es": TEXT_SCHEMA,
                    "technical_refs": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 3,
                        "items": TEXT_SCHEMA,
                    },
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "reason": TEXT_SCHEMA,
                },
            },
        },
        "ambiguities": STRING_ARRAY_SCHEMA,
    },
}
PROPOSAL_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "contract_version",
        "domain",
        "summary",
        "business_explanation",
        "semantic_mapping",
        "grain",
        "fact",
        "dimensions",
        "joins",
        "kpis",
        "etl_plan",
        "quality_rules",
        "assumptions",
        "warnings",
    ],
    "properties": {
        "contract_version": {"type": "integer", "enum": [CONTRACT_VERSION]},
        "domain": {"type": "string", "enum": [SALES_PROFILE.code]},
        "summary": TEXT_SCHEMA,
        "business_explanation": TEXT_SCHEMA,
        "semantic_mapping": {"type": "array", "maxItems": 0},
        "grain": {
            "type": "object",
            "additionalProperties": False,
            "required": ["description", "source_tables"],
            "properties": {
                "description": TEXT_SCHEMA,
                "source_tables": STRING_ARRAY_SCHEMA,
            },
        },
        "fact": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "source_tables", "business_keys", "measures"],
            "properties": {
                "name": {"type": "string", "enum": ["fact_ventas"]},
                "source_tables": STRING_ARRAY_SCHEMA,
                "business_keys": STRING_ARRAY_SCHEMA,
                "measures": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name", "source_columns", "aggregation"],
                        "properties": {
                            "name": TEXT_SCHEMA,
                            "source_columns": STRING_ARRAY_SCHEMA,
                            "aggregation": {
                                "type": "string",
                                "enum": sorted(ALLOWED_AGGREGATIONS),
                            },
                        },
                    },
                },
            },
        },
        "dimensions": {
            "type": "array",
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "source_tables", "business_key", "attributes"],
                "properties": {
                    "name": {
                        "type": "string",
                        "enum": sorted(ALLOWED_DESTINATIONS - {"fact_ventas"}),
                    },
                    "source_tables": STRING_ARRAY_SCHEMA,
                    "business_key": TEXT_SCHEMA,
                    "attributes": STRING_ARRAY_SCHEMA,
                },
            },
        },
        "joins": {
            "type": "array",
            "maxItems": 6,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "left_table",
                    "right_table",
                    "left_columns",
                    "right_columns",
                ],
                "properties": {
                    "left_table": TEXT_SCHEMA,
                    "right_table": TEXT_SCHEMA,
                    "left_columns": STRING_ARRAY_SCHEMA,
                    "right_columns": STRING_ARRAY_SCHEMA,
                },
            },
        },
        "kpis": {
            "type": "array",
            "minItems": 1,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["code", "name", "formula", "unit"],
                "properties": {
                    "code": TEXT_SCHEMA,
                    "name": TEXT_SCHEMA,
                    "formula": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["operation", "measure"],
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": sorted(ALLOWED_AGGREGATIONS),
                            },
                            "measure": TEXT_SCHEMA,
                        },
                    },
                    "unit": TEXT_SCHEMA,
                },
            },
        },
        "etl_plan": {
            "type": "array",
            "minItems": 1,
            "maxItems": 6,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["order", "operation", "inputs", "output", "description"],
                "properties": {
                    "order": {"type": "integer"},
                    "operation": {"type": "string", "enum": sorted(ALLOWED_OPERATIONS)},
                    "inputs": STRING_ARRAY_SCHEMA,
                    "output": TEXT_SCHEMA,
                    "description": TEXT_SCHEMA,
                },
            },
        },
        "quality_rules": SHORT_STRING_ARRAY_SCHEMA,
        "assumptions": SHORT_STRING_ARRAY_SCHEMA,
        "warnings": SHORT_STRING_ARRAY_SCHEMA,
    },
}

PROPOSAL_BLUEPRINT_SYSTEM_INSTRUCTION = (
    "Eres el copiloto de un analista de BI. Decide un modelo dimensional de ventas usando "
    "exclusivamente las tablas y columnas del alcance recibido. No generes SQL ni código. "
    "Devuelve sólo JSON válido y breve. Selecciona una tabla de hechos, hasta dos medidas, "
    "entre una y cuatro dimensiones y hasta tres KPI. Cada medida debe usar una columna de la "
    "tabla de hechos y priorizar importe, total o cantidad; no sumes identificadores. Declara "
    "semantic_role en cada medida y KPI usando sales_amount, quantity, customer_count o "
    "transaction_count. Cada KPI usa measure_index=0 para la primera medida o 1 para la segunda "
    "y debe tener el mismo semantic_role que su medida. Un KPI customer_count requiere una "
    "medida customer_count con conteo distinto de un identificador de cliente. Asocia producto, "
    "cliente y territorio con la tabla técnica cuyo nombre corresponda. No inventes "
    "identificadores. Las explicaciones y nombres de negocio deben estar en español."
)

SEMANTIC_ROLES = {
    "sales_amount",
    "quantity",
    "customer_count",
    "transaction_count",
}
ROLE_AGGREGATIONS = {
    "sales_amount": {"sum", "average", "min", "max"},
    "quantity": {"sum", "average", "min", "max"},
    "customer_count": {"count_distinct"},
    "transaction_count": {"count", "count_distinct"},
}
ROLE_DEFAULT_AGGREGATION = {
    "sales_amount": "sum",
    "quantity": "sum",
    "customer_count": "count_distinct",
    "transaction_count": "count_distinct",
}


def proposal_blueprint_schema(
    scope: dict[str, Any], semantic_map: dict[str, Any]
) -> dict[str, Any]:
    """Constrain the LLM to compact decisions that the application can expand safely."""
    tables = [
        str(item.get("ref"))
        for item in scope.get("tables", [])
        if isinstance(item, dict) and item.get("ref")
    ]
    table_enum = tables or ["sin_tabla"]
    fact_candidates = list(
        dict.fromkeys(
            str(reference)
            for candidate in semantic_map.get("candidates", [])
            if isinstance(candidate, dict)
            and any(
                token in str(candidate.get("business_concept", "")).casefold()
                for token in ("sale", "venta", "order", "pedido")
            )
            for reference in candidate.get("technical_refs", [])
            if str(reference) in table_enum
        )
    )
    if not fact_candidates:
        fact_candidates = table_enum
    fact_candidate_set = set(fact_candidates)
    measure_terms = {
        "amount",
        "total",
        "qty",
        "quantity",
        "price",
        "cost",
        "tax",
        "freight",
        "importe",
        "cantidad",
        "customer",
        "cliente",
        "account",
        "order",
        "pedido",
        "transaction",
    }
    measure_columns = sorted(
        {
            str(column.get("name"))
            for item in scope.get("tables", [])
            if isinstance(item, dict) and str(item.get("ref")) in fact_candidate_set
            for column in item.get("columns", [])
            if isinstance(column, dict)
            and column.get("name")
            and bool(_search_tokens(column.get("name")) & measure_terms)
        }
    )
    if not measure_columns:
        measure_columns = sorted(
            {
                str(column.get("name"))
                for item in scope.get("tables", [])
                if isinstance(item, dict) and str(item.get("ref")) in fact_candidate_set
                for column in item.get("columns", [])
                if isinstance(column, dict)
                and column.get("name")
                and not bool(column.get("pk", False))
                and re.search(
                    r"int|decimal|numeric|money|float|real",
                    str(column.get("type", "")).casefold(),
                )
            }
        )
    column_enum = measure_columns or ["sin_columna"]
    short_text = {"type": "string", "maxLength": 120}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "contract_version",
            "domain",
            "summary",
            "grain_description",
            "fact_source",
            "measures",
            "dimensions",
            "kpis",
            "assumptions",
            "warnings",
        ],
        "properties": {
            "contract_version": {"type": "integer", "enum": [CONTRACT_VERSION]},
            "domain": {"type": "string", "enum": [SALES_PROFILE.code]},
            "summary": short_text,
            "grain_description": short_text,
            "fact_source": {"type": "string", "enum": fact_candidates},
            "measures": {
                "type": "array",
                "minItems": 1,
                "maxItems": 2,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "source_column", "aggregation", "semantic_role"],
                    "properties": {
                        "name": short_text,
                        "source_column": {"type": "string", "enum": column_enum},
                        "aggregation": {
                            "type": "string",
                            "enum": sorted(ALLOWED_AGGREGATIONS),
                        },
                        "semantic_role": {
                            "type": "string",
                            "enum": sorted(SEMANTIC_ROLES),
                        },
                    },
                },
            },
            "dimensions": {
                "type": "array",
                "minItems": 1,
                "maxItems": 4,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "source_table"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "enum": sorted(ALLOWED_DESTINATIONS - {"fact_ventas"}),
                        },
                        "source_table": {"type": "string", "enum": table_enum},
                    },
                },
            },
            "kpis": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "code",
                        "name",
                        "measure_index",
                        "operation",
                        "unit",
                        "semantic_role",
                    ],
                    "properties": {
                        "code": short_text,
                        "name": short_text,
                        "measure_index": {"type": "integer", "enum": [0, 1]},
                        "operation": {
                            "type": "string",
                            "enum": sorted(ALLOWED_AGGREGATIONS),
                        },
                        "unit": short_text,
                        "semantic_role": {
                            "type": "string",
                            "enum": sorted(SEMANTIC_ROLES),
                        },
                    },
                },
            },
            "assumptions": {
                "type": "array",
                "maxItems": 2,
                "items": short_text,
            },
            "warnings": {
                "type": "array",
                "maxItems": 2,
                "items": short_text,
            },
        },
    }


def canonical_hash(value: object) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def verify_proposal_evidence(
    proposal_document: dict[str, Any],
    stored_validation: dict[str, Any],
    scope: dict[str, Any],
    semantic_map: dict[str, Any],
    metadata_document: dict[str, Any],
    snapshot_hash: str,
    proposal_prompt_version: str | None = None,
) -> dict[str, Any]:
    """Re-run deterministic controls without invoking the LLM or executing ETL."""
    snapshot_integrity = canonical_hash(metadata_document) == snapshot_hash
    current_validation = validate_proposal(proposal_document, scope, metadata_document)
    current_issues = [
        item for item in current_validation.get("issues", []) if isinstance(item, dict)
    ]
    reference_errors = [
        item
        for item in current_issues
        if item.get("level") == "error"
        and (
            str(item.get("code", "")).startswith("reference.")
            or item.get("code") == "join.not_declared"
        )
    ]
    references_valid = not reference_errors
    validation_consistent = canonical_hash(current_validation) == canonical_hash(stored_validation)
    same_engine_version = (
        proposal_prompt_version is None or proposal_prompt_version == PROMPT_VERSION
    )

    blueprint = proposal_document.get("ai_decisions")
    replay_hash = ""
    deterministic_replay = False
    if isinstance(blueprint, dict):
        replay = expand_proposal_blueprint(blueprint, scope, semantic_map)
        replay_hash = canonical_hash(replay)
        deterministic_replay = replay_hash == canonical_hash(proposal_document)

    candidates = [item for item in semantic_map.get("candidates", []) if isinstance(item, dict)]
    validated_reference_count = sum(
        len(item.get("technical_refs", []))
        for item in candidates
        if bool(item.get("references_validated")) and isinstance(item.get("technical_refs"), list)
    )
    rejected_reference_count = len(
        [item for item in semantic_map.get("rejected_references", []) if isinstance(item, dict)]
    )
    replay_blocking = same_engine_version and not deterministic_replay
    validation_blocking = same_engine_version and not validation_consistent
    approval_safe = (
        snapshot_integrity
        and bool(current_validation.get("valid"))
        and not replay_blocking
        and not validation_blocking
    )
    compatibility_warning = not same_engine_version
    checks = [
        {
            "code": "snapshot.integrity",
            "label": "Integridad de los metadatos",
            "passed": snapshot_integrity,
            "detail": "La huella coincide con la instantánea estructural persistida.",
        },
        {
            "code": "references.current",
            "label": "Referencias técnicas comprobadas",
            "passed": references_valid,
            "detail": (
                f"{validated_reference_count} referencias técnicas válidas; "
                f"{rejected_reference_count} descartadas."
            ),
        },
        {
            "code": "validation.consistency",
            "label": "Consistencia del contrato BI",
            "passed": validation_consistent if same_engine_version else False,
            "detail": (
                (
                    "La propuesta fue creada con "
                    f"{proposal_prompt_version} y el motor actual es {PROMPT_VERSION}; "
                    "la comparación histórica se conserva como advertencia de compatibilidad."
                )
                if not same_engine_version
                else (
                    "La validación recalculada coincide con la evidencia guardada: "
                    f"{current_validation.get('errors', 0)} errores y "
                    f"{current_validation.get('warnings', 0)} advertencias."
                )
            ),
        },
        {
            "code": "proposal.replay",
            "label": "Reproducción determinística del contrato",
            "passed": deterministic_replay if same_engine_version else False,
            "detail": (
                (
                    "La reproducción exacta no es comparable porque la propuesta pertenece "
                    f"a {proposal_prompt_version} y el motor actual es {PROMPT_VERSION}."
                )
                if not same_engine_version
                else (
                    "Las decisiones persistidas reconstruyen exactamente el mismo contrato."
                    if deterministic_replay
                    else "El contrato no pudo reconstruirse de forma idéntica."
                )
            ),
        },
    ]
    return {
        "verified": approval_safe,
        "approval_safe": approval_safe,
        "compatibility_warning": compatibility_warning,
        "checks": checks,
        "snapshot_hash": snapshot_hash,
        "proposal_hash": canonical_hash(proposal_document),
        "replay_hash": replay_hash,
        "validated_reference_count": validated_reference_count,
        "rejected_reference_count": rejected_reference_count,
        "validation_errors": int(current_validation.get("errors", 0)),
        "validation_warnings": int(current_validation.get("warnings", 0)),
        "pending_validations": [
            (
                "Contraste de cifras mediante consultas de referencia después de "
                "materializar el datamart."
            ),
            "Evaluación formal de utilidad mediante juicio de expertos.",
            "MAPE y RMSE cuando se implemente el pronóstico de ventas.",
        ],
    }


def metadata_tables(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for schema in document.get("schemas", []):
        if not isinstance(schema, dict):
            continue
        schema_name = str(schema.get("name", ""))
        for table in schema.get("tables", []):
            if not isinstance(table, dict):
                continue
            name = str(table.get("name", ""))
            result[f"{schema_name}.{name}"] = table
    return result


def compact_metadata_blocks(
    document: dict[str, Any], business_request: dict[str, Any], max_items: int
) -> list[dict[str, Any]]:
    tables = metadata_tables(document)
    selected_references = _discovery_references(tables, business_request)
    compact: list[dict[str, Any]] = []
    for reference in selected_references:
        table = tables[reference]
        compact.append(
            {
                "ref": reference,
                "columns": _compact_columns(table),
                "foreign_keys": [
                    {
                        "columns": relation.get("columns", []),
                        "target": (
                            f"{relation.get('referenced_schema', '')}."
                            f"{relation.get('referenced_table', '')}"
                        ),
                        "target_columns": relation.get("referenced_columns", []),
                    }
                    for relation in table.get("foreign_keys", [])
                    if isinstance(relation, dict)
                ],
            }
        )
    size = max(1, max_items)
    return [
        {
            "task": "discover_sales_semantics",
            "contract_version": CONTRACT_VERSION,
            "business_request": business_request,
            "metadata": compact[index : index + size],
        }
        for index in range(0, len(compact), size)
    ]


def _search_tokens(value: object) -> set[str]:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(value))
    return {token for token in re.findall(r"[a-záéíóúñ0-9]+", text.casefold()) if len(token) >= 3}


def _compact_columns(table: dict[str, Any], limit: int = 8) -> list[dict[str, object]]:
    foreign_key_columns = {
        str(column)
        for relation in table.get("foreign_keys", [])
        if isinstance(relation, dict)
        for column in relation.get("columns", [])
    }
    descriptive_terms = {"name", "nombre", "description", "descripcion", "code", "number"}
    ranked: list[tuple[int, int, dict[str, object]]] = []
    for position, column in enumerate(table.get("columns", [])):
        if not isinstance(column, dict):
            continue
        name = str(column.get("name", ""))
        data_type = str(column.get("data_type", ""))
        tokens = _search_tokens(name)
        score = (
            (20 if bool(column.get("primary_key", False)) else 0)
            + (16 if name in foreign_key_columns else 0)
            + 6 * len(tokens & SALES_PROFILE.discovery_terms)
            + 10 * len(tokens & descriptive_terms)
            + (1 if re.search(r"int|decimal|numeric|money|date|time", data_type.casefold()) else 0)
        )
        ranked.append(
            (
                -score,
                position,
                {
                    "name": name,
                    "type": data_type,
                    "pk": bool(column.get("primary_key", False)),
                    "nullable": bool(column.get("nullable", False)),
                },
            )
        )
    selected = sorted(ranked)[:limit]
    return [item for _, _, item in sorted(selected, key=lambda entry: entry[1])]


def _discovery_references(
    tables: dict[str, dict[str, Any]], business_request: dict[str, Any]
) -> list[str]:
    """Create a bounded, domain-aware shortlist before invoking the LLM.

    This keeps local models responsive without choosing a dimensional model for them:
    the LLM still interprets the shortlisted technical metadata and the deterministic
    validator remains the authority for every returned reference.
    """
    scope_limit = SALES_PROFILE.discovery_scope_max_tables
    if len(tables) <= scope_limit:
        return sorted(tables)
    request_tokens = _search_tokens(business_request)
    search_terms = request_tokens | set(SALES_PROFILE.discovery_terms)
    scores: dict[str, int] = {}
    for reference, table in tables.items():
        reference_tokens = _search_tokens(reference)
        column_tokens = {
            token
            for column in table.get("columns", [])
            if isinstance(column, dict)
            for token in _search_tokens(column.get("name", ""))
        }
        scores[reference] = (
            5 * len(reference_tokens & search_terms)
            + 8 * len(reference_tokens & request_tokens)
            + len(column_tokens & search_terms)
            + (
                6
                if {"sales", "venta", "ventas"} & reference_tokens
                and {"order", "pedido", "detail", "line"} & reference_tokens
                else 0
            )
            - 10 * len(reference_tokens & SALES_PROFILE.deprioritized_terms)
        )
    ranked = sorted(tables, key=lambda ref: (-scores[ref], ref))
    requested_dimensions = {
        str(value).casefold() for value in business_request.get("requested_dimensions", [])
    }
    selected: list[str] = []
    for dimension in sorted(requested_dimensions):
        matching = [reference for reference in ranked if dimension in _search_tokens(reference)]
        if matching:
            best = min(matching, key=lambda ref: (len(_search_tokens(ref)), -scores[ref], ref))
            if best not in selected:
                selected.append(best)
    for reference in ranked:
        if reference not in selected:
            selected.append(reference)
        if len(selected) >= scope_limit:
            break
    return selected[:scope_limit]


def validated_semantic_candidates(
    responses: list[dict[str, Any]], document: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    existing = metadata_tables(document)
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for response in responses:
        for raw in response.get("candidates", []):
            if not isinstance(raw, dict):
                continue
            references = raw.get("technical_refs", [])
            if not isinstance(references, list) or not references:
                rejected.append(
                    _issue(
                        "semantic.missing_reference",
                        "warning",
                        "semantic_mapping",
                        "Se descartó un concepto sin origen técnico.",
                    )
                )
                continue
            normalized = [str(item) for item in references]
            unknown = [item for item in normalized if item not in existing]
            if unknown:
                rejected.append(
                    _issue(
                        "semantic.unknown_reference",
                        "warning",
                        "semantic_mapping",
                        f"Se descartó una referencia inexistente: {unknown[0]}.",
                    )
                )
                continue
            key = (str(raw.get("business_concept", "")).casefold(), tuple(sorted(normalized)))
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "business_concept": str(raw.get("business_concept", "concepto"))[:80],
                    "business_name_es": str(raw.get("business_name_es", "Concepto de negocio"))[
                        :160
                    ],
                    "description_es": str(raw.get("description_es", ""))[:500],
                    "technical_refs": normalized,
                    "confidence": str(raw.get("confidence", "low"))
                    if str(raw.get("confidence", "low")) in {"high", "medium", "low"}
                    else "low",
                    "reason": str(raw.get("reason", ""))[:500],
                    "references_validated": True,
                }
            )
    return {
        "contract_version": CONTRACT_VERSION,
        "candidates": candidates,
        "rejected_references": rejected,
    }, rejected


def derived_scope(document: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    tables = metadata_tables(document)
    selected = list(
        dict.fromkeys(
            reference
            for candidate in semantic_map.get("candidates", [])
            for reference in candidate.get("technical_refs", [])
            if reference in tables
        )
    )
    selected_set = set(selected)
    graph: dict[str, set[str]] = {reference: set() for reference in tables}
    for source, table in tables.items():
        for relation in table.get("foreign_keys", []):
            if not isinstance(relation, dict):
                continue
            target = (
                f"{relation.get('referenced_schema', '')}.{relation.get('referenced_table', '')}"
            )
            if target in tables:
                graph[source].add(target)
                graph[target].add(source)

    def shortest_path(start: str, destination: str) -> list[str]:
        queue: list[tuple[str, list[str]]] = [(start, [start])]
        visited = {start}
        while queue:
            current, path = queue.pop(0)
            if current == destination:
                return path
            for neighbor in sorted(graph[current]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, [*path, neighbor]))
        return []

    expanded_order = list(selected)
    if selected:
        root = selected[0]
        for destination in selected[1:]:
            for reference in shortest_path(root, destination):
                if reference not in expanded_order:
                    expanded_order.append(reference)
    expanded = set(expanded_order[:PROPOSAL_SCOPE_MAX_TABLES])
    outbound_neighbors: set[str] = set()
    for reference in selected:
        for relation in tables[reference].get("foreign_keys", []):
            if not isinstance(relation, dict):
                continue
            target = (
                f"{relation.get('referenced_schema', '')}.{relation.get('referenced_table', '')}"
            )
            if target in tables:
                outbound_neighbors.add(target)
    ranked_neighbors = sorted(
        outbound_neighbors - expanded,
        key=lambda ref: (
            -len(_search_tokens(ref) & SALES_PROFILE.discovery_terms),
            ref,
        ),
    )
    expanded.update(ranked_neighbors[: max(0, PROPOSAL_SCOPE_MAX_TABLES - len(expanded))])
    # Never discard an LLM candidate merely because a connector path consumed the limit.
    expanded.update(selected_set)
    scope_tables = []
    for reference in sorted(expanded):
        table = tables[reference]
        scope_tables.append(
            {
                "ref": reference,
                "columns": _compact_columns(table, limit=12),
                "foreign_keys": table.get("foreign_keys", []),
            }
        )
    return {"origin": "semantic-discovery:v1", "tables": scope_tables}


def proposal_payload(
    snapshot_hash: str,
    connector: str,
    business_request: dict[str, Any],
    scope: dict[str, Any],
    semantic_map: dict[str, Any],
) -> dict[str, Any]:
    return {
        "request_version": CONTRACT_VERSION,
        "language": "es",
        "task": "propose_sales_dimensional_model",
        "source": {"connector": connector, "snapshot_hash": snapshot_hash},
        "business_request": business_request,
        "semantic_map": semantic_map.get("candidates", []),
        "scope": scope,
        "constraints": {
            "no_sql": True,
            "human_approval_required": True,
            "allowed_etl_operations": sorted(ALLOWED_OPERATIONS),
            "technical_names_must_exist": True,
        },
    }


def _semantic_role(value: dict[str, Any], source_column: str = "") -> str:
    """Resolve a provider-declared role with a backwards-compatible deterministic fallback."""
    declared = str(value.get("semantic_role", ""))
    if declared in SEMANTIC_ROLES:
        return declared
    tokens = _search_tokens(
        {
            "name": value.get("name", ""),
            "code": value.get("code", ""),
            "column": source_column,
        }
    )
    aggregation = str(value.get("aggregation", value.get("operation", "")))
    if tokens & {"customer", "customers", "cliente", "clientes"}:
        return "customer_count"
    if tokens & {"quantity", "qty", "cantidad", "unidades", "units"}:
        return "quantity"
    if tokens & {"amount", "total", "sales", "venta", "ventas", "importe", "monto"}:
        return "sales_amount"
    if aggregation in {"count", "count_distinct"}:
        return "transaction_count"
    return "sales_amount"


def _measure_candidates_for_role(role: str, fact_columns: list[dict[str, Any]]) -> list[str]:
    role_terms = {
        "sales_amount": {"amount", "total", "line", "sales", "importe", "monto"},
        "quantity": {"qty", "quantity", "cantidad", "unidades", "units"},
        "customer_count": {"customer", "cliente", "account"},
        "transaction_count": {"order", "sale", "venta", "transaction", "pedido"},
    }
    terms = role_terms.get(role, set())
    candidates: list[str] = []
    for column in fact_columns:
        name = str(column["name"])
        tokens = _search_tokens(name)
        identifier_like = (
            bool(column.get("pk"))
            or name.casefold().endswith("id")
            or bool(tokens & {"code", "codigo", "key", "number", "numero"})
        )
        if role in {"sales_amount", "quantity"} and identifier_like:
            continue
        if tokens & terms:
            candidates.append(name)
    return candidates


def _column_supports_role(role: str, column: str) -> bool:
    tokens = _search_tokens(column)
    required_terms = {
        "sales_amount": {"amount", "total", "line", "sales", "importe", "monto"},
        "quantity": {"qty", "quantity", "cantidad", "unidades", "units"},
        "customer_count": {"customer", "cliente", "account", "person", "store"},
        "transaction_count": {"order", "sale", "sales", "venta", "transaction", "pedido"},
    }
    return bool(tokens & required_terms.get(role, set()))


def expand_proposal_blueprint(
    blueprint: dict[str, Any],
    scope: dict[str, Any],
    semantic_map: dict[str, Any],
) -> dict[str, Any]:
    """Expand compact AI decisions into a deterministic, auditable proposal contract."""
    scoped = {
        str(item.get("ref")): item
        for item in scope.get("tables", [])
        if isinstance(item, dict) and item.get("ref")
    }
    fact_source = str(blueprint.get("fact_source", ""))
    fact_table = scoped.get(fact_source, {})
    fact_columns = [
        item
        for item in fact_table.get("columns", [])
        if isinstance(item, dict) and item.get("name")
    ]
    business_keys = [str(item["name"]) for item in fact_columns if bool(item.get("pk", False))]
    if not business_keys and fact_columns:
        business_keys = [str(fact_columns[0]["name"])]

    automatic_adjustments: list[str] = []
    proposal_warnings: list[str] = []
    measures: list[dict[str, Any]] = []
    for item in blueprint.get("measures", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "medida_ventas"))
        proposed_column = str(item.get("source_column", ""))
        role = _semantic_role(item, proposed_column)
        candidates = _measure_candidates_for_role(role, fact_columns)
        source_column = proposed_column
        if candidates and proposed_column not in candidates:
            source_column = max(
                candidates,
                key=lambda column: (
                    len(_search_tokens(column)),
                    "total" in _search_tokens(column),
                    column,
                ),
            )
            automatic_adjustments.append(
                f"La medida {name} se ajustó de {proposed_column} a {source_column} "
                "según su significado de negocio."
            )
        aggregation = str(item.get("aggregation", "sum"))
        if aggregation not in ROLE_AGGREGATIONS[role]:
            adjusted_aggregation = ROLE_DEFAULT_AGGREGATION[role]
            automatic_adjustments.append(
                f"La agregación de {name} se ajustó de {aggregation} a "
                f"{adjusted_aggregation} según su función semántica."
            )
            aggregation = adjusted_aggregation
        measures.append(
            {
                "name": name,
                "source_columns": [source_column],
                "aggregation": aggregation,
                "semantic_role": role,
            }
        )
    dimension_terms = {
        "dim_producto": {"product", "producto"},
        "dim_cliente": {"customer", "person", "store", "cliente"},
        "dim_territorio": {"territory", "region", "territorio"},
        "dim_fecha": {"date", "calendar", "fecha"},
    }
    chosen_dimensions: dict[str, tuple[int, dict[str, Any]]] = {}
    for item in blueprint.get("dimensions", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", ""))
        source = str(item.get("source_table", ""))
        if not name:
            continue
        score = 10 * len(_search_tokens(source) & dimension_terms.get(name, set()))
        if source == fact_source:
            score -= 5
        previous = chosen_dimensions.get(name)
        if previous is None or score > previous[0]:
            chosen_dimensions[name] = (score, item)

    dimensions: list[dict[str, Any]] = []

    def dimension_source_score(name: str, reference: str) -> tuple[int, int, str]:
        terms = dimension_terms.get(name, set())
        table_token = reference.rsplit(".", 1)[-1].casefold()
        reference_tokens = _search_tokens(reference)
        columns = scoped[reference].get("columns", [])
        column_matches = sum(
            bool(_search_tokens(column.get("name", "")) & terms)
            for column in columns
            if isinstance(column, dict)
        )
        score = (
            (100 if table_token in terms else 0)
            + 30 * len(reference_tokens & terms)
            + 8 * column_matches
            - len(reference_tokens)
        )
        if name == "dim_fecha":
            transaction_date = any(
                (_search_tokens(column.get("name", "")) & {"date", "fecha"})
                and (_search_tokens(column.get("name", "")) & {"order", "sale", "venta"})
                for column in columns
                if isinstance(column, dict)
            )
            score += 80 if transaction_date else 0
            score += 20 * len(reference_tokens & {"order", "sale", "sales", "venta"})
        return score, -len(reference), reference

    requested_destinations = {
        destination
        for code, destination in SALES_PROFILE.dimension_destinations
        if code in set(blueprint.get("requested_dimensions", []))
    }
    for name in sorted(requested_destinations - set(chosen_dimensions)):
        ranked_sources = sorted(
            scoped,
            key=lambda reference: dimension_source_score(name, reference),
            reverse=True,
        )
        if not ranked_sources:
            continue
        source = ranked_sources[0]
        score = dimension_source_score(name, source)[0]
        if score <= 0:
            continue
        chosen_dimensions[name] = (score, {"name": name, "source_table": source})
        automatic_adjustments.append(
            f"La dimensión solicitada {name} se incorporó desde {source} "
            "porque la fuente fue comprobada en los metadatos."
        )

    for _, item in chosen_dimensions.values():
        name = str(item.get("name", ""))
        proposed_source = str(item.get("source_table", ""))
        source = max(scoped, key=lambda ref: dimension_source_score(name, ref))
        if source != proposed_source:
            automatic_adjustments.append(
                f"La fuente de {name} se ajustó de {proposed_source} a {source} "
                "según los metadatos verificados."
            )
        table = scoped.get(source, {})
        columns = [
            column
            for column in table.get("columns", [])
            if isinstance(column, dict) and column.get("name")
        ]
        keys = [str(column["name"]) for column in columns if bool(column.get("pk", False))]
        if name == "dim_fecha":
            date_columns = [
                str(column["name"])
                for column in columns
                if _search_tokens(column.get("name", "")) & dimension_terms[name]
            ]
            business_key = date_columns[0] if date_columns else (keys[0] if keys else "")
        else:
            business_key = keys[0] if keys else (str(columns[0]["name"]) if columns else "")
        attributes = [
            str(column["name"]) for column in columns if str(column["name"]) != business_key
        ][:4]
        dimensions.append(
            {
                "name": name,
                "source_tables": [source],
                "business_key": business_key,
                "attributes": attributes,
            }
        )

    joins: list[dict[str, Any]] = []
    for source, table in scoped.items():
        for relation in table.get("foreign_keys", []):
            if not isinstance(relation, dict):
                continue
            target = (
                f"{relation.get('referenced_schema', '')}.{relation.get('referenced_table', '')}"
            )
            if target not in scoped:
                continue
            joins.append(
                {
                    "left_table": source,
                    "right_table": target,
                    "left_columns": list(relation.get("columns", [])),
                    "right_columns": list(relation.get("referenced_columns", [])),
                }
            )
            if len(joins) >= 6:
                break
        if len(joins) >= 6:
            break

    kpis: list[dict[str, Any]] = []
    decision_diagnostics: list[dict[str, Any]] = []
    for item in blueprint.get("kpis", []):
        if not isinstance(item, dict):
            continue
        raw_index = item.get("measure_index", 0)
        index = raw_index if isinstance(raw_index, int) else 0
        measure = measures[min(max(index, 0), len(measures) - 1)] if measures else {}
        measure_name = str(measure.get("name", ""))
        measure_role = str(measure.get("semantic_role", ""))
        kpi_role = _semantic_role(item)
        compatible_measures = [
            str(candidate["name"])
            for candidate in measures
            if candidate.get("semantic_role") == kpi_role
        ]
        if not measure_name or measure_role != kpi_role:
            reason = (
                f"El KPI {item.get('name', 'sin nombre')} fue excluido porque la medida "
                f"{measure_name or 'seleccionada'} no representa {kpi_role}."
            )
            proposal_warnings.append(reason)
            decision_diagnostics.append(
                {
                    "kind": "kpi",
                    "code": str(item.get("code", "")),
                    "status": "excluded",
                    "reason": reason,
                    "compatible_measures": compatible_measures,
                }
            )
            continue
        operation = str(item.get("operation", measure.get("aggregation", "sum")))
        if operation not in ROLE_AGGREGATIONS[kpi_role]:
            adjusted_operation = str(measure.get("aggregation"))
            automatic_adjustments.append(
                f"La operación del KPI {item.get('name', 'sin nombre')} se ajustó de "
                f"{operation} a {adjusted_operation} según su función semántica."
            )
            operation = adjusted_operation
        kpis.append(
            {
                "code": str(item.get("code", "kpi_ventas")),
                "name": str(item.get("name", "Indicador de ventas")),
                "formula": {
                    "operation": operation,
                    "measure": measure_name,
                },
                "unit": str(item.get("unit", "valor")),
                "semantic_role": kpi_role,
            }
        )
        decision_diagnostics.append(
            {
                "kind": "kpi",
                "code": str(item.get("code", "")),
                "status": "included",
                "reason": "La función del KPI y la medida son compatibles.",
                "compatible_measures": compatible_measures,
            }
        )

    included_destinations = {str(item.get("name", "")) for item in dimensions}
    for missing in sorted(requested_destinations - included_destinations):
        proposal_warnings.append(
            f"La dimensión solicitada {missing} no pudo incorporarse con el alcance verificado."
        )
    sources = list(scoped)
    etl_plan: list[dict[str, Any]] = [
        {
            "order": 1,
            "operation": "extract",
            "inputs": sources,
            "output": "stg_ventas_fuente",
            "description": "Extraer únicamente columnas incluidas en la propuesta aprobada.",
        }
    ]
    if joins:
        etl_plan.append(
            {
                "order": 2,
                "operation": "join",
                "inputs": ["stg_ventas_fuente"],
                "output": "stg_ventas_integrada",
                "description": "Relacionar fuentes sólo mediante claves foráneas verificadas.",
            }
        )
    etl_plan.extend(
        [
            {
                "order": len(etl_plan) + 1,
                "operation": "derive",
                "inputs": [etl_plan[-1]["output"]],
                "output": "stg_ventas_transformada",
                "description": "Preparar claves y medidas declaradas sin ejecutar SQL libre.",
            },
            {
                "order": len(etl_plan) + 2,
                "operation": "load",
                "inputs": ["stg_ventas_transformada"],
                "output": "dimensiones_ventas",
                "description": "Cargar dimensiones después de superar controles de calidad.",
            },
            {
                "order": len(etl_plan) + 3,
                "operation": "load",
                "inputs": ["stg_ventas_transformada", "dimensiones_ventas"],
                "output": "fact_ventas",
                "description": "Cargar el hecho al final para conservar integridad referencial.",
            },
        ]
    )
    summary = str(blueprint.get("summary", "Propuesta dimensional de ventas."))
    return {
        "contract_version": CONTRACT_VERSION,
        "domain": SALES_PROFILE.code,
        "summary": summary,
        "business_explanation": (
            f"{summary} La aplicación expandió y validó las decisiones técnicas del copiloto."
        ),
        "semantic_mapping": semantic_map.get("candidates", []),
        "grain": {
            "description": str(
                blueprint.get("grain_description", "Una fila por transacción de venta.")
            ),
            "source_tables": [fact_source],
        },
        "fact": {
            "name": "fact_ventas",
            "source_tables": [fact_source],
            "business_keys": business_keys[:4],
            "measures": measures,
        },
        "dimensions": dimensions,
        "joins": joins,
        "kpis": kpis,
        "etl_plan": etl_plan,
        "quality_rules": [
            "Las claves de negocio no deben estar vacías.",
            "Las relaciones deben coincidir con claves foráneas de la instantánea.",
            "Los importes y cantidades deben conservar su tipo y signo de origen.",
        ],
        "assumptions": list(blueprint.get("assumptions", [])),
        "warnings": proposal_warnings,
        "automatic_adjustments": automatic_adjustments,
        "provider_observations": list(blueprint.get("warnings", [])),
        "decision_diagnostics": decision_diagnostics,
        "ai_decisions": blueprint,
    }


def apply_analyst_adjustments(
    source_blueprint: dict[str, Any], adjustments: dict[str, Any]
) -> dict[str, Any]:
    """Create a bounded blueprint revision using only choices from the source proposal."""
    blueprint = deepcopy(source_blueprint)
    if not blueprint:
        raise ValueError("La propuesta de origen no conserva decisiones ajustables.")

    blueprint["summary"] = str(adjustments.get("summary", "")).strip()
    blueprint["grain_description"] = str(adjustments.get("grain_description", "")).strip()

    source_dimensions = {
        str(item.get("name")): item
        for item in blueprint.get("dimensions", [])
        if isinstance(item, dict) and item.get("name")
    }
    requested_dimensions = list(adjustments.get("dimension_names", []))
    if not requested_dimensions or not set(requested_dimensions).issubset(source_dimensions):
        raise ValueError("Seleccione únicamente dimensiones incluidas en la propuesta de origen.")
    blueprint["dimensions"] = [deepcopy(source_dimensions[name]) for name in requested_dimensions]

    source_measures = [
        item
        for item in blueprint.get("measures", [])
        if isinstance(item, dict) and item.get("name")
    ]
    measures_by_name = {
        str(item["name"]): (index, item) for index, item in enumerate(source_measures)
    }
    requested_measures = list(adjustments.get("measure_names", []))
    if not requested_measures or not set(requested_measures).issubset(measures_by_name):
        raise ValueError("Seleccione únicamente medidas incluidas en la propuesta de origen.")
    aggregation_changes = adjustments.get("measure_aggregations", {})
    selected_measures: list[dict[str, Any]] = []
    index_map: dict[int, int] = {}
    for new_index, name in enumerate(requested_measures):
        old_index, source_measure = measures_by_name[name]
        measure = deepcopy(source_measure)
        if name in aggregation_changes:
            measure["aggregation"] = aggregation_changes[name]
        selected_measures.append(measure)
        index_map[old_index] = new_index
    blueprint["measures"] = selected_measures

    source_kpis = {
        str(item.get("code")): item
        for item in blueprint.get("kpis", [])
        if isinstance(item, dict) and item.get("code")
    }
    requested_kpis = list(adjustments.get("kpi_codes", []))
    if not requested_kpis or not set(requested_kpis).issubset(source_kpis):
        raise ValueError("Seleccione únicamente KPIs incluidos en la propuesta de origen.")
    selected_kpis: list[dict[str, Any]] = []
    kpi_measure_names = adjustments.get("kpi_measure_names", {})
    for code in requested_kpis:
        kpi = deepcopy(source_kpis[code])
        requested_measure = str(kpi_measure_names.get(code, ""))
        old_index = kpi.get("measure_index", 0)
        if requested_measure:
            if (
                requested_measure not in measures_by_name
                or requested_measure not in requested_measures
            ):
                raise ValueError(
                    f"El KPI {code} sólo puede asociarse a una medida seleccionada y verificada."
                )
            source_index = measures_by_name[requested_measure][0]
        elif isinstance(old_index, int):
            source_index = old_index
        else:
            source_index = -1
        if source_index not in index_map:
            raise ValueError(
                f"El KPI {code} depende de una medida que fue retirada de la revisión."
            )
        kpi_role = _semantic_role(kpi)
        selected_measure = source_measures[source_index]
        measure_role = _semantic_role(
            selected_measure,
            str(selected_measure.get("source_column", "")),
        )
        if kpi_role != measure_role:
            raise ValueError(
                f"El KPI {code} no es compatible con la medida {selected_measure.get('name')}."
            )
        kpi["measure_index"] = index_map[source_index]
        selected_kpis.append(kpi)
    blueprint["kpis"] = selected_kpis
    return blueprint


def _issue(code: str, level: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "level": level, "path": path, "message": message}


def validate_proposal(
    proposal: dict[str, Any], scope: dict[str, Any], document: dict[str, Any]
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    all_tables = metadata_tables(document)
    scoped = {
        str(item.get("ref")): item for item in scope.get("tables", []) if isinstance(item, dict)
    }
    if proposal.get("contract_version") != CONTRACT_VERSION:
        issues.append(
            _issue(
                "contract.version",
                "error",
                "contract_version",
                "La versión del contrato no es compatible.",
            )
        )
    if proposal.get("domain") != SALES_PROFILE.code:
        issues.append(
            _issue(
                "domain.invalid",
                "error",
                "domain",
                "La propuesta debe limitarse al dominio de ventas.",
            )
        )
    if not str(proposal.get("business_explanation", "")).strip():
        issues.append(
            _issue(
                "explanation.missing",
                "error",
                "business_explanation",
                "Falta la explicación de negocio en español.",
            )
        )
    serialized = json.dumps(proposal, ensure_ascii=False).casefold()
    if re.search(r"\b(select|insert|update|delete|drop|alter|create)\b", serialized):
        issues.append(
            _issue(
                "executable.detected",
                "error",
                "$",
                "La propuesta contiene una instrucción ejecutable no permitida.",
            )
        )

    def check_table(reference: object, path: str) -> None:
        value = str(reference)
        if value not in all_tables:
            issues.append(
                _issue(
                    "reference.table_unknown",
                    "error",
                    path,
                    f"La tabla {value} no existe en la instantánea.",
                )
            )
        elif value not in scoped:
            issues.append(
                _issue(
                    "reference.table_out_of_scope",
                    "error",
                    path,
                    f"La tabla {value} está fuera del alcance validado.",
                )
            )

    grain = proposal.get("grain")
    if not isinstance(grain, dict) or not str(grain.get("description", "")).strip():
        issues.append(
            _issue(
                "grain.missing",
                "error",
                "grain",
                "La propuesta no define la granularidad del hecho.",
            )
        )
    elif isinstance(grain.get("source_tables"), list):
        for index, table in enumerate(grain["source_tables"]):
            check_table(table, f"grain.source_tables.{index}")

    fact = proposal.get("fact")
    measures: set[str] = set()
    measure_semantics: dict[str, tuple[str, str]] = {}
    fact_sources: list[str] = []
    if not isinstance(fact, dict) or fact.get("name") != "fact_ventas":
        issues.append(
            _issue(
                "fact.invalid",
                "error",
                "fact",
                "La propuesta debe definir un único hecho fact_ventas.",
            )
        )
    else:
        fact_sources = [str(item) for item in fact.get("source_tables", [])]
        if not fact_sources:
            issues.append(
                _issue(
                    "fact.sources_missing",
                    "error",
                    "fact.source_tables",
                    "El hecho no tiene tablas fuente.",
                )
            )
        for index, table in enumerate(fact_sources):
            check_table(table, f"fact.source_tables.{index}")
        raw_measures = fact.get("measures", [])
        if not isinstance(raw_measures, list) or not raw_measures:
            issues.append(
                _issue(
                    "measure.missing", "error", "fact.measures", "La propuesta no contiene medidas."
                )
            )
        else:
            for index, measure in enumerate(raw_measures):
                if not isinstance(measure, dict):
                    issues.append(
                        _issue(
                            "measure.invalid",
                            "error",
                            f"fact.measures.{index}",
                            "La medida no tiene la estructura esperada.",
                        )
                    )
                    continue
                name = str(measure.get("name", ""))
                if name:
                    measures.add(name)
                aggregation = str(measure.get("aggregation", ""))
                if aggregation not in ALLOWED_AGGREGATIONS:
                    issues.append(
                        _issue(
                            "measure.aggregation",
                            "error",
                            f"fact.measures.{index}.aggregation",
                            "La agregación no está permitida.",
                        )
                    )
                source_columns = measure.get("source_columns", [])
                source_column = (
                    str(source_columns[0])
                    if isinstance(source_columns, list) and source_columns
                    else ""
                )
                role = _semantic_role(measure, source_column)
                measure_semantics[name] = (role, aggregation)
                if source_column and not _column_supports_role(role, source_column):
                    issues.append(
                        _issue(
                            "measure.semantic_source",
                            "error",
                            f"fact.measures.{index}.source_columns",
                            (
                                f"La columna {source_column} no es compatible con la función "
                                f"semántica {role} declarada para la medida {name}."
                            ),
                        )
                    )
                if aggregation not in ROLE_AGGREGATIONS[role]:
                    issues.append(
                        _issue(
                            "measure.semantic_aggregation",
                            "error",
                            f"fact.measures.{index}.aggregation",
                            (
                                f"La agregación {aggregation} no es compatible con la función "
                                f"semántica {role} de la medida {name}."
                            ),
                        )
                    )
                columns = measure.get("source_columns", [])
                available = {
                    str(column.get("name"))
                    for table_ref in fact_sources
                    for column in scoped.get(table_ref, {}).get("columns", [])
                    if isinstance(column, dict)
                }
                for column in columns if isinstance(columns, list) else []:
                    if str(column) not in available:
                        issues.append(
                            _issue(
                                "reference.column_unknown",
                                "error",
                                f"fact.measures.{index}.source_columns",
                                f"La columna {column} no existe en las fuentes del hecho.",
                            )
                        )

    dimensions = proposal.get("dimensions", [])
    if not isinstance(dimensions, list):
        issues.append(
            _issue(
                "dimensions.invalid",
                "error",
                "dimensions",
                "Las dimensiones no tienen la estructura esperada.",
            )
        )
    else:
        for index, dimension in enumerate(dimensions):
            if not isinstance(dimension, dict):
                continue
            if dimension.get("name") not in ALLOWED_DESTINATIONS - {"fact_ventas"}:
                issues.append(
                    _issue(
                        "dimension.name",
                        "error",
                        f"dimensions.{index}.name",
                        "La dimensión destino no pertenece al alcance aprobado.",
                    )
                )
            source_tables = [str(item) for item in dimension.get("source_tables", [])]
            for table in source_tables:
                check_table(table, f"dimensions.{index}.source_tables")
            available = {
                str(column.get("name"))
                for table_ref in source_tables
                for column in scoped.get(table_ref, {}).get("columns", [])
                if isinstance(column, dict)
            }
            for column in [dimension.get("business_key"), *dimension.get("attributes", [])]:
                if column and str(column) not in available:
                    issues.append(
                        _issue(
                            "reference.column_unknown",
                            "error",
                            f"dimensions.{index}",
                            f"La columna {column} no existe en la dimensión propuesta.",
                        )
                    )

    declared_relations = set()
    for source, table in all_tables.items():
        for relation in table.get("foreign_keys", []):
            if not isinstance(relation, dict):
                continue
            target = (
                f"{relation.get('referenced_schema', '')}.{relation.get('referenced_table', '')}"
            )
            declared_relations.add(
                (
                    source,
                    target,
                    tuple(relation.get("columns", [])),
                    tuple(relation.get("referenced_columns", [])),
                )
            )
            declared_relations.add(
                (
                    target,
                    source,
                    tuple(relation.get("referenced_columns", [])),
                    tuple(relation.get("columns", [])),
                )
            )
    for index, join in enumerate(proposal.get("joins", [])):
        if not isinstance(join, dict):
            continue
        relation = (
            str(join.get("left_table")),
            str(join.get("right_table")),
            tuple(join.get("left_columns", [])),
            tuple(join.get("right_columns", [])),
        )
        if relation not in declared_relations:
            issues.append(
                _issue(
                    "join.not_declared",
                    "error",
                    f"joins.{index}",
                    "La unión no corresponde a una clave foránea declarada.",
                )
            )

    kpis = proposal.get("kpis", [])
    if not isinstance(kpis, list) or not kpis:
        issues.append(
            _issue("kpi.missing", "error", "kpis", "La propuesta debe incluir al menos un KPI.")
        )
    else:
        for index, kpi in enumerate(kpis):
            formula = kpi.get("formula", {}) if isinstance(kpi, dict) else {}
            if (
                formula.get("operation") not in ALLOWED_AGGREGATIONS
                or formula.get("measure") not in measures
            ):
                issues.append(
                    _issue(
                        "kpi.formula",
                        "error",
                        f"kpis.{index}.formula",
                        "El KPI no referencia una medida y operación válidas.",
                    )
                )
                continue
            measure_name = str(formula.get("measure", ""))
            measure_role, _ = measure_semantics.get(measure_name, ("", ""))
            kpi_role = _semantic_role(
                kpi if isinstance(kpi, dict) else {},
            )
            operation = str(formula.get("operation", ""))
            if kpi_role != measure_role:
                issues.append(
                    _issue(
                        "kpi.semantic_mismatch",
                        "error",
                        f"kpis.{index}.formula",
                        (
                            f"El KPI {kpi.get('name', 'sin nombre')} representa {kpi_role}, "
                            f"pero su medida {measure_name} representa {measure_role}."
                        ),
                    )
                )
            if operation not in ROLE_AGGREGATIONS.get(kpi_role, set()):
                issues.append(
                    _issue(
                        "kpi.semantic_operation",
                        "error",
                        f"kpis.{index}.formula.operation",
                        (
                            f"La operación {operation} no es compatible con la función "
                            f"semántica {kpi_role} del KPI."
                        ),
                    )
                )

    plan = proposal.get("etl_plan", [])
    if not isinstance(plan, list) or not plan:
        issues.append(_issue("etl.missing", "error", "etl_plan", "Falta el plan ETL declarativo."))
    else:
        for index, step in enumerate(plan):
            if not isinstance(step, dict) or step.get("operation") not in ALLOWED_OPERATIONS:
                issues.append(
                    _issue(
                        "etl.operation",
                        "error",
                        f"etl_plan.{index}",
                        "El plan contiene una operación no permitida.",
                    )
                )

    for warning in proposal.get("warnings", []):
        issues.append(_issue("proposal.warning", "warning", "warnings", str(warning)[:500]))
    errors = sum(issue["level"] == "error" for issue in issues)
    warnings = sum(issue["level"] == "warning" for issue in issues)
    return {
        "contract_version": CONTRACT_VERSION,
        "valid": errors == 0,
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
    }
