from __future__ import annotations

import json
from copy import deepcopy

import pytest

from app.modules.copilot.service import (
    COMPILATION_RULES_VERSION,
    PROMPT_VERSION,
    canonical_hash,
    compact_metadata_blocks,
    derived_scope,
    expand_proposal_blueprint,
    proposal_blueprint_schema,
    proposal_payload,
    validate_proposal,
    validated_semantic_candidates,
    verify_proposal_evidence,
)


def _wide_reviewed_metadata(spanish: bool, entity_count: int):
    schema = "Comercial" if spanish else "Operations"
    line = "DetalleFacturas" if spanish else "InvoiceLines"
    document = "Facturas" if spanish else "Invoices"
    identifier = "FacturaID" if spanish else "InvoiceID"
    amount = "ImporteRegistrado" if spanish else "ExtendedPrice"
    quantity = "Cantidad" if spanish else "Quantity"
    emitted = "FechaEmision" if spanish else "InvoiceDate"
    label = "Nombre" if spanish else "Name"
    columns = [{"name": "LineID", "data_type": "int", "primary_key": True}]
    foreign_keys = []
    entities = []
    evidence = [
        f"{schema}.{line}.LineID",
        f"{schema}.{line}.{identifier}",
        f"{schema}.{line}.{amount}",
        f"{schema}.{line}.{quantity}",
        f"{schema}.{document}.{identifier}",
        f"{schema}.{document}.{emitted}",
    ]
    for index in range(entity_count):
        key = f"Entity{index}ID"
        columns.append({"name": key, "data_type": "int"})
        foreign_keys.append(
            {
                "columns": [key],
                "referenced_schema": schema,
                "referenced_table": f"Entity{index}",
                "referenced_columns": [key],
            }
        )
        entities.append(
            {
                "name": f"Entity{index}",
                "columns": [
                    {"name": key, "data_type": "int", "primary_key": True},
                    {"name": label, "data_type": "nvarchar"},
                ],
                "foreign_keys": [],
            }
        )
        evidence.extend([f"{schema}.{line}.{key}", f"{schema}.Entity{index}.{label}"])
    columns.extend([{"name": f"OtherName{index}", "data_type": "nvarchar"} for index in range(14)])
    columns.extend(
        [
            {"name": identifier, "data_type": "int"},
            {"name": quantity, "data_type": "int"},
            {"name": amount, "data_type": "decimal"},
        ]
    )
    foreign_keys.append(
        {
            "columns": [identifier],
            "referenced_schema": schema,
            "referenced_table": document,
            "referenced_columns": [identifier],
        }
    )
    header = {
        "name": document,
        "columns": [
            {"name": identifier, "data_type": "int", "primary_key": True},
            *[{"name": f"OtherName{index}", "data_type": "nvarchar"} for index in range(14)],
            {"name": emitted, "data_type": "date"},
        ],
        "foreign_keys": [],
    }
    fact = {
        "name": line,
        "columns": columns,
        "foreign_keys": foreign_keys,
        "rows": [{"secret_row": "never-send"}],
    }
    metadata = {
        "password": "never-send",
        "schemas": [{"name": schema, "tables": [fact, header, *entities]}],
    }
    request = {
        "goal": "Comparar el importe y las unidades por período y entidad.",
        "viability_assessment": {
            "requirements": [
                {
                    "code": "ai:0",
                    "status": "direct",
                    "label": "Alcance revisado",
                    "evidence": evidence,
                    "components": ["sales_amount", "quantity", "date"],
                }
            ],
            "accepted_limitations": ["currency-unverified"],
        },
    }
    responses = [
        {
            "candidates": [
                {
                    "business_concept": "sale_line",
                    "business_name_es": "Líneas facturadas",
                    "technical_refs": [f"{schema}.{line}"],
                    "confidence": "high",
                }
            ]
        }
    ]
    semantic, _ = validated_semantic_candidates(responses, metadata)
    return (
        metadata,
        request,
        semantic,
        evidence,
        f"{schema}.{line}",
        identifier,
        amount,
        quantity,
        emitted,
    )


@pytest.mark.parametrize("spanish", [False, True])
@pytest.mark.parametrize("entity_count", [1, 14])
def test_reviewed_evidence_survives_all_context_boundaries(spanish, entity_count):
    metadata, request, semantic, evidence, fact_ref, identifier, amount, quantity, emitted = (
        _wide_reviewed_metadata(spanish, entity_count)
    )
    before = deepcopy((metadata, request, semantic))
    blocks = compact_metadata_blocks(metadata, request, max_items=3)
    discovery = {
        f"{table['ref']}.{column['name']}"
        for block in blocks
        for table in block["metadata"]
        for column in table["columns"]
    }
    scope = derived_scope(metadata, semantic, request)
    scoped = {
        f"{table['ref']}.{column['name']}"
        for table in scope["tables"]
        for column in table["columns"]
    }
    payload = proposal_payload("a" * 64, "sqlserver", request, scope, semantic)
    proposed = {
        f"{table['ref']}.{column['name']}"
        for table in payload["scope"]["tables"]
        for column in table["columns"]
    }
    assert set(evidence) <= discovery
    assert set(evidence) <= scoped
    assert set(evidence) <= proposed
    assert payload["business_request"]["requirements"][0]["references"] == evidence
    assert payload["business_request"]["accepted_limitations"] == ["currency-unverified"]
    schema = proposal_blueprint_schema(scope, semantic, request["viability_assessment"])
    allowed = schema["properties"]["measures"]["items"]["properties"]["source_column"]["enum"]
    assert {identifier, amount, quantity} <= set(allowed)
    if entity_count > 12:
        assert len(payload["scope"]["tables"]) > 12
        assert (
            len(
                next(table for table in payload["scope"]["tables"] if table["ref"] == fact_ref)[
                    "columns"
                ]
            )
            > 8
        )
    assert "never-send" not in json.dumps([blocks, payload])
    assert (metadata, request, semantic) == before


@pytest.mark.parametrize("identifier", ["InvoiceID", "FacturaID", "ComprobanteId"])
@pytest.mark.parametrize("rules", [5, 6])
def test_declared_document_keys_are_offered_for_counts_but_sum_stays_invalid(identifier, rules):
    fact_ref = "Comercial.Detalle"
    source = {
        "name": "Detalle",
        "columns": [
            {"name": "LineID", "data_type": "int", "primary_key": True},
            {"name": identifier, "data_type": "int"},
            {"name": "Importe", "data_type": "decimal"},
        ],
        "foreign_keys": [
            {
                "columns": [identifier],
                "referenced_schema": "Comercial",
                "referenced_table": "Documentos",
                "referenced_columns": [identifier],
            }
        ],
    }
    header = {
        "name": "Documentos",
        "columns": [
            {"name": identifier, "data_type": "int", "primary_key": True},
            {"name": "Fecha", "data_type": "date"},
        ],
        "foreign_keys": [],
    }
    metadata = {"schemas": [{"name": "Comercial", "tables": [source, header]}]}
    semantic, _ = validated_semantic_candidates(
        [
            {
                "candidates": [
                    {
                        "business_concept": "sale_line",
                        "business_name_es": "Detalle",
                        "technical_refs": [fact_ref],
                        "confidence": "high",
                    }
                ]
            }
        ],
        metadata,
    )
    scope = derived_scope(metadata, semantic)
    response_schema = proposal_blueprint_schema(scope, semantic)
    assert (
        identifier
        in response_schema["properties"]["measures"]["items"]["properties"]["source_column"]["enum"]
    )
    blueprint = {
        "domain": "ventas",
        "summary": "Importe y documentos distintos.",
        "grain_description": "Una fila por línea.",
        "fact_source": fact_ref,
        "measures": [
            {
                "name": "Importe registrado",
                "source_column": "Importe",
                "aggregation": "sum",
                "semantic_role": "sales_amount",
            }
        ],
        "dimensions": [{"name": "dim_fecha", "source_table": "Comercial.Documentos"}],
        "kpis": [
            {
                "code": "importe",
                "name": "Importe registrado",
                "measure_index": 0,
                "operation": "sum",
                "unit": "moneda de origen",
                "semantic_role": "sales_amount",
            }
        ],
        "assumptions": [],
        "warnings": [],
    }
    proposal = expand_proposal_blueprint(
        blueprint, scope, semantic, compilation_rules_version=rules
    )
    proposal["fact"]["measures"].append(
        {
            "name": "Documentos distintos",
            "source_columns": [identifier],
            "aggregation": "sum",
            "semantic_role": "transaction_count",
        }
    )
    checked = validate_proposal(proposal, scope, metadata)
    assert "measure.semantic_aggregation" in {issue["code"] for issue in checked["issues"]}
    proposal["fact"]["measures"][-1]["aggregation"] = "count_distinct"
    checked = validate_proposal(proposal, scope, metadata)
    if identifier in {"InvoiceID", "FacturaID"}:
        assert not any(
            issue["code"]
            in {
                "measure.semantic_source",
                "measure.semantic_aggregation",
                "measure.transaction_distinct_document",
            }
            for issue in checked["issues"]
        )
    else:
        # Merely being a key does not prove its commercial role under persisted rules 5.
        assert "measure.semantic_source" in {issue["code"] for issue in checked["issues"]}


def test_v8_contract_verification_remains_read_only_after_v9_context_change():
    metadata, _, semantic, _, fact_ref, _, amount, _, emitted = _wide_reviewed_metadata(False, 1)
    scope = derived_scope(metadata, semantic)
    blueprint = {
        "domain": "ventas",
        "summary": "Importe por fecha.",
        "grain_description": "Una fila por línea.",
        "fact_source": fact_ref,
        "measures": [
            {
                "name": "Importe registrado",
                "source_column": amount,
                "aggregation": "sum",
                "semantic_role": "sales_amount",
            }
        ],
        "dimensions": [{"name": "dim_fecha", "source_table": "Operations.Invoices"}],
        "kpis": [
            {
                "code": "importe",
                "name": "Importe registrado",
                "measure_index": 0,
                "operation": "sum",
                "unit": "moneda de origen",
                "semantic_role": "sales_amount",
            }
        ],
        "assumptions": [],
        "warnings": [],
    }
    # Use a complete historic context, as persisted v8 records do, rather than re-deriving it.
    scope = derived_scope(
        metadata,
        semantic,
        {
            "viability_assessment": {
                "requirements": [
                    {
                        "status": "direct",
                        "evidence": [f"{fact_ref}.{amount}", f"Operations.Invoices.{emitted}"],
                    }
                ]
            }
        },
    )
    proposal = expand_proposal_blueprint(blueprint, scope, semantic, compilation_rules_version=5)
    stored = validate_proposal(proposal, scope, metadata)
    assert stored["valid"]
    before = deepcopy((proposal, stored, scope, semantic, metadata))
    checked = verify_proposal_evidence(
        proposal, stored, scope, semantic, metadata, canonical_hash(metadata), "sales-bi-v8"
    )
    assert PROMPT_VERSION == "sales-bi-v9"
    assert COMPILATION_RULES_VERSION == 6
    assert checked["approval_safe"] is True
    assert checked["compatibility_warning"] is True
    assert all(item["passed"] for item in checked["checks"])
    assert (proposal, stored, scope, semantic, metadata) == before
