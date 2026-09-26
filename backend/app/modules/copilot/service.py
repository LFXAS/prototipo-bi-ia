from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any

from app.modules.copilot.domains import SALES_PROFILE
from app.modules.copilot.entity_resolution import enrich_dimension_labels

PROMPT_VERSION = "sales-bi-v5"
CONTRACT_VERSION = 1
ALLOWED_OPERATIONS = {"extract", "join", "filter", "derive", "aggregate", "load"}
ALLOWED_AGGREGATIONS = {"sum", "count", "count_distinct", "average", "min", "max"}
ALLOWED_CALCULATED_MEASURE_OPERATIONS = {"multiply", "add", "subtract", "divide"}
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

SEMANTIC_ADVICE_SYSTEM_INSTRUCTION = (
    "Actúas como copiloto de un analista BI dentro de una decisión semántica controlada. "
    "Responde únicamente con el objetivo, el concepto y la evidencia estructural recibida. "
    "No inventes tablas, columnas, relaciones, resultados ni reglas del negocio; no produzcas "
    "SQL y reconoce expresamente cuando la evidencia no permite concluir. Explica en español "
    "para una persona que inicia en BI. Distingue evidencia técnica de una definición que sólo "
    "puede confirmar el negocio. Devuelve exclusivamente el JSON solicitado."
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
    "assumptions y warnings. Sé conciso: hasta seis medidas, cuatro dimensiones, seis uniones, "
    "hasta doce KPI y seis pasos ETL; cada explicación debe tener menos de 160 caracteres."
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


def semantic_advice_response_schema(technical_refs: list[str]) -> dict[str, Any]:
    reference_enum = technical_refs or ["sin_referencia"]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "conclusion",
            "answer_es",
            "evidence",
            "risk_es",
            "include_consequence_es",
            "exclude_consequence_es",
            "recommended_action_es",
            "confidence",
        ],
        "properties": {
            "conclusion": {
                "type": "string",
                "enum": ["include", "exclude", "define_business"],
            },
            "answer_es": {"type": "string", "maxLength": 800},
            "evidence": {
                "type": "array",
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["technical_ref", "detail_es"],
                    "properties": {
                        "technical_ref": {"type": "string", "enum": reference_enum},
                        "detail_es": {"type": "string", "maxLength": 240},
                    },
                },
            },
            "risk_es": {"type": "string", "maxLength": 400},
            "include_consequence_es": {"type": "string", "maxLength": 400},
            "exclude_consequence_es": {"type": "string", "maxLength": 400},
            "recommended_action_es": {"type": "string", "maxLength": 400},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
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
                    "maxItems": 6,
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
            "maxItems": 12,
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
    "Devuelve sólo JSON válido y breve. Selecciona una tabla de hechos, hasta seis medidas, "
    "entre una y cuatro dimensiones y hasta doce KPI. Cada medida directa usa una columna de "
    "la tabla de hechos. Si un importe requiere cálculo por fila, usa calculation_operation "
    "multiply, add, subtract o divide y calculation_inputs con columnas numéricas existentes; "
    "usa direct y una lista vacía cuando no haya cálculo. Nunca inventes una fórmula libre. "
    "Una tasa de descuento no es un importe: para descuento monetario combina, cuando existan "
    "de forma inequívoca, precio por tasa de descuento por cantidad. Prioriza importe, total o "
    "cantidad y no sumes identificadores. Declara "
    "semantic_role en cada medida y KPI usando sales_amount, quantity, customer_count o "
    "transaction_count. Cada KPI usa measure_index=0 para la primera medida o 1 para la segunda "
    "y debe tener el mismo semantic_role que su medida. Un KPI customer_count requiere una "
    "medida customer_count con conteo distinto de un identificador de cliente. CustomerID, "
    "cliente, account, person o store pueden representar clientes; OrderID, SalesOrderID y "
    "transaction no los representan. Si la tabla de hechos elegida no contiene una columna de "
    "cliente compatible, omite la medida y los KPI customer_count. Para transaction_count usa "
    "el identificador del pedido con count_distinct, nunca el identificador del detalle. "
    "Conserva columnas monetarias específicas: precio usa price, descuento usa discount y el "
    "importe de venta usa amount o total. Asocia producto, "
    "cliente y territorio con la tabla técnica cuyo nombre corresponda. No inventes "
    "identificadores. Las explicaciones, resúmenes y nombres de negocio deben estar en español "
    "y no superar 160 caracteres por texto."
)

SEMANTIC_ROLES = {
    "sales_amount",
    "cost_amount",
    "discount_amount",
    "quantity",
    "customer_count",
    "transaction_count",
}
ROLE_AGGREGATIONS = {
    "sales_amount": {"sum", "average", "min", "max"},
    "cost_amount": {"sum", "average", "min", "max"},
    "discount_amount": {"sum", "average", "min", "max"},
    "quantity": {"sum", "average", "min", "max"},
    "customer_count": {"count_distinct"},
    "transaction_count": {"count_distinct"},
}
ROLE_DEFAULT_AGGREGATION = {
    "sales_amount": "sum",
    "cost_amount": "sum",
    "discount_amount": "sum",
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
            for candidate in selected_semantic_candidates(semantic_map)
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
        "discount",
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
    short_text = {"type": "string", "maxLength": 160}
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
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "name",
                        "source_column",
                        "aggregation",
                        "semantic_role",
                        "calculation_operation",
                        "calculation_inputs",
                    ],
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
                        "calculation_operation": {
                            "type": "string",
                            "enum": [
                                "direct",
                                *sorted(ALLOWED_CALCULATED_MEASURE_OPERATIONS),
                            ],
                        },
                        "calculation_inputs": {
                            "type": "array",
                            "maxItems": 4,
                            "items": {"type": "string", "enum": column_enum},
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
                "maxItems": 12,
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
                        "measure_index": {"type": "integer", "minimum": 0, "maximum": 5},
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
        stored_assessment = proposal_document.get("need_assessment")
        if isinstance(stored_assessment, dict):
            replay = apply_financial_requirements(replay, stored_assessment, scope)
            replay["need_assessment"] = deepcopy(stored_assessment)
            replay["requirement_coverage"] = build_requirement_coverage(replay, stored_assessment)
        for revision_key in ("controlled_relation_revision", "analyst_revision"):
            if revision_key in proposal_document:
                replay[revision_key] = deepcopy(proposal_document[revision_key])
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


def _semantic_candidate_evidence(
    references: list[str], existing: dict[str, dict[str, Any]], confidence: str
) -> dict[str, Any]:
    """Build deterministic, human-readable evidence without querying business rows."""
    reference_set = set(references)
    relation_sources: dict[str, list[str]] = {reference: [] for reference in references}
    relation_targets: dict[str, list[str]] = {reference: [] for reference in references}
    for source, table in existing.items():
        for relation in table.get("foreign_keys", []):
            if not isinstance(relation, dict):
                continue
            target = (
                f"{relation.get('referenced_schema', '')}.{relation.get('referenced_table', '')}"
            )
            if source in reference_set and target in existing:
                relation_targets[source].append(target)
            if target in reference_set:
                relation_sources[target].append(source)

    checks: list[dict[str, object]] = []
    for reference in references:
        table = existing[reference]
        columns = [item for item in table.get("columns", []) if isinstance(item, dict)]
        primary_keys = [
            str(item.get("name", ""))
            for item in columns
            if bool(item.get("primary_key", False)) and item.get("name")
        ]
        related = sorted(set(relation_sources[reference] + relation_targets[reference]))
        checks.extend(
            [
                {
                    "code": "reference_exists",
                    "passed": True,
                    "label": "Referencia comprobada",
                    "detail": f"{reference} existe en la instantánea vigente.",
                },
                {
                    "code": "columns_available",
                    "passed": bool(columns),
                    "label": "Estructura disponible",
                    "detail": (
                        f"{len(columns)} columnas detectadas."
                        if columns
                        else "No se detectaron columnas utilizables."
                    ),
                },
                {
                    "code": "business_key_available",
                    "passed": bool(primary_keys),
                    "label": "Clave identificadora",
                    "detail": (
                        f"Clave verificada: {', '.join(primary_keys)}."
                        if primary_keys
                        else "No se encontró una clave primaria declarada."
                    ),
                },
                {
                    "code": "relationship_available",
                    "passed": bool(related),
                    "label": "Relación estructural",
                    "detail": (
                        f"Se relaciona con: {', '.join(related[:4])}."
                        if related
                        else "No se encontró una relación declarada con otra tabla."
                    ),
                },
            ]
        )

    structural_checks = [
        item
        for item in checks
        if item["code"] in {"columns_available", "business_key_available", "relationship_available"}
    ]
    structurally_supported = bool(structural_checks) and all(
        bool(item["passed"]) for item in structural_checks
    )
    if confidence == "low":
        status = "decision_required"
        recommendation = "exclude"
        guidance = (
            "Se excluyó preventivamente porque la evidencia semántica es débil. "
            "Inclúyalo sólo si la necesidad del negocio lo requiere y confirme la decisión."
        )
    elif confidence == "medium" and structurally_supported:
        status = "structurally_supported"
        recommendation = "include"
        guidance = (
            "La asociación inicial era intermedia, pero las claves y relaciones declaradas "
            "respaldan su inclusión. No necesita consultar la base manualmente."
        )
    elif confidence == "medium":
        status = "review_required"
        recommendation = "exclude"
        guidance = (
            "La estructura no aporta evidencia suficiente y el concepto se excluyó "
            "preventivamente. Revise la explicación y decida dentro de la plataforma; "
            "no es necesario escribir SQL."
        )
    else:
        status = "confirmed"
        recommendation = "include"
        guidance = "La referencia y su asociación semántica tienen evidencia suficiente."
    return {
        "status": status,
        "recommended_action": recommendation,
        "guidance": guidance,
        "checks": checks,
    }


def selected_semantic_candidates(semantic_map: dict[str, Any]) -> list[dict[str, Any]]:
    """Return selected candidates while keeping legacy proposals compatible."""
    return [
        item
        for item in semantic_map.get("candidates", [])
        if isinstance(item, dict) and bool(item.get("selected", True))
    ]


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
    tokens = {token for token in re.findall(r"[a-záéíóúñ0-9]+", text.casefold()) if len(token) >= 3}
    # A question may use a plural (products/productos) while a technical table uses
    # the singular (Product). Retaining both forms improves discovery without choosing
    # the model on behalf of the LLM.
    singulars = {
        token[:-2] if token.endswith("es") and len(token) > 5 else token[:-1]
        for token in tokens
        if token.endswith("s") and len(token) > 4
    }
    return tokens | {token for token in singulars if len(token) >= 3}


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
            confidence = (
                str(raw.get("confidence", "low"))
                if str(raw.get("confidence", "low")) in {"high", "medium", "low"}
                else "low"
            )
            evidence = _semantic_candidate_evidence(normalized, existing, confidence)
            candidates.append(
                {
                    "business_concept": str(raw.get("business_concept", "concepto"))[:80],
                    "business_name_es": str(raw.get("business_name_es", "Concepto de negocio"))[
                        :160
                    ],
                    "description_es": str(raw.get("description_es", ""))[:500],
                    "technical_refs": normalized,
                    "confidence": confidence,
                    "reason": str(raw.get("reason", ""))[:500],
                    "references_validated": True,
                    "evidence": evidence,
                    "selected": evidence["recommended_action"] != "exclude",
                    "selection_source": "automatic",
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
            for candidate in selected_semantic_candidates(semantic_map)
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
    concept_neighbor_terms = {
        "product": {"product", "producto"},
        "customer": {"customer", "cliente"},
        "territory": {"territory", "territorio"},
        "date": {"date", "fecha", "calendar"},
    }
    preferred_neighbors: list[str] = []
    for candidate in selected_semantic_candidates(semantic_map):
        if not isinstance(candidate, dict):
            continue
        concept_tokens = _search_tokens(
            {
                "code": candidate.get("business_concept", ""),
                "name": candidate.get("business_name_es", ""),
            }
        )
        exact_names = {
            term
            for concept, terms in concept_neighbor_terms.items()
            if concept in concept_tokens or bool(concept_tokens & terms)
            for term in terms
        }
        if not exact_names:
            continue
        for reference in candidate.get("technical_refs", []):
            reference = str(reference)
            if reference not in graph:
                continue
            current_name = reference.rsplit(".", 1)[-1].casefold()
            if current_name in exact_names:
                continue
            for neighbor in sorted(graph[reference]):
                neighbor_name = neighbor.rsplit(".", 1)[-1].casefold()
                if neighbor_name in exact_names and neighbor not in preferred_neighbors:
                    preferred_neighbors.append(neighbor)
    for reference in preferred_neighbors:
        if len(expanded) >= PROPOSAL_SCOPE_MAX_TABLES:
            break
        expanded.add(reference)
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
            -len(_search_tokens(ref.rsplit(".", 1)[-1]) & SALES_PROFILE.discovery_terms),
            len(_search_tokens(ref.rsplit(".", 1)[-1])),
            ref,
        ),
    )
    expanded.update(ranked_neighbors[: max(0, PROPOSAL_SCOPE_MAX_TABLES - len(expanded))])
    # Entity labels may live behind nullable identity branches (person, organization, etc.).
    # Preserve those declared targets even when the dimensional connector path filled the
    # compact scope; the deterministic resolver still decides whether they are compatible.
    identity_terms = {
        "customer",
        "client",
        "cliente",
        "buyer",
        "comprador",
        "person",
        "persona",
        "store",
        "tienda",
        "company",
        "empresa",
        "organization",
        "business",
        "entity",
        "entidad",
    }
    identity_neighbors: list[str] = []
    for candidate in selected_semantic_candidates(semantic_map):
        if not isinstance(candidate, dict):
            continue
        concept_tokens = _search_tokens(candidate.get("business_concept", ""))
        if not concept_tokens & {"customer", "client", "cliente", "buyer", "comprador"}:
            continue
        for reference in candidate.get("technical_refs", []):
            reference = str(reference)
            if reference not in tables:
                continue
            for relation in tables[reference].get("foreign_keys", []):
                if not isinstance(relation, dict):
                    continue
                target = (
                    f"{relation.get('referenced_schema', '')}."
                    f"{relation.get('referenced_table', '')}"
                )
                relation_tokens = _search_tokens(
                    {
                        "target": target,
                        "columns": relation.get("columns", []),
                    }
                )
                if target in tables and relation_tokens & identity_terms:
                    identity_neighbors.append(target)
    expanded.update(dict.fromkeys(identity_neighbors))
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
    assessment = business_request.get("viability_assessment", {})
    assessment = assessment if isinstance(assessment, dict) else {}
    compact_request = {
        "domain": business_request.get("domain"),
        "goal": business_request.get("goal"),
        "questions": [
            {
                "code": item.get("code"),
                "label": item.get("label"),
                "instruction": item.get("instruction"),
            }
            for item in business_request.get("questions", [])
            if isinstance(item, dict)
        ],
        "periodicity": {
            key: business_request.get("periodicity", {}).get(key) for key in ("code", "label")
        },
        "requirements": [
            {
                "code": item.get("code"),
                "label": item.get("label"),
                "status": item.get("status"),
                "components": item.get("components", []),
                "formula": item.get("formula"),
            }
            for item in assessment.get("requirements", [])
            if isinstance(item, dict)
        ],
        "accepted_limitations": assessment.get("accepted_limitations", []),
    }
    compact_semantic_map = [
        {
            "business_concept": item.get("business_concept"),
            "business_name_es": item.get("business_name_es"),
            "technical_refs": item.get("technical_refs", []),
            "confidence": item.get("confidence"),
        }
        for item in selected_semantic_candidates(semantic_map)
    ]
    scoped_refs = {
        str(item.get("ref"))
        for item in scope.get("tables", [])
        if isinstance(item, dict) and item.get("ref")
    }
    compact_scope = {
        "tables": [
            {
                "ref": table.get("ref"),
                "columns": list(table.get("columns", []))[:8],
                "foreign_keys": [
                    relation
                    for relation in table.get("foreign_keys", [])
                    if isinstance(relation, dict)
                    and (
                        f"{relation.get('referenced_schema', '')}."
                        f"{relation.get('referenced_table', '')}"
                    )
                    in scoped_refs
                ],
            }
            for table in scope.get("tables", [])
            if isinstance(table, dict)
        ]
    }
    return {
        "request_version": CONTRACT_VERSION,
        "language": "es",
        "task": "propose_sales_dimensional_model",
        "source": {"connector": connector, "snapshot_hash": snapshot_hash},
        "business_request": compact_request,
        "semantic_map": compact_semantic_map,
        "scope": compact_scope,
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
    if tokens & {"discount", "descuento"}:
        return "discount_amount"
    if tokens & {"cost", "costo", "coste"}:
        return "cost_amount"
    if tokens & {"amount", "total", "sales", "venta", "ventas", "importe", "monto"}:
        return "sales_amount"
    if aggregation in {"count", "count_distinct"}:
        return "transaction_count"
    return "sales_amount"


def _measure_candidates_for_role(role: str, fact_columns: list[dict[str, Any]]) -> list[str]:
    role_terms = {
        "sales_amount": {
            "amount",
            "total",
            "line",
            "sales",
            "importe",
            "monto",
            "price",
            "precio",
            "cost",
            "costo",
            "tax",
            "impuesto",
            "freight",
            "flete",
            "discount",
            "descuento",
        },
        "quantity": {"qty", "quantity", "cantidad", "unidades", "units"},
        "cost_amount": {"cost", "costo", "coste"},
        "discount_amount": {"discount", "descuento"},
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
        if role == "transaction_count" and tokens & {"detail", "line", "detalle", "linea"}:
            continue
        if role == "transaction_count" and tokens & {
            "qty",
            "quantity",
            "cantidad",
            "units",
            "unidades",
        }:
            continue
        if tokens & terms:
            candidates.append(name)
    return candidates


def _column_supports_role(role: str, column: str) -> bool:
    tokens = _search_tokens(column)
    required_terms = {
        "sales_amount": {
            "amount",
            "total",
            "line",
            "sales",
            "importe",
            "monto",
            "price",
            "precio",
            "cost",
            "costo",
            "tax",
            "impuesto",
            "freight",
            "flete",
            "discount",
            "descuento",
        },
        "quantity": {"qty", "quantity", "cantidad", "unidades", "units"},
        "cost_amount": {"cost", "costo", "coste"},
        "discount_amount": {"discount", "descuento"},
        "customer_count": {"customer", "cliente", "account", "person", "store"},
        "transaction_count": {"order", "sale", "sales", "venta", "transaction", "pedido"},
    }
    return bool(tokens & required_terms.get(role, set()))


def _looks_like_discount_rate(value: object) -> bool:
    tokens = _search_tokens(value)
    return bool(tokens & {"discount", "descuento"}) and not bool(
        tokens & {"amount", "importe", "monto", "total", "value", "valor"}
    )


def _numeric_fact_columns(fact_columns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        column
        for column in fact_columns
        if re.search(
            r"tinyint|smallint|int|bigint|decimal|numeric|money|float|real",
            str(column.get("type", column.get("data_type", ""))).casefold(),
        )
    ]


def _discount_amount_suggestion(
    measure_name: str,
    proposed_column: str,
    fact_columns: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Infer a monetary discount recipe only when every semantic factor is unambiguous."""
    if not (
        _looks_like_discount_rate(proposed_column)
        and bool(_search_tokens(measure_name) & {"discount", "descuento", "total", "importe"})
    ):
        return None
    numeric_names = [str(column.get("name", "")) for column in _numeric_fact_columns(fact_columns)]
    discount_candidates = [name for name in numeric_names if _looks_like_discount_rate(name)]
    price_candidates = [
        name
        for name in numeric_names
        if bool(_search_tokens(name) & {"price", "precio"})
        and not bool(_search_tokens(name) & {"discount", "descuento"})
    ]
    quantity_candidates = [
        name
        for name in numeric_names
        if bool(_search_tokens(name) & {"qty", "quantity", "cantidad", "units", "unidades"})
    ]
    if (
        discount_candidates == [proposed_column]
        and len(price_candidates) == 1
        and len(quantity_candidates) == 1
    ):
        return {
            "operation": "multiply",
            "inputs": [price_candidates[0], proposed_column, quantity_candidates[0]],
            "null_policy": "preserve_null",
            "reason": (
                "La columna de descuento representa una tasa; el importe monetario por fila "
                "requiere precio por tasa por cantidad."
            ),
        }
    return None


def _discount_amount_recipe_is_complete(operation: str, inputs: list[str]) -> bool:
    """Accept a discount amount only when a verified monetary base accompanies its rate."""
    if operation != "multiply" or not any(_looks_like_discount_rate(value) for value in inputs):
        return False
    non_discount = [value for value in inputs if not _looks_like_discount_rate(value)]
    has_price = any(bool(_search_tokens(value) & {"price", "precio"}) for value in non_discount)
    has_quantity = any(
        bool(_search_tokens(value) & {"qty", "quantity", "cantidad", "units", "unidades"})
        for value in non_discount
    )
    has_amount_base = any(
        bool(
            _search_tokens(value)
            & {"amount", "importe", "monto", "value", "valor", "gross", "bruto", "subtotal"}
        )
        for value in non_discount
    )
    return (has_price and has_quantity) or has_amount_base


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
    decision_diagnostics: list[dict[str, Any]] = []
    measure_index_map: dict[int, int] = {}
    measures: list[dict[str, Any]] = []
    fact_columns_by_name = {str(item.get("name")): item for item in fact_columns}
    for source_index, item in enumerate(blueprint.get("measures", [])):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "medida_ventas"))
        calculation = item.get("calculation") if isinstance(item.get("calculation"), dict) else None
        provider_calculation_operation = str(item.get("calculation_operation", "direct"))
        provider_calculation_inputs = item.get("calculation_inputs", [])
        if (
            calculation is None
            and provider_calculation_operation != "direct"
            and isinstance(provider_calculation_inputs, list)
        ):
            calculation = {
                "operation": provider_calculation_operation,
                "inputs": [str(value) for value in provider_calculation_inputs],
            }
        calculation_inputs = (
            [str(value) for value in calculation.get("inputs", [])]
            if calculation is not None and isinstance(calculation.get("inputs"), list)
            else []
        )
        proposed_column = str(item.get("source_column", ""))
        role = _semantic_role(item, " ".join(calculation_inputs) or proposed_column)
        suggested_calculation: dict[str, Any] | None = None
        discount_input = next(
            (value for value in calculation_inputs if _looks_like_discount_rate(value)),
            proposed_column if _looks_like_discount_rate(proposed_column) else "",
        )
        if (
            calculation is not None
            and role in {"sales_amount", "discount_amount"}
            and discount_input
        ):
            operation = str(calculation.get("operation", ""))
            if not _discount_amount_recipe_is_complete(operation, calculation_inputs):
                suggested_calculation = _discount_amount_suggestion(
                    name, discount_input, fact_columns
                )
                if suggested_calculation is None:
                    reason = (
                        f"La medida {name} fue excluida porque usa una tasa de descuento sin "
                        "una base monetaria verificable. Defina precio y cantidad, o un importe "
                        "base inequívoco, antes de calcular el descuento."
                    )
                    proposal_warnings.append(reason)
                    decision_diagnostics.append(
                        {
                            "kind": "measure",
                            "code": name,
                            "status": "excluded",
                            "reason": reason,
                            "compatible_measures": [],
                        }
                    )
                    continue
                calculation = suggested_calculation
                calculation_inputs = [str(value) for value in suggested_calculation["inputs"]]
                automatic_adjustments.append(
                    f"La medida {name} se corrigió automáticamente como importe monetario: "
                    f"{' × '.join(calculation_inputs)}. La receta incompleta del proveedor "
                    "fue sustituida por columnas verificadas."
                )
                decision_diagnostics.append(
                    {
                        "kind": "measure",
                        "code": name,
                        "status": "auto_corrected",
                        "reason": str(suggested_calculation["reason"]),
                        "suggested_calculation": {
                            "operation": "multiply",
                            "inputs": calculation_inputs,
                        },
                    }
                )
        if calculation is None:
            suggested_calculation = _discount_amount_suggestion(name, proposed_column, fact_columns)
            if suggested_calculation is not None:
                calculation = suggested_calculation
                calculation_inputs = [str(value) for value in suggested_calculation["inputs"]]
                automatic_adjustments.append(
                    f"La medida {name} se corrigió automáticamente como importe monetario: "
                    f"{' × '.join(calculation_inputs)}. La tasa original se conserva como entrada."
                )
                decision_diagnostics.append(
                    {
                        "kind": "measure",
                        "code": name,
                        "status": "auto_corrected",
                        "reason": str(suggested_calculation["reason"]),
                        "suggested_calculation": {
                            "operation": "multiply",
                            "inputs": calculation_inputs,
                        },
                    }
                )
        if calculation is not None:
            operation = str(calculation.get("operation", ""))
            valid_width = 2 <= len(calculation_inputs) <= 4
            if operation in {"subtract", "divide"}:
                valid_width = len(calculation_inputs) == 2
            if (
                operation not in ALLOWED_CALCULATED_MEASURE_OPERATIONS
                or not valid_width
                or len(set(calculation_inputs)) != len(calculation_inputs)
                or any(value not in fact_columns_by_name for value in calculation_inputs)
            ):
                reason = (
                    f"La medida calculada {name} fue excluida porque su receta no usa una "
                    "operacion controlada y columnas verificadas de la tabla de hechos."
                )
                proposal_warnings.append(reason)
                decision_diagnostics.append(
                    {
                        "kind": "measure",
                        "code": name,
                        "status": "excluded",
                        "reason": reason,
                        "compatible_measures": [],
                    }
                )
                continue
            non_numeric = [
                value
                for value in calculation_inputs
                if not re.search(
                    r"tinyint|smallint|int|bigint|decimal|numeric|money|float|real",
                    str(fact_columns_by_name[value].get("type", "")).casefold(),
                )
            ]
            if non_numeric:
                reason = (
                    f"La medida calculada {name} fue excluida porque las entradas "
                    f"{', '.join(non_numeric)} no son numericas."
                )
                proposal_warnings.append(reason)
                decision_diagnostics.append(
                    {
                        "kind": "measure",
                        "code": name,
                        "status": "excluded",
                        "reason": reason,
                        "compatible_measures": [],
                    }
                )
                continue
            source_column = calculation_inputs[0]
            aggregation = str(item.get("aggregation", "sum"))
            if aggregation not in ROLE_AGGREGATIONS[role]:
                aggregation = ROLE_DEFAULT_AGGREGATION[role]
            formula_operator = {
                "multiply": "×",
                "add": "+",
                "subtract": "−",
                "divide": "÷",
            }[operation]
            measure_index_map[source_index] = len(measures)
            measures.append(
                {
                    "name": name,
                    "source_columns": calculation_inputs,
                    "aggregation": aggregation,
                    "semantic_role": role,
                    "provenance": {
                        "kind": "calculated",
                        "source_references": [
                            f"{fact_source}.{column}" for column in calculation_inputs
                        ],
                        "formula": f" {formula_operator} ".join(calculation_inputs),
                        "verification": "Columnas y tipos comprobados en la instantánea.",
                    },
                    "calculation": {
                        "operation": operation,
                        "inputs": calculation_inputs,
                        "null_policy": "preserve_null",
                    },
                }
            )
            if suggested_calculation is None:
                automatic_adjustments.append(
                    f"La medida {name} se derivará mediante {operation} usando exclusivamente "
                    "columnas verificadas, sin SQL libre."
                )
            continue
        candidates = _measure_candidates_for_role(role, fact_columns)
        if not candidates and not _column_supports_role(role, proposed_column):
            reason = (
                f"La medida {name} fue excluida porque {proposed_column or 'la columna elegida'} "
                f"no representa {role} en la tabla de hechos verificada."
            )
            proposal_warnings.append(reason)
            decision_diagnostics.append(
                {
                    "kind": "measure",
                    "code": name,
                    "status": "excluded",
                    "reason": reason,
                    "compatible_measures": [],
                }
            )
            continue
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
        measure_index_map[source_index] = len(measures)
        measures.append(
            {
                "name": name,
                "source_columns": [source_column],
                "aggregation": aggregation,
                "semantic_role": role,
                "provenance": {
                    "kind": "direct",
                    "source_references": [f"{fact_source}.{source_column}"],
                    "formula": f"{aggregation.upper()}({source_column})",
                    "verification": "Tabla y columna comprobadas en la instantánea.",
                },
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
        source = (
            proposed_source
            if bool(item.get("source_locked")) and proposed_source in scoped
            else max(scoped, key=lambda ref: dimension_source_score(name, ref))
        )
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
    for item in blueprint.get("kpis", []):
        if not isinstance(item, dict):
            continue
        raw_index = item.get("measure_index", 0)
        index = raw_index if isinstance(raw_index, int) else 0
        effective_index = measure_index_map.get(index)
        measure = measures[effective_index] if effective_index is not None else {}
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
                "provenance": {
                    "measure": measure_name,
                    "operation": operation,
                    "source_references": list(
                        measure.get("provenance", {}).get("source_references", [])
                    ),
                    "formula": f"{operation.upper()}({measure_name})",
                },
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
    dimensions, semantic_quality = enrich_dimension_labels(dimensions, scope, semantic_map)
    summary = str(blueprint.get("summary", "Propuesta dimensional de ventas."))
    return {
        "contract_version": CONTRACT_VERSION,
        "domain": SALES_PROFILE.code,
        "summary": summary,
        "business_explanation": (
            f"{summary} La aplicación expandió y validó las decisiones técnicas del copiloto."
        ),
        "semantic_mapping": selected_semantic_candidates(semantic_map),
        "grain": {
            "description": str(
                blueprint.get("grain_description", "Una fila por transacción de venta.")
            ),
            "source_tables": [fact_source],
            "business_keys": business_keys[:4],
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
            (
                "Cada dimensión visible debe resolver una etiqueta descriptiva con "
                "cobertura comprobada."
            ),
        ],
        "assumptions": list(blueprint.get("assumptions", [])),
        "warnings": proposal_warnings,
        "automatic_adjustments": automatic_adjustments,
        "provider_observations": list(blueprint.get("warnings", [])),
        "decision_diagnostics": decision_diagnostics,
        "semantic_quality": semantic_quality,
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
    calculation_changes = adjustments.get("measure_calculations", {})
    selected_measures: list[dict[str, Any]] = []
    index_map: dict[int, int] = {}
    for new_index, name in enumerate(requested_measures):
        old_index, source_measure = measures_by_name[name]
        measure = deepcopy(source_measure)
        if name in aggregation_changes:
            measure["aggregation"] = aggregation_changes[name]
        if name in calculation_changes:
            calculation = calculation_changes[name]
            if not isinstance(calculation, dict):
                raise ValueError(f"El calculo de {name} no tiene una estructura valida.")
            measure["calculation"] = deepcopy(calculation)
            inputs = calculation.get("inputs", [])
            if isinstance(inputs, list) and inputs:
                measure["source_column"] = str(inputs[0])
        else:
            measure.pop("calculation", None)
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


def controlled_relation_catalog(scope: dict[str, Any]) -> list[dict[str, Any]]:
    """Expose only declared relationships with deterministic cardinality and risk checks."""
    tables = {
        str(item.get("ref")): item
        for item in scope.get("tables", [])
        if isinstance(item, dict) and item.get("ref")
    }

    def column_map(reference: str) -> dict[str, dict[str, Any]]:
        return {
            str(item.get("name")): item
            for item in tables.get(reference, {}).get("columns", [])
            if isinstance(item, dict) and item.get("name")
        }

    def compatible(left_type: str, right_type: str) -> bool:
        def normalized(value: str) -> str:
            return re.sub(r"\([^)]*\)", "", value.casefold()).strip()

        left = normalized(left_type)
        right = normalized(right_type)
        integer = {"tinyint", "smallint", "int", "bigint"}
        text = {"char", "nchar", "varchar", "nvarchar", "text"}
        return left == right or ({left, right} <= integer) or ({left, right} <= text)

    options: list[dict[str, Any]] = []
    for source, table in tables.items():
        for relation in table.get("foreign_keys", []):
            if not isinstance(relation, dict):
                continue
            target = (
                f"{relation.get('referenced_schema', '')}.{relation.get('referenced_table', '')}"
            )
            if target not in tables:
                continue
            left_columns = [str(item) for item in relation.get("columns", [])]
            right_columns = [str(item) for item in relation.get("referenced_columns", [])]
            source_columns = column_map(source)
            target_columns = column_map(target)
            left_types = [
                str(source_columns.get(item, {}).get("type", "")) for item in left_columns
            ]
            right_types = [
                str(target_columns.get(item, {}).get("type", "")) for item in right_columns
            ]
            types_match = (
                bool(left_columns)
                and len(left_columns) == len(right_columns)
                and all(
                    compatible(left_type, right_type)
                    for left_type, right_type in zip(left_types, right_types, strict=True)
                )
            )
            target_unique = bool(right_columns) and all(
                bool(target_columns.get(item, {}).get("pk", False)) for item in right_columns
            )
            source_unique = bool(left_columns) and all(
                bool(source_columns.get(item, {}).get("pk", False)) for item in left_columns
            )
            cardinality = (
                "one_to_one"
                if source_unique and target_unique
                else "many_to_one"
                if target_unique
                else "unknown"
            )
            nullable_source = any(
                bool(source_columns.get(item, {}).get("nullable", False)) for item in left_columns
            )
            duplication_risk = not target_unique
            signature = {
                "left_table": source,
                "right_table": target,
                "left_columns": left_columns,
                "right_columns": right_columns,
            }
            eligible = types_match and target_unique
            options.append(
                {
                    "option_id": canonical_hash(signature),
                    **signature,
                    "left_types": left_types,
                    "right_types": right_types,
                    "cardinality": cardinality,
                    "target_unique": target_unique,
                    "nullable_source": nullable_source,
                    "duplication_risk": duplication_risk,
                    "eligible": eligible,
                    "guidance": (
                        "Relación declarada hacia una clave única; conserva la granularidad."
                        if eligible
                        else (
                            "No se puede seleccionar: la clave destino no es única."
                            if duplication_risk
                            else "No se puede seleccionar: los tipos de las columnas no coinciden."
                        )
                    ),
                }
            )
    return options


def apply_controlled_relationship(
    source_blueprint: dict[str, Any],
    dimension_name: str,
    option: dict[str, Any],
) -> dict[str, Any]:
    """Lock one dimensional source to the parent of a prevalidated declared relationship."""
    if not bool(option.get("eligible")) or bool(option.get("duplication_risk")):
        raise ValueError("La relación no conserva la granularidad aprobada.")
    blueprint = deepcopy(source_blueprint)
    dimensions = [item for item in blueprint.get("dimensions", []) if isinstance(item, dict)]
    dimension = next((item for item in dimensions if str(item.get("name")) == dimension_name), None)
    if dimension is None:
        raise ValueError("La dimensión no pertenece a la propuesta seleccionada.")
    dimension["source_table"] = str(option["right_table"])
    dimension["source_locked"] = True
    blueprint["controlled_relation"] = {
        "dimension_name": dimension_name,
        "option_id": option["option_id"],
        "left_table": option["left_table"],
        "right_table": option["right_table"],
        "left_columns": option["left_columns"],
        "right_columns": option["right_columns"],
        "cardinality": option["cardinality"],
        "duplication_risk": False,
    }
    return blueprint


def _issue(code: str, level: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "level": level, "path": path, "message": message}


def build_requirement_coverage(
    proposal: dict[str, Any], assessment: dict[str, Any]
) -> list[dict[str, Any]]:
    """Link every assessed requirement to concrete proposal outputs or an explicit gap."""
    fact = proposal.get("fact", {}) if isinstance(proposal.get("fact"), dict) else {}
    measures = [item for item in fact.get("measures", []) if isinstance(item, dict)]
    dimensions = [item for item in proposal.get("dimensions", []) if isinstance(item, dict)]
    kpis = [item for item in proposal.get("kpis", []) if isinstance(item, dict)]
    dimension_outputs = {
        "date": ["dim_fecha"]
        if any(item.get("name") == "dim_fecha" for item in dimensions)
        else [],
        "product": ["dim_producto"]
        if any(item.get("name") == "dim_producto" for item in dimensions)
        else [],
        "customer": ["dim_cliente"]
        if any(item.get("name") == "dim_cliente" for item in dimensions)
        else [],
        "territory": ["dim_territorio"]
        if any(item.get("name") == "dim_territorio" for item in dimensions)
        else [],
    }

    def measure_outputs(component: str) -> list[str]:
        roles = {
            "sales_amount": "sales_amount",
            "quantity": "quantity",
            "transactions": "transaction_count",
        }
        expected_role = roles.get(component)
        terms = {
            "unit_cost": {"cost", "costo", "coste", "standard"},
            "unit_price": {"price", "precio"},
            "discount_rate": {"discount", "descuento", "rate", "tasa"},
        }.get(component, set())
        outputs: list[str] = []
        for measure in measures:
            tokens = _search_tokens(
                {
                    "name": measure.get("name", ""),
                    "columns": measure.get("source_columns", []),
                }
            )
            if (expected_role and measure.get("semantic_role") == expected_role) or (
                terms and tokens & terms
            ):
                outputs.append(f"medida:{measure.get('name')}")
        return list(dict.fromkeys(outputs))

    derived_term_groups = {
        "goal:discount_amount": [{"discount", "descuento"}],
        "goal:total_cost": [{"cost", "costo", "coste"}, {"total"}],
        "goal:gross_margin": [{"margin", "margen", "profit", "rentabilidad"}],
        "goal:sales_per_unit": [{"venta", "sales"}, {"unit", "unidad"}],
        "goal:cost_per_unit": [
            {"cost", "costo", "coste"},
            {"unit", "unidad"},
        ],
    }

    def derived_outputs(code: str) -> list[str]:
        required_groups = derived_term_groups.get(code)
        if not required_groups:
            return []
        results: list[str] = []
        for kind, values in (("medida", measures), ("kpi", kpis)):
            for value in values:
                tokens = _search_tokens(
                    {
                        "name": value.get("name", ""),
                        "code": value.get("code", ""),
                    }
                )
                if all(tokens & group for group in required_groups):
                    results.append(f"{kind}:{value.get('name')}")
        return results

    accepted = set(assessment.get("accepted_limitations", []))
    coverage: list[dict[str, Any]] = []
    for requirement in assessment.get("requirements", []):
        if not isinstance(requirement, dict):
            continue
        code = str(requirement.get("code", ""))
        request_status = str(requirement.get("status", "ambiguous"))
        components = [str(item) for item in requirement.get("components", [])]
        outputs: list[str] = []
        component_gaps: list[str] = []
        for component in components:
            matches = dimension_outputs.get(component, []) or measure_outputs(component)
            if matches:
                outputs.extend(matches)
            else:
                component_gaps.append(component)
        explicit_derived = derived_outputs(code)
        if explicit_derived:
            outputs.extend(explicit_derived)
            component_gaps = []
        if request_status == "unavailable" and code in accepted:
            coverage_status = "accepted_limitation"
            explanation = "La ausencia fue confirmada; no se inventará una fuente o cálculo."
        elif request_status == "ambiguous" and code in accepted:
            coverage_status = "human_decision"
            explanation = "La ambigüedad y su alcance fueron aceptados por el analista."
        elif not component_gaps and outputs:
            coverage_status = "covered"
            explanation = "El requisito aparece en salidas verificables de la propuesta."
        else:
            coverage_status = "not_covered"
            explanation = (
                "La propuesta no materializa todavía: "
                + ", ".join(component_gaps or components or ["el resultado solicitado"])
                + "."
            )
        coverage.append(
            {
                "requirement_code": code,
                "label": str(requirement.get("label", code)),
                "request_status": request_status,
                "coverage_status": coverage_status,
                "outputs": list(dict.fromkeys(outputs)),
                "explanation": explanation,
            }
        )
    return coverage


def apply_financial_requirements(
    proposal: dict[str, Any], assessment: dict[str, Any], scope: dict[str, Any]
) -> dict[str, Any]:
    """Materialize proven financial requirements that the provider may have omitted.

    The enrichment is deliberately structural: it only uses columns present in the
    bounded scope and paths composed from declared foreign keys. Ambiguous candidates
    remain uncovered so the normal validation blocks approval instead of guessing.
    """
    result = deepcopy(proposal)
    requested = {
        str(item.get("code"))
        for item in assessment.get("requirements", [])
        if isinstance(item, dict) and item.get("status") in {"direct", "derivable"}
    }
    financial_codes = {
        "goal:discount_amount",
        "goal:total_cost",
        "goal:gross_margin",
        "goal:sales_per_unit",
        "goal:cost_per_unit",
    }
    if not requested & financial_codes:
        return result

    tables = {
        str(item.get("ref")): item
        for item in scope.get("tables", [])
        if isinstance(item, dict) and item.get("ref")
    }
    fact = result.get("fact")
    if not isinstance(fact, dict):
        return result
    fact_sources = [str(item) for item in fact.get("source_tables", [])]
    if len(fact_sources) != 1 or fact_sources[0] not in tables:
        return result
    fact_source = fact_sources[0]

    graph: dict[str, set[str]] = {reference: set() for reference in tables}
    for source, table in tables.items():
        for relation in table.get("foreign_keys", []):
            if not isinstance(relation, dict):
                continue
            target = (
                f"{relation.get('referenced_schema', '')}.{relation.get('referenced_table', '')}"
            )
            if target in graph:
                graph[source].add(target)
                graph[target].add(source)

    def reachable(target: str) -> bool:
        pending = [fact_source]
        visited = {fact_source}
        while pending:
            current = pending.pop(0)
            if current == target:
                return True
            for neighbor in sorted(graph.get(current, set())):
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
        return False

    def candidates(
        pattern_groups: tuple[set[str], ...],
        *,
        fact_only: bool = False,
        allowed_tables: set[str] | None = None,
    ) -> list[str]:
        references: list[str] = []
        for terms in pattern_groups:
            for table_ref, table in tables.items():
                if fact_only and table_ref != fact_source:
                    continue
                if allowed_tables is not None and table_ref not in allowed_tables:
                    continue
                if not reachable(table_ref):
                    continue
                for column in table.get("columns", []):
                    if not isinstance(column, dict) or not column.get("name"):
                        continue
                    name = str(column["name"])
                    if terms <= _search_tokens(name):
                        references.append(f"{table_ref}.{name}")
            if references:
                return list(dict.fromkeys(references))
        return []

    measures = [item for item in fact.get("measures", []) if isinstance(item, dict)]
    kpis = [item for item in result.get("kpis", []) if isinstance(item, dict)]

    def measure_for_role(role: str) -> dict[str, Any] | None:
        return next((item for item in measures if item.get("semantic_role") == role), None)

    def append_measure(
        *, name: str, role: str, references: list[str], operation: str, formula: str
    ) -> dict[str, Any] | None:
        existing = measure_for_role(role)
        if existing is not None:
            return existing
        if not references or any(reference.count(".") < 2 for reference in references):
            return None
        measure = {
            "name": name,
            "source_columns": references,
            "aggregation": "sum",
            "semantic_role": role,
            "provenance": {
                "kind": "calculated",
                "source_references": references,
                "formula": formula,
                "verification": (
                    "Columnas, tipos y ruta de relación comprobados en la instantánea."
                ),
            },
            "calculation": {
                "operation": operation,
                "inputs": references,
                "null_policy": "preserve_null",
            },
        }
        measures.append(measure)
        return measure

    quantity = measure_for_role("quantity")
    quantity_name = str(quantity.get("name")) if quantity else ""
    quantity_refs = (
        [str(item) for item in quantity.get("provenance", {}).get("source_references", [])]
        if quantity
        else candidates(({"order", "qty"}, {"quantity"}, {"cantidad"}, {"units"}), fact_only=True)
    )
    if not quantity_name and len(quantity_refs) == 1:
        reference = quantity_refs[0]
        quantity = {
            "name": "unidades_vendidas",
            "source_columns": [reference],
            "aggregation": "sum",
            "semantic_role": "quantity",
            "provenance": {
                "kind": "direct",
                "source_references": [reference],
                "formula": f"SUM({reference})",
                "verification": "Tabla y columna comprobadas en la instantánea.",
            },
        }
        measures.append(quantity)
        quantity_name = "unidades_vendidas"

    cost_requested = bool(
        requested & {"goal:total_cost", "goal:gross_margin", "goal:cost_per_unit"}
    )
    total_cost: dict[str, Any] | None = None
    if cost_requested and len(quantity_refs) == 1:
        product_sources = {
            str(source)
            for dimension in result.get("dimensions", [])
            if isinstance(dimension, dict)
            and bool(
                _search_tokens(
                    {
                        "name": dimension.get("name", ""),
                        "role": dimension.get("semantic_role", ""),
                    }
                )
                & {"product", "producto", "productos"}
            )
            for source in dimension.get("source_tables", [])
            if str(source) in tables and reachable(str(source))
        }
        cost_patterns = (
            {"standard", "cost"},
            {"unit", "cost"},
            {"product", "cost"},
            {"costo", "unitario"},
            {"costo"},
            {"cost"},
        )
        cost_refs = candidates(
            cost_patterns,
            allowed_tables=product_sources or None,
        )
        if len(cost_refs) == 1:
            total_cost = append_measure(
                name="costo_total",
                role="cost_amount",
                references=[quantity_refs[0], cost_refs[0]],
                operation="multiply",
                formula=f"SUM({quantity_refs[0]} × {cost_refs[0]})",
            )

    if "goal:discount_amount" in requested:
        price_refs = [
            reference
            for reference in candidates(({"unit", "price"},), fact_only=True)
            if "discount" not in _search_tokens(reference)
            and "descuento" not in _search_tokens(reference)
        ]
        discount_refs = candidates(
            ({"unit", "price", "discount"}, {"discount", "rate"}),
            fact_only=True,
        )
        if len(price_refs) == len(discount_refs) == len(quantity_refs) == 1:
            append_measure(
                name="descuento_monetario",
                role="discount_amount",
                references=[price_refs[0], discount_refs[0], quantity_refs[0]],
                operation="multiply",
                formula=(f"SUM({price_refs[0]} × {discount_refs[0]} × {quantity_refs[0]})"),
            )

    fact["measures"] = measures
    result["fact"] = fact

    def add_aggregate(code: str, name: str, measure: dict[str, Any], unit: str) -> None:
        if any(str(item.get("code")) == code for item in kpis):
            return
        kpis.append(
            {
                "code": code,
                "name": name,
                "description_es": f"{name} calculado únicamente con medidas verificadas.",
                "formula_kind": "aggregate",
                "formula": {"operation": "sum", "measure": str(measure.get("name"))},
                "unit": unit,
                "semantic_role": str(measure.get("semantic_role")),
                "provenance": deepcopy(measure.get("provenance", {})),
            }
        )

    def add_derived(
        code: str, name: str, kind: str, inputs: list[str], unit: str, formula: str
    ) -> None:
        if not all(inputs) or any(str(item.get("code")) == code for item in kpis):
            return
        kpis.append(
            {
                "code": code,
                "name": name,
                "description_es": f"{name} derivado de resultados agregados conciliados.",
                "formula_kind": kind,
                "inputs": inputs,
                "unit": unit,
                "provenance": {
                    "source_references": inputs,
                    "formula": formula,
                    "verification": "Entradas conciliadas y denominador controlado.",
                },
            }
        )

    sales = measure_for_role("sales_amount")
    sales_name = str(sales.get("name")) if sales else ""
    if total_cost is not None:
        total_cost_name = str(total_cost.get("name"))
        add_aggregate("costo_total", "Costo total", total_cost, "moneda de origen")
        if "goal:gross_margin" in requested and sales_name:
            add_derived(
                "margen_bruto",
                "Margen bruto",
                "difference",
                [sales_name, total_cost_name],
                "moneda de origen",
                f"SUM({sales_name}) − SUM({total_cost_name})",
            )
            add_derived(
                "margen_porcentaje",
                "Margen bruto %",
                "share",
                ["margen_bruto", sales_name],
                "porcentaje",
                f"margen_bruto ÷ SUM({sales_name}) × 100",
            )
        if "goal:cost_per_unit" in requested and quantity_name:
            add_derived(
                "costo_por_unidad",
                "Costo por unidad",
                "ratio",
                [total_cost_name, quantity_name],
                "moneda de origen por unidad",
                f"SUM({total_cost_name}) ÷ SUM({quantity_name})",
            )
    discount = measure_for_role("discount_amount")
    if discount is not None:
        add_aggregate(
            "descuento_monetario",
            "Descuento monetario",
            discount,
            "moneda de origen",
        )
    if "goal:sales_per_unit" in requested and sales_name and quantity_name:
        add_derived(
            "venta_por_unidad",
            "Venta por unidad",
            "ratio",
            [sales_name, quantity_name],
            "moneda de origen por unidad",
            f"SUM({sales_name}) ÷ SUM({quantity_name})",
        )
    result["kpis"] = kpis
    return result


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
        grain_keys = {str(item) for item in grain.get("business_keys", [])}
        for table in grain["source_tables"]:
            table_columns = {
                str(column.get("name"))
                for column in scoped.get(str(table), {}).get("columns", [])
                if isinstance(column, dict)
            }
            detail_identifiers = {
                column
                for column in table_columns
                if _search_tokens(column) & {"detail", "line", "detalle", "linea"}
                and _search_tokens(column) & {"id", "key", "clave"}
            }
            if detail_identifiers and not detail_identifiers.issubset(grain_keys):
                issues.append(
                    _issue(
                        "grain.detail_key_missing",
                        "error",
                        "grain.business_keys",
                        (
                            "La granularidad debe conservar el identificador del detalle: "
                            f"{', '.join(sorted(detail_identifiers))}."
                        ),
                    )
                )

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
        relation_graph: dict[str, set[str]] = {reference: set() for reference in scoped}
        for source, table in scoped.items():
            for relation in table.get("foreign_keys", []):
                if not isinstance(relation, dict):
                    continue
                target = (
                    f"{relation.get('referenced_schema', '')}."
                    f"{relation.get('referenced_table', '')}"
                )
                if target in relation_graph:
                    relation_graph[source].add(target)
                    relation_graph[target].add(source)

        def source_reference(value: object) -> str | None:
            raw = str(value)
            if raw.count(".") >= 2:
                table_ref, column_name = raw.rsplit(".", 1)
                table_columns = {
                    str(column.get("name"))
                    for column in scoped.get(table_ref, {}).get("columns", [])
                    if isinstance(column, dict)
                }
                if column_name not in table_columns:
                    return None
                pending = list(fact_sources)
                visited = set(fact_sources)
                while pending:
                    current = pending.pop(0)
                    if current == table_ref:
                        return raw
                    for neighbor in sorted(relation_graph.get(current, set())):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            pending.append(neighbor)
                return None
            matches = [
                f"{table_ref}.{raw}"
                for table_ref in fact_sources
                if raw
                in {
                    str(column.get("name"))
                    for column in scoped.get(table_ref, {}).get("columns", [])
                    if isinstance(column, dict)
                }
            ]
            return matches[0] if len(matches) == 1 else None

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
                calculation = (
                    measure.get("calculation")
                    if isinstance(measure.get("calculation"), dict)
                    else None
                )
                if (
                    calculation is None
                    and role in {"sales_amount", "discount_amount"}
                    and _looks_like_discount_rate(source_column)
                ):
                    issues.append(
                        _issue(
                            "measure.discount_rate_as_amount",
                            "error",
                            f"fact.measures.{index}",
                            (
                                f"{name} usa {source_column}, que parece una tasa de descuento, "
                                "como si fuera un importe monetario. Defina una medida calculada "
                                "con columnas verificadas de precio, tasa y cantidad."
                            ),
                        )
                    )
                if (
                    calculation is None
                    and source_column
                    and not _column_supports_role(role, source_column)
                ):
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
                if role == "transaction_count":
                    source_tokens = _search_tokens(source_column)
                    if (
                        aggregation != "count_distinct"
                        or source_tokens
                        & {
                            "detail",
                            "line",
                            "detalle",
                            "linea",
                        }
                        or not source_tokens
                        & {
                            "order",
                            "sale",
                            "sales",
                            "transaction",
                            "pedido",
                        }
                    ):
                        issues.append(
                            _issue(
                                "measure.transaction_distinct_order",
                                "error",
                                f"fact.measures.{index}",
                                (
                                    "Transacciones debe usar COUNT(DISTINCT) sobre el "
                                    "identificador del pedido, nunca sobre el detalle."
                                ),
                            )
                        )
                columns = measure.get("source_columns", [])
                for column in columns if isinstance(columns, list) else []:
                    if source_reference(column) is None:
                        issues.append(
                            _issue(
                                "reference.column_unknown",
                                "error",
                                f"fact.measures.{index}.source_columns",
                                (
                                    f"La columna {column} no existe o no tiene una ruta "
                                    "de relación declarada desde el hecho."
                                ),
                            )
                        )
                if calculation is not None:
                    operation = str(calculation.get("operation", ""))
                    inputs = calculation.get("inputs", [])
                    if operation not in ALLOWED_CALCULATED_MEASURE_OPERATIONS:
                        issues.append(
                            _issue(
                                "measure.calculation_operation",
                                "error",
                                f"fact.measures.{index}.calculation.operation",
                                "La operacion de la medida calculada no esta permitida.",
                            )
                        )
                    if not isinstance(inputs, list) or inputs != columns:
                        issues.append(
                            _issue(
                                "measure.calculation_inputs",
                                "error",
                                f"fact.measures.{index}.calculation.inputs",
                                "Las entradas del calculo deben coincidir con sus columnas fuente.",
                            )
                        )
                    elif (
                        len(inputs) < 2
                        or len(inputs) > 4
                        or (operation in {"subtract", "divide"} and len(inputs) != 2)
                    ):
                        issues.append(
                            _issue(
                                "measure.calculation_arity",
                                "error",
                                f"fact.measures.{index}.calculation.inputs",
                                "La cantidad de entradas no corresponde a la operacion controlada.",
                            )
                        )
                    if (
                        role in {"sales_amount", "discount_amount"}
                        and isinstance(inputs, list)
                        and any(_looks_like_discount_rate(value) for value in inputs)
                        and not _discount_amount_recipe_is_complete(
                            operation, [str(value) for value in inputs]
                        )
                    ):
                        issues.append(
                            _issue(
                                "measure.discount_amount_incomplete",
                                "error",
                                f"fact.measures.{index}.calculation.inputs",
                                (
                                    f"{name} usa una tasa de descuento, pero el cálculo no "
                                    "incluye una base monetaria verificable. Use precio por tasa "
                                    "por cantidad o un importe base inequívoco por tasa."
                                ),
                            )
                        )
                if "need_assessment" in proposal:
                    provenance = measure.get("provenance")
                    if not isinstance(provenance, dict):
                        issues.append(
                            _issue(
                                "measure.provenance_missing",
                                "error",
                                f"fact.measures.{index}.provenance",
                                "La medida no muestra su tabla, columnas y fórmula verificable.",
                            )
                        )
                    else:
                        expected_references = {
                            reference
                            for column in columns
                            if (reference := source_reference(column)) is not None
                        }
                        references = {str(item) for item in provenance.get("source_references", [])}
                        if not references or not references.issubset(expected_references):
                            issues.append(
                                _issue(
                                    "measure.provenance_invalid",
                                    "error",
                                    f"fact.measures.{index}.provenance",
                                    "La procedencia no coincide con tabla.columna verificadas.",
                                )
                            )
                        if not str(provenance.get("formula", "")).strip():
                            issues.append(
                                _issue(
                                    "measure.formula_missing",
                                    "error",
                                    f"fact.measures.{index}.provenance.formula",
                                    "La medida debe mostrar su agregación o fórmula controlada.",
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
            if dimension.get("name") == "dim_fecha":
                continue
            display_label = dimension.get("display_label")
            if not isinstance(display_label, dict):
                if "semantic_quality" not in proposal:
                    continue
                issues.append(
                    _issue(
                        "dimension.display_label_missing",
                        "error",
                        f"dimensions.{index}.display_label",
                        (
                            "La dimensión no resuelve una etiqueta descriptiva. Revise sus "
                            "relaciones antes de publicarla para análisis."
                        ),
                    )
                )
                continue
            variants = display_label.get("variants", [])
            if not isinstance(variants, list) or not variants:
                issues.append(
                    _issue(
                        "dimension.display_variants_missing",
                        "error",
                        f"dimensions.{index}.display_label.variants",
                        "La etiqueta descriptiva no conserva una ruta verificable.",
                    )
                )
                continue
            base_source = source_tables[0] if len(source_tables) == 1 else ""
            base_table = all_tables.get(base_source, {})
            base_foreign_keys = [
                item for item in base_table.get("foreign_keys", []) if isinstance(item, dict)
            ]
            for variant_index, variant in enumerate(variants):
                if not isinstance(variant, dict):
                    continue
                target = str(variant.get("source_table", ""))
                columns = [str(item) for item in variant.get("columns", [])]
                if target not in all_tables:
                    issues.append(
                        _issue(
                            "dimension.display_table_unknown",
                            "error",
                            f"dimensions.{index}.display_label.variants.{variant_index}",
                            f"La ruta descriptiva {target} no existe en la instantánea.",
                        )
                    )
                    continue
                target_columns = {
                    str(item.get("name"))
                    for item in all_tables[target].get("columns", [])
                    if isinstance(item, dict)
                }
                if not columns or any(column not in target_columns for column in columns):
                    issues.append(
                        _issue(
                            "dimension.display_column_unknown",
                            "error",
                            f"dimensions.{index}.display_label.variants.{variant_index}",
                            "La ruta descriptiva contiene columnas inexistentes.",
                        )
                    )
                if target != base_source:
                    left_columns = [str(item) for item in variant.get("left_columns", [])]
                    right_columns = [str(item) for item in variant.get("right_columns", [])]
                    relation_exists = any(
                        f"{relation.get('referenced_schema', '')}."
                        f"{relation.get('referenced_table', '')}"
                        == target
                        and [str(item) for item in relation.get("columns", [])] == left_columns
                        and [str(item) for item in relation.get("referenced_columns", [])]
                        == right_columns
                        for relation in base_foreign_keys
                    )
                    if not relation_exists:
                        issues.append(
                            _issue(
                                "dimension.display_relation_unknown",
                                "error",
                                f"dimensions.{index}.display_label.variants.{variant_index}",
                                "La ruta descriptiva no coincide con una relación declarada.",
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
        known_kpi_inputs = set(measures)
        for index, kpi in enumerate(kpis):
            if not isinstance(kpi, dict):
                issues.append(
                    _issue(
                        "kpi.formula",
                        "error",
                        f"kpis.{index}.formula",
                        "El KPI no tiene una estructura válida.",
                    )
                )
                continue
            code = str(kpi.get("code", ""))
            kind = str(kpi.get("formula_kind", "aggregate"))
            if kind in {"ratio", "share", "difference"}:
                inputs = [str(item) for item in kpi.get("inputs", [])]
                if len(inputs) != 2 or not all(item in known_kpi_inputs for item in inputs):
                    issues.append(
                        _issue(
                            "kpi.derived_inputs",
                            "error",
                            f"kpis.{index}.inputs",
                            (
                                "El KPI derivado requiere exactamente dos medidas o "
                                "indicadores previamente comprobados."
                            ),
                        )
                    )
                provenance = kpi.get("provenance")
                if (
                    not isinstance(provenance, dict)
                    or not str(provenance.get("formula", "")).strip()
                ):
                    issues.append(
                        _issue(
                            "kpi.derived_formula",
                            "error",
                            f"kpis.{index}.provenance",
                            "El KPI derivado debe mostrar su fórmula y denominador.",
                        )
                    )
                if code:
                    known_kpi_inputs.add(code)
                continue
            formula = kpi.get("formula", {}) if isinstance(kpi.get("formula"), dict) else {}
            if (
                kind != "aggregate"
                or formula.get("operation") not in ALLOWED_AGGREGATIONS
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
            if code:
                known_kpi_inputs.add(code)

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

    assessment = proposal.get("need_assessment")
    coverage = proposal.get("requirement_coverage")
    if isinstance(assessment, dict):
        coverage_items = coverage if isinstance(coverage, list) else []
        expected_requirements = {
            str(item.get("code"))
            for item in assessment.get("requirements", [])
            if isinstance(item, dict)
        }
        covered_requirements = {
            str(item.get("requirement_code")) for item in coverage_items if isinstance(item, dict)
        }
        if expected_requirements != covered_requirements:
            issues.append(
                _issue(
                    "coverage.incomplete_matrix",
                    "error",
                    "requirement_coverage",
                    "La matriz no representa todos los requisitos de la necesidad.",
                )
            )
        for index, item in enumerate(coverage_items):
            if not isinstance(item, dict):
                continue
            coverage_status = str(item.get("coverage_status", "not_covered"))
            request_status = str(item.get("request_status", "ambiguous"))
            if coverage_status == "not_covered" and request_status in {"direct", "derivable"}:
                issues.append(
                    _issue(
                        "coverage.requirement_missing",
                        "error",
                        f"requirement_coverage.{index}",
                        (
                            f"El requisito {item.get('label', 'sin etiqueta')} era viable, "
                            "pero no aparece en la propuesta. Genere una versión corregida."
                        ),
                    )
                )
            elif coverage_status in {"accepted_limitation", "human_decision"}:
                issues.append(
                    _issue(
                        "coverage.human_decision",
                        "warning",
                        f"requirement_coverage.{index}",
                        str(item.get("explanation", "Decisión humana registrada.")),
                    )
                )

    controlled_revision = proposal.get("controlled_relation_revision")
    if isinstance(controlled_revision, dict) and (
        not bool(controlled_revision.get("validated"))
        or bool(controlled_revision.get("duplication_risk"))
        or controlled_revision.get("cardinality") not in {"many_to_one", "one_to_one"}
    ):
        issues.append(
            _issue(
                "relationship.controlled_revision_invalid",
                "error",
                "controlled_relation_revision",
                (
                    "La corrección de relación no demuestra cardinalidad segura ni "
                    "conservación de la granularidad."
                ),
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
