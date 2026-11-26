from __future__ import annotations

from copy import deepcopy

import pytest

from app.modules.copilot.service import (
    apply_analyst_adjustments,
    build_requirement_coverage,
    canonical_hash,
    expand_proposal_blueprint,
    validate_proposal,
    verify_proposal_evidence,
)
from app.modules.etl.service import assess_selection_coverage, compile_kpi_recipes


def context():
    fact_columns = [
        {"name": "LineID", "type": "int", "pk": True},
        {"name": "InvoiceID", "type": "int", "pk": False},
        {"name": "Amount", "type": "decimal", "pk": False},
        {"name": "Quantity", "type": "int", "pk": False},
    ]
    header_columns = [
        {"name": "InvoiceID", "type": "int", "pk": True},
        {"name": "InvoiceDate", "type": "date", "pk": False},
    ]
    foreign_key = {
        "columns": ["InvoiceID"],
        "referenced_schema": "Commerce",
        "referenced_table": "Documents",
        "referenced_columns": ["InvoiceID"],
    }
    scope = {
        "origin": "semantic-discovery:v1",
        "tables": [
            {"ref": "Commerce.Lines", "columns": fact_columns, "foreign_keys": [foreign_key]},
            {"ref": "Commerce.Documents", "columns": header_columns, "foreign_keys": []},
        ],
    }
    metadata = {
        "schemas": [
            {
                "name": "Commerce",
                "tables": [
                    {
                        "name": "Lines",
                        "columns": [
                            {
                                "name": col["name"],
                                "data_type": col["type"],
                                "primary_key": col["pk"],
                            }
                            for col in fact_columns
                        ],
                        "foreign_keys": [foreign_key],
                    },
                    {
                        "name": "Documents",
                        "columns": [
                            {
                                "name": col["name"],
                                "data_type": col["type"],
                                "primary_key": col["pk"],
                            }
                            for col in header_columns
                        ],
                        "foreign_keys": [],
                    },
                ],
            }
        ]
    }
    assessment = {
        "requirements": [
            {
                "code": "goal:quantity",
                "label": "Unidades registradas",
                "status": "direct",
                "components": ["quantity"],
                "evidence": ["Commerce.Lines.Quantity"],
            },
        ],
        "accepted_limitations": [],
    }
    blueprint = {
        "domain": "ventas",
        "summary": "Importes y unidades por período.",
        "grain_description": "Una fila por línea registrada.",
        "fact_source": "Commerce.Lines",
        "measures": [
            {
                "name": "Importe registrado",
                "source_column": "Amount",
                "aggregation": "sum",
                "semantic_role": "sales_amount",
            },
            {
                "name": "Unidades registradas",
                "source_column": "Quantity",
                "aggregation": "sum",
                "semantic_role": "quantity",
            },
        ],
        "dimensions": [{"name": "dim_fecha", "source_table": "Commerce.Documents"}],
        "kpis": [
            {
                "code": "importe_del_proveedor",
                "name": "Importe registrado",
                "measure_index": 0,
                "operation": "sum",
                "semantic_role": "sales_amount",
                "unit": "moneda de origen",
            }
        ],
        "assumptions": [],
        "warnings": [],
        "business_request_scope": {
            "goal": "Analizar importes y unidades por período.",
            "requirements": assessment["requirements"],
        },
    }
    semantic = {
        "candidates": [
            {
                "business_concept": "sale_line",
                "technical_refs": ["Commerce.Lines"],
                "selected": True,
            }
        ]
    }
    return blueprint, scope, semantic, metadata, assessment


def with_coverage(proposal, assessment):
    result = deepcopy(proposal)
    result["need_assessment"] = deepcopy(assessment)
    result["requirement_coverage"] = build_requirement_coverage(result, assessment)
    return result


def adjustments(blueprint, kpi_codes):
    return {
        "summary": blueprint["summary"],
        "grain_description": blueprint["grain_description"],
        "dimension_names": ["dim_fecha"],
        "measure_names": [measure["name"] for measure in blueprint["measures"]],
        "kpi_codes": kpi_codes,
    }


def test_requested_measure_gets_one_selectable_kpi_with_platform_attribution():
    blueprint, scope, semantic, metadata, assessment = context()
    before = deepcopy((blueprint, scope, semantic, metadata, assessment))
    proposal = with_coverage(expand_proposal_blueprint(blueprint, scope, semantic), assessment)
    quantities = [kpi for kpi in proposal["kpis"] if kpi["semantic_role"] == "quantity"]
    assert len(quantities) == 1
    assert quantities[0]["formula"] == {"measure": "Unidades registradas", "operation": "sum"}
    decision = next(
        item for item in proposal["ai_decisions"]["kpis"] if item["code"] == quantities[0]["code"]
    )
    assert decision["decision_origin"] == "validated_requirement"
    assert proposal["ai_decisions"]["provider_kpis"] == blueprint["kpis"]
    diagnostic = proposal["decision_diagnostics"][-1]
    assert diagnostic["origin"] == "validated_requirement"
    assert diagnostic["requirement_codes"] == ["goal:quantity"]
    assert proposal["requirement_coverage"][0]["coverage_status"] == "covered"
    assert proposal["requirement_coverage"][0]["required_metrics"][0]["kpi_codes"] == [
        quantities[0]["code"]
    ]
    assert validate_proposal(proposal, scope, metadata)["valid"]
    recipes, issues = compile_kpi_recipes(proposal)
    assert not issues
    assert any(
        recipe["recipe"]
        == {"template": "aggregate", "measure": "unidades_registradas", "operation": "sum"}
        for recipe in recipes
    )
    assert (blueprint, scope, semantic, metadata, assessment) == before


def test_equivalent_provider_kpi_is_preserved_without_duplicate_or_forced_code():
    blueprint, scope, semantic, _, assessment = context()
    blueprint["kpis"].append(
        {
            "code": "codigo_libre_del_proveedor",
            "name": "Cantidad observada",
            "measure_index": 1,
            "operation": "sum",
            "semantic_role": "quantity",
            "unit": "piezas",
        }
    )
    proposal = with_coverage(expand_proposal_blueprint(blueprint, scope, semantic), assessment)
    assert [kpi["code"] for kpi in proposal["kpis"]] == [
        "importe_del_proveedor",
        "codigo_libre_del_proveedor",
    ]
    assert "platform_kpi_additions" not in proposal["ai_decisions"]
    assert (
        assess_selection_coverage(proposal, ["codigo_libre_del_proveedor"])["status"] == "complete"
    )


def test_average_quantity_does_not_replace_requested_sum():
    blueprint, scope, semantic, _, assessment = context()
    blueprint["kpis"].append(
        {
            "code": "promedio",
            "name": "Promedio por línea",
            "measure_index": 1,
            "operation": "average",
            "semantic_role": "quantity",
            "unit": "unidades",
        }
    )
    proposal = with_coverage(expand_proposal_blueprint(blueprint, scope, semantic), assessment)
    quantity_kpis = [item for item in proposal["kpis"] if item.get("semantic_role") == "quantity"]
    assert {item["formula"]["operation"] for item in quantity_kpis} == {"average", "sum"}
    assert assess_selection_coverage(proposal, ["promedio"])["status"] == "partial"


def test_multiple_quantity_recipes_remain_uncovered_instead_of_guessing():
    blueprint, scope, semantic, metadata, assessment = context()
    scope["tables"][0]["columns"].append({"name": "OtherQuantity", "type": "int", "pk": False})
    metadata["schemas"][0]["tables"][0]["columns"].append(
        {"name": "OtherQuantity", "data_type": "int", "primary_key": False}
    )
    blueprint["measures"].append(
        {
            "name": "Otra cantidad",
            "source_column": "OtherQuantity",
            "aggregation": "sum",
            "semantic_role": "quantity",
        }
    )
    proposal = with_coverage(expand_proposal_blueprint(blueprint, scope, semantic), assessment)
    assert not any(item.get("semantic_role") == "quantity" for item in proposal["kpis"])
    assert proposal["requirement_coverage"][0]["coverage_status"] == "not_covered"
    assert not validate_proposal(proposal, scope, metadata)["valid"]


def test_quantity_used_only_as_a_financial_operand_does_not_get_an_unrequested_kpi():
    blueprint, scope, semantic, _, _ = context()
    blueprint["business_request_scope"]["requirements"] = [
        {"code": "goal:total_cost", "status": "derivable", "components": ["unit_cost", "quantity"]}
    ]
    proposal = expand_proposal_blueprint(blueprint, scope, semantic)
    assert [item["code"] for item in proposal["kpis"]] == ["importe_del_proveedor"]
    assert "platform_kpi_additions" not in proposal["ai_decisions"]


def test_an_identifier_cannot_be_completed_as_a_numeric_quantity():
    blueprint, scope, semantic, _, _ = context()
    scope["tables"][0]["columns"] = [
        col for col in scope["tables"][0]["columns"] if col["name"] != "Quantity"
    ]
    blueprint["measures"][1]["source_column"] = "InvoiceID"
    proposal = expand_proposal_blueprint(blueprint, scope, semantic)
    assert not any(item.get("semantic_role") == "quantity" for item in proposal["kpis"])
    assert not any(item.get("semantic_role") == "quantity" for item in proposal["fact"]["measures"])


def test_a_v5_parent_never_offered_the_new_kpi_so_its_first_v6_child_completes_it():
    blueprint, scope, semantic, _, assessment = context()
    parent = expand_proposal_blueprint(blueprint, scope, semantic, compilation_rules_version=5)
    before = deepcopy(parent)
    revised = apply_analyst_adjustments(
        parent["ai_decisions"], adjustments(blueprint, ["importe_del_proveedor"])
    )
    child = with_coverage(expand_proposal_blueprint(revised, scope, semantic), assessment)
    assert any(item.get("semantic_role") == "quantity" for item in child["kpis"])
    assert child["requirement_coverage"][0]["coverage_status"] == "covered"
    assert parent == before


def test_personalization_can_remove_an_offered_kpi_without_silent_replacement():
    blueprint, scope, semantic, metadata, assessment = context()
    parent = with_coverage(expand_proposal_blueprint(blueprint, scope, semantic), assessment)
    before = deepcopy(parent)
    revised = apply_analyst_adjustments(
        parent["ai_decisions"], adjustments(blueprint, ["importe_del_proveedor"])
    )
    child = with_coverage(expand_proposal_blueprint(revised, scope, semantic), assessment)
    assert not any(item.get("semantic_role") == "quantity" for item in child["kpis"])
    assert child["requirement_coverage"][0]["coverage_status"] == "not_covered"
    assert "coverage.requirement_missing" in {
        item["code"] for item in validate_proposal(child, scope, metadata)["issues"]
    }
    assert parent == before


def test_etl_selection_is_partial_when_the_requested_quantity_kpi_is_not_selected():
    blueprint, scope, semantic, _, assessment = context()
    proposal = with_coverage(expand_proposal_blueprint(blueprint, scope, semantic), assessment)
    quantity = next(
        item["code"] for item in proposal["kpis"] if item.get("semantic_role") == "quantity"
    )
    assert assess_selection_coverage(proposal, ["importe_del_proveedor"])["status"] == "partial"
    assert assess_selection_coverage(proposal, ["importe_del_proveedor"])["missing_kpi_codes"] == [
        quantity
    ]
    assert assess_selection_coverage(proposal, [quantity])["status"] == "complete"
    legacy = deepcopy(proposal)
    legacy["compilation_rules_version"] = 5
    assert assess_selection_coverage(legacy, ["importe_del_proveedor"]) == {
        "status": "complete",
        "required_kpi_codes": [],
        "missing_kpi_codes": [],
        "message": "La selección conserva los resultados financieros solicitados.",
    }


def test_v6_completion_replays_identically_with_its_attribution():
    blueprint, scope, semantic, metadata, assessment = context()
    proposal = with_coverage(expand_proposal_blueprint(blueprint, scope, semantic), assessment)
    before = deepcopy(proposal)
    checked = verify_proposal_evidence(
        proposal,
        validate_proposal(proposal, scope, metadata),
        scope,
        semantic,
        metadata,
        canonical_hash(metadata),
    )
    assert checked["approval_safe"]
    assert checked["checks"][-1]["passed"]
    assert proposal == before


# Hashes captured from the committed pre-fix compiler for this fixture, not from rules 6.
LEGACY_HASHES = {
    1: "e5ff31715c9282a5287f95b1cde9583edc365e4a726f6447ad1d1674ff730dd3",
    2: "d19536b9d5907771d638904695d38e41834b66ad0f6f34a8560d3f7519e70a03",
    3: "1f81bc28924a95f22f98ff0a846d82508e9068a6bcc72aace7deef700f739ea4",
    4: "814bbbc8d6ba45bd901a70015a4a59f702dd928b611dc490fa1b8572d18f2457",
    5: "38d6f03ee2e8b6e576035c04e390c4659f6b92e56f9e057a7cdd99d78c081020",
}


@pytest.mark.parametrize("rules", [1, 2, 3, 4, 5])
def test_compilation_rules_1_through_5_remain_byte_for_byte_frozen(rules):
    blueprint, scope, semantic, _, _ = context()
    proposal = expand_proposal_blueprint(
        blueprint, scope, semantic, compilation_rules_version=rules
    )
    assert canonical_hash(proposal) == LEGACY_HASHES[rules]
    assert [item["code"] for item in proposal["kpis"]] == ["importe_del_proveedor"]


def test_document_average_is_a_required_selectable_recipe_independent_of_its_label():
    blueprint, scope, semantic, _, assessment = context()
    blueprint["measures"].append(
        {
            "name": "Documentos distintos",
            "source_column": "InvoiceID",
            "aggregation": "count_distinct",
            "semantic_role": "transaction_count",
        }
    )
    blueprint["kpis"].extend(
        [
            {
                "code": "conteo_variable",
                "name": "Facturas distintas",
                "measure_index": 2,
                "operation": "count_distinct",
                "semantic_role": "transaction_count",
                "unit": "Documentos",
            },
            {
                "code": "promedio_variable",
                "name": "Importe promedio por factura",
                "measure_index": 0,
                "operation": "average",
                "semantic_role": "sales_amount",
                "unit": "moneda por documento",
            },
        ]
    )
    assessment["requirements"].append(
        {
            "code": "ai:average",
            "coverage_code": "goal:average_transaction",
            "label": "Valor medio solicitado",
            "status": "derivable",
            "components": ["sales_amount", "transactions"],
            "evidence": ["Commerce.Lines.Amount", "Commerce.Lines.InvoiceID"],
        }
    )
    proposal = expand_proposal_blueprint(blueprint, scope, semantic)
    average = next(item for item in proposal["kpis"] if item["code"] == "promedio_variable")
    assert average["formula_kind"] == "ratio"
    # The requirement binding must follow the verified recipe, not a model-facing label.
    average["name"] = "Indicador documental con otro nombre"
    proposal = with_coverage(proposal, assessment)
    average_coverage = proposal["requirement_coverage"][-1]
    assert average_coverage["coverage_status"] == "covered"
    assert average_coverage["required_metrics"] == [
        {"component": "goal:average_transaction", "kpi_codes": ["promedio_variable"]}
    ]
    before = deepcopy(proposal)
    all_codes = [item["code"] for item in proposal["kpis"]]
    complete = assess_selection_coverage(proposal, all_codes)
    partial = assess_selection_coverage(
        proposal, [code for code in all_codes if code != "promedio_variable"]
    )
    assert complete["status"] == "complete"
    assert partial["status"] == "partial"
    assert partial["missing_kpi_codes"] == ["promedio_variable"]
    assert proposal == before
    legacy = deepcopy(proposal)
    legacy["compilation_rules_version"] = 5
    assert (
        assess_selection_coverage(
            legacy, [code for code in all_codes if code != "promedio_variable"]
        )["status"]
        == "complete"
    )


@pytest.mark.parametrize(
    "capability,kind,inputs,expected_groups",
    [
        ("discount_amount", "aggregate", ["discount"], 1),
        ("total_cost", "aggregate", ["cost"], 1),
        ("sales_per_unit", "ratio", ["sales", "quantity"], 1),
        ("cost_per_unit", "ratio", ["cost", "quantity"], 1),
        ("gross_margin", "difference", ["sales", "cost"], 2),
    ],
)
def test_derived_selection_bindings_follow_controlled_recipes_not_names(
    capability, kind, inputs, expected_groups
):
    measures = [
        {"name": name, "semantic_role": role, "aggregation": "sum"}
        for name, role in [
            ("sales", "sales_amount"),
            ("quantity", "quantity"),
            ("cost", "cost_amount"),
            ("discount", "discount_amount"),
        ]
    ]
    kpi = {"code": "codigo_arbitrario", "name": "Resultado de negocio", "formula_kind": kind}
    if kind == "aggregate":
        kpi["formula"] = {"measure": inputs[0], "operation": "sum"}
    else:
        kpi["inputs"] = inputs
    kpis = [kpi]
    if capability == "gross_margin":
        kpis.append(
            {
                "code": "otra_etiqueta",
                "name": "Participación observada",
                "formula_kind": "share",
                "inputs": ["codigo_arbitrario", "sales"],
            }
        )
    assessment = {
        "requirements": [
            {
                "code": "ai:result",
                "coverage_code": f"goal:{capability}",
                "label": "Resultado solicitado",
                "status": "derivable",
                "components": [],
            }
        ],
        "accepted_limitations": [],
    }
    proposal = with_coverage(
        {"compilation_rules_version": 6, "fact": {"measures": measures}, "kpis": kpis}, assessment
    )
    assert proposal["requirement_coverage"][0]["coverage_status"] == "covered"
    assert len(proposal["requirement_coverage"][0]["required_metrics"]) == expected_groups
    assert (
        assess_selection_coverage(proposal, [item["code"] for item in kpis])["status"] == "complete"
    )
    assert assess_selection_coverage(proposal, [])["status"] == "partial"
    assert assess_selection_coverage(proposal, [])["missing_kpi_codes"] == sorted(
        item["code"] for item in kpis
    )
