from __future__ import annotations

from copy import deepcopy

import pytest

from app.modules.copilot.domains import (
    catalog_for_snapshot,
    default_needs_catalog_configuration,
    normalize_needs_catalog_configuration,
)
from app.modules.copilot.service import (
    apply_analyst_adjustments,
    canonical_hash,
    compact_metadata_blocks,
    derived_scope,
    expand_proposal_blueprint,
    validate_proposal,
    validated_semantic_candidates,
    verify_proposal_evidence,
)

DOCUMENT = {
    "contract_version": 1,
    "source": {"connector": "sqlserver", "database": "SalesDemo"},
    "schemas": [
        {
            "name": "Sales",
            "tables": [
                {
                    "name": "OrderDetail",
                    "columns": [
                        {"name": "OrderID", "data_type": "int", "primary_key": True},
                        {"name": "ProductID", "data_type": "int", "primary_key": True},
                        {"name": "LineTotal", "data_type": "money", "primary_key": False},
                    ],
                    "foreign_keys": [
                        {
                            "name": "FK_OrderDetail_Product",
                            "columns": ["ProductID"],
                            "referenced_schema": "Production",
                            "referenced_table": "Product",
                            "referenced_columns": ["ProductID"],
                        }
                    ],
                }
            ],
        },
        {
            "name": "Production",
            "tables": [
                {
                    "name": "Product",
                    "columns": [
                        {"name": "ProductID", "data_type": "int", "primary_key": True},
                        {"name": "Name", "data_type": "nvarchar", "primary_key": False},
                    ],
                    "foreign_keys": [],
                }
            ],
        },
    ],
}


def semantic_response(reference: str = "Sales.OrderDetail") -> dict[str, object]:
    return {
        "contract_version": 1,
        "candidates": [
            {
                "business_concept": "venta",
                "business_name_es": "Detalle de venta",
                "description_es": "Una línea vendida.",
                "technical_refs": [reference],
                "confidence": "high",
                "reason": "Contiene el importe de la línea.",
            }
        ],
    }


def valid_proposal() -> dict[str, object]:
    return {
        "contract_version": 1,
        "domain": "ventas",
        "summary": "Ventas por producto.",
        "business_explanation": "Cada fila representará una línea vendida.",
        "semantic_mapping": [],
        "grain": {
            "description": "Una fila por línea vendida.",
            "source_tables": ["Sales.OrderDetail"],
        },
        "fact": {
            "name": "fact_ventas",
            "source_tables": ["Sales.OrderDetail"],
            "business_keys": ["OrderID", "ProductID"],
            "measures": [
                {
                    "name": "importe_venta",
                    "source_columns": ["LineTotal"],
                    "aggregation": "sum",
                }
            ],
        },
        "dimensions": [
            {
                "name": "dim_producto",
                "source_tables": ["Production.Product"],
                "business_key": "ProductID",
                "attributes": ["Name"],
            }
        ],
        "joins": [
            {
                "left_table": "Sales.OrderDetail",
                "right_table": "Production.Product",
                "left_columns": ["ProductID"],
                "right_columns": ["ProductID"],
            }
        ],
        "kpis": [
            {
                "code": "ventas_totales",
                "name": "Ventas totales",
                "formula": {"operation": "sum", "measure": "importe_venta"},
                "unit": "currency",
            }
        ],
        "etl_plan": [
            {
                "order": 1,
                "operation": "extract",
                "inputs": ["Sales.OrderDetail"],
                "output": "stg_ventas",
                "description": "Extraer los campos aprobados.",
            }
        ],
        "quality_rules": [],
        "assumptions": [],
        "warnings": [],
    }


def valid_blueprint() -> dict[str, object]:
    return {
        "contract_version": 1,
        "domain": "ventas",
        "summary": "Ventas por producto.",
        "grain_description": "Una fila por línea vendida.",
        "fact_source": "Sales.OrderDetail",
        "measures": [{"name": "importe_venta", "source_column": "LineTotal", "aggregation": "sum"}],
        "dimensions": [{"name": "dim_producto", "source_table": "Production.Product"}],
        "kpis": [
            {
                "code": "ventas_totales",
                "name": "Ventas totales",
                "measure_index": 0,
                "operation": "sum",
                "unit": "moneda",
            }
        ],
        "assumptions": [],
        "warnings": [],
    }


def test_metadata_is_partitioned_without_rows_or_secrets() -> None:
    blocks = compact_metadata_blocks(
        DOCUMENT,
        {"goal": "Analizar ventas por producto", "questions": ["top_products"]},
        1,
    )
    assert len(blocks) == 2
    assert all(len(block["metadata"]) == 1 for block in blocks)
    assert "password" not in str(blocks).casefold()
    assert "rows" not in str(blocks).casefold()


def test_catalog_is_derived_from_snapshot_metadata() -> None:
    catalog = catalog_for_snapshot(DOCUMENT)
    sales = catalog[0]
    questions = {item["code"]: item for item in sales["questions"]}
    periodicities = {item["code"]: item for item in sales["periodicities"]}

    assert sales["code"] == "ventas"
    assert sales["available"] is True
    assert questions["top_products"]["available"] is True
    assert questions["territory_performance"]["available"] is True
    assert "dimensions" not in sales
    assert set(periodicities) == {"day", "week", "month", "quarter", "year"}
    assert all(item["available"] is False for item in periodicities.values())


def test_catalog_labels_and_availability_are_configurable_without_changing_codes() -> None:
    configuration = default_needs_catalog_configuration()
    questions = configuration["questions"]
    assert isinstance(questions, list)
    questions[1]["label"] = "Ranking comercial de productos"
    questions[1]["description"] = "Ordena productos por el resultado comercial seleccionado."
    questions[1]["enabled"] = False

    catalog = catalog_for_snapshot(DOCUMENT, configuration)
    top_products = catalog[0]["questions"][1]

    assert top_products["code"] == "top_products"
    assert top_products["label"] == "Ranking comercial de productos"
    assert top_products["available"] is False
    assert "deshabilitada" in str(top_products["reason"])


def test_catalog_accepts_dynamic_business_questions_but_rejects_unsupported_periodicities() -> None:
    configuration = default_needs_catalog_configuration()
    questions = configuration["questions"]
    assert isinstance(questions, list)
    questions[0]["code"] = "margin_evolution"
    questions[0]["label"] = "Evolución del margen"
    questions[0]["description"] = (
        "Permite orientar el análisis hacia la evolución del margen comercial."
    )
    questions[0]["prompt_instruction"] = (
        "Busque evidencia verificable para calcular y explicar el margen comercial."
    )

    normalized = normalize_needs_catalog_configuration(configuration)
    assert normalized["questions"][0]["code"] == "margin_evolution"

    periodicities = configuration["periodicities"]
    assert isinstance(periodicities, list)
    configuration["periodicities"] = [item for item in periodicities if item["code"] == "month"]
    reduced_catalog = catalog_for_snapshot(DOCUMENT, configuration)
    assert [item["code"] for item in reduced_catalog[0]["periodicities"]] == ["month"]

    periodicities = configuration["periodicities"]
    assert isinstance(periodicities, list)
    periodicities[0]["code"] = "fortnight"

    with pytest.raises(ValueError, match="estrategia temporal"):
        normalize_needs_catalog_configuration(configuration)


def test_semantic_reference_must_exist_before_scope_is_derived() -> None:
    semantic_map, rejected = validated_semantic_candidates(
        [semantic_response("Sales.TableInventedByModel")], DOCUMENT
    )
    assert semantic_map["candidates"] == []
    assert rejected[0]["code"] == "semantic.unknown_reference"


def test_scope_adds_only_declared_related_tables() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    assert [item["ref"] for item in scope["tables"]] == [
        "Production.Product",
        "Sales.OrderDetail",
    ]


def test_valid_proposal_passes_deterministic_checks() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    validation = validate_proposal(valid_proposal(), scope, DOCUMENT)
    assert validation["valid"] is True
    assert validation["errors"] == 0


def test_compact_ai_blueprint_is_expanded_and_validated_deterministically() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    blueprint = {
        "contract_version": 1,
        "domain": "ventas",
        "summary": "Ventas por producto.",
        "grain_description": "Una fila por línea vendida.",
        "fact_source": "Sales.OrderDetail",
        "measures": [{"name": "importe_venta", "source_column": "OrderID", "aggregation": "sum"}],
        "dimensions": [{"name": "dim_producto", "source_table": "Sales.OrderDetail"}],
        "kpis": [
            {
                "code": "ventas_totales",
                "name": "Ventas totales",
                "measure_index": 0,
                "operation": "sum",
                "unit": "moneda",
            }
        ],
        "assumptions": [],
        "warnings": [],
    }
    proposal = expand_proposal_blueprint(blueprint, scope, semantic_map)
    validation = validate_proposal(proposal, scope, DOCUMENT)
    assert proposal["ai_decisions"] == blueprint
    assert proposal["fact"]["measures"][0]["source_columns"] == ["LineTotal"]
    assert proposal["dimensions"][0]["source_tables"] == ["Production.Product"]
    assert proposal["warnings"] == []
    assert len([item for item in proposal["automatic_adjustments"] if "se ajustó" in item]) == 2
    assert proposal["etl_plan"][-1]["output"] == "fact_ventas"
    assert validation["valid"] is True


def test_sales_amount_never_uses_an_identifier_as_automatic_replacement() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    fact_table = next(item for item in scope["tables"] if item["ref"] == "Sales.OrderDetail")
    fact_table["columns"].insert(
        0,
        {"name": "SalesOrderDetailID", "type": "int", "pk": True, "nullable": False},
    )
    blueprint = valid_blueprint()
    blueprint["measures"] = [
        {"name": "Importe", "source_column": "UnitPrice", "aggregation": "sum"}
    ]

    proposal = expand_proposal_blueprint(blueprint, scope, semantic_map)

    assert proposal["fact"]["measures"][0]["source_columns"] == ["LineTotal"]


def test_provider_observations_are_trace_only_not_validation_warnings() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    blueprint = valid_blueprint()
    blueprint["requested_dimensions"] = ["product"]
    blueprint["warnings"] = ["No se incluyen detalles de productos."]

    proposal = expand_proposal_blueprint(blueprint, scope, semantic_map)
    validation = validate_proposal(proposal, scope, DOCUMENT)

    assert proposal["provider_observations"] == ["No se incluyen detalles de productos."]
    assert proposal["warnings"] == []
    assert validation["warnings"] == 0


def test_incompatible_kpi_is_excluded_and_explained() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    blueprint = valid_blueprint()
    blueprint["measures"][0]["semantic_role"] = "sales_amount"
    blueprint["kpis"] = [
        {
            "code": "ventas_totales",
            "name": "Ventas totales",
            "measure_index": 0,
            "operation": "sum",
            "unit": "moneda",
            "semantic_role": "sales_amount",
        },
        {
            "code": "clientes_activos",
            "name": "Clientes activos",
            "measure_index": 0,
            "operation": "count_distinct",
            "unit": "clientes",
            "semantic_role": "customer_count",
        },
    ]

    proposal = expand_proposal_blueprint(blueprint, scope, semantic_map)
    validation = validate_proposal(proposal, scope, DOCUMENT)

    assert [item["code"] for item in proposal["kpis"]] == ["ventas_totales"]
    assert proposal["decision_diagnostics"][1]["status"] == "excluded"
    assert "fue excluido" in proposal["warnings"][0]
    assert validation["valid"] is True
    assert validation["warnings"] == 1


def test_semantic_mismatch_in_a_saved_kpi_blocks_validation() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    proposal = valid_proposal()
    proposal["kpis"] = [
        {
            "code": "clientes_activos",
            "name": "Clientes activos",
            "formula": {"operation": "count_distinct", "measure": "importe_venta"},
            "unit": "clientes",
        }
    ]

    validation = validate_proposal(proposal, scope, DOCUMENT)

    assert validation["valid"] is False
    assert "kpi.semantic_mismatch" in {item["code"] for item in validation["issues"]}


def test_approved_decisions_reproduce_the_same_validated_proposal() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    proposal = expand_proposal_blueprint(valid_blueprint(), scope, semantic_map)
    validation = validate_proposal(proposal, scope, DOCUMENT)

    evidence = verify_proposal_evidence(
        proposal,
        validation,
        scope,
        semantic_map,
        DOCUMENT,
        canonical_hash(DOCUMENT),
    )

    assert evidence["verified"] is True
    assert evidence["proposal_hash"] == evidence["replay_hash"]
    assert evidence["validated_reference_count"] == 1
    assert all(check["passed"] for check in evidence["checks"])


def test_analyst_adjustment_creates_a_bounded_reproducible_blueprint() -> None:
    source = {
        **valid_blueprint(),
        "measures": [
            {"name": "importe_venta", "source_column": "LineTotal", "aggregation": "sum"},
            {"name": "lineas", "source_column": "OrderID", "aggregation": "count"},
        ],
        "kpis": [
            {
                "code": "ventas_totales",
                "name": "Ventas totales",
                "measure_index": 0,
                "operation": "sum",
                "unit": "moneda",
            },
            {
                "code": "lineas_vendidas",
                "name": "Líneas vendidas",
                "measure_index": 1,
                "operation": "count",
                "unit": "registros",
            },
        ],
    }
    revised = apply_analyst_adjustments(
        source,
        {
            "summary": "Ventas totales por producto",
            "grain_description": "Una fila por línea de venta aprobada",
            "dimension_names": ["dim_producto"],
            "measure_names": ["importe_venta"],
            "kpi_codes": ["ventas_totales"],
            "measure_aggregations": {"importe_venta": "average"},
        },
    )

    assert revised["summary"] == "Ventas totales por producto"
    assert revised["measures"] == [
        {"name": "importe_venta", "source_column": "LineTotal", "aggregation": "average"}
    ]
    assert revised["kpis"][0]["measure_index"] == 0


def test_analyst_can_reassign_a_kpi_only_to_a_semantically_compatible_measure() -> None:
    source = {
        **valid_blueprint(),
        "measures": [
            {
                "name": "importe_venta",
                "source_column": "LineTotal",
                "aggregation": "sum",
                "semantic_role": "sales_amount",
            },
            {
                "name": "clientes_distintos",
                "source_column": "CustomerID",
                "aggregation": "count_distinct",
                "semantic_role": "customer_count",
            },
        ],
        "kpis": [
            {
                "code": "clientes_activos",
                "name": "Clientes activos",
                "measure_index": 0,
                "operation": "count_distinct",
                "unit": "clientes",
                "semantic_role": "customer_count",
            }
        ],
    }

    revised = apply_analyst_adjustments(
        source,
        {
            "summary": "Clientes activos por producto",
            "grain_description": "Una fila por línea de venta aprobada",
            "dimension_names": ["dim_producto"],
            "measure_names": ["importe_venta", "clientes_distintos"],
            "kpi_codes": ["clientes_activos"],
            "kpi_measure_names": {"clientes_activos": "clientes_distintos"},
        },
    )

    assert revised["kpis"][0]["measure_index"] == 1

    with pytest.raises(ValueError, match="no es compatible"):
        apply_analyst_adjustments(
            source,
            {
                "summary": "Clientes activos por producto",
                "grain_description": "Una fila por línea de venta aprobada",
                "dimension_names": ["dim_producto"],
                "measure_names": ["importe_venta", "clientes_distintos"],
                "kpi_codes": ["clientes_activos"],
                "kpi_measure_names": {"clientes_activos": "importe_venta"},
            },
        )


def test_analyst_adjustment_rejects_a_kpi_whose_measure_was_removed() -> None:
    source = {
        **valid_blueprint(),
        "measures": [
            {"name": "importe_venta", "source_column": "LineTotal", "aggregation": "sum"},
            {"name": "lineas", "source_column": "OrderID", "aggregation": "count"},
        ],
        "kpis": [
            {
                "code": "lineas_vendidas",
                "name": "Líneas vendidas",
                "measure_index": 1,
                "operation": "count",
                "unit": "registros",
            }
        ],
    }
    with pytest.raises(ValueError, match="depende de una medida"):
        apply_analyst_adjustments(
            source,
            {
                "summary": "Ventas por producto",
                "grain_description": "Una fila por línea de venta",
                "dimension_names": ["dim_producto"],
                "measure_names": ["importe_venta"],
                "kpi_codes": ["lineas_vendidas"],
                "measure_aggregations": {},
            },
        )


def test_reproducibility_evidence_detects_a_changed_saved_proposal() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    proposal = expand_proposal_blueprint(valid_blueprint(), scope, semantic_map)
    validation = validate_proposal(proposal, scope, DOCUMENT)
    changed = deepcopy(proposal)
    changed["summary"] = "Texto modificado después de la aprobación."

    evidence = verify_proposal_evidence(
        changed,
        validation,
        scope,
        semantic_map,
        DOCUMENT,
        canonical_hash(DOCUMENT),
    )

    assert evidence["verified"] is False
    assert evidence["approval_safe"] is False
    replay_check = next(check for check in evidence["checks"] if check["code"] == "proposal.replay")
    assert replay_check["passed"] is False


def test_previous_engine_version_is_a_non_blocking_compatibility_warning() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    proposal = expand_proposal_blueprint(valid_blueprint(), scope, semantic_map)
    validation = validate_proposal(proposal, scope, DOCUMENT)

    evidence = verify_proposal_evidence(
        proposal,
        validation,
        scope,
        semantic_map,
        DOCUMENT,
        canonical_hash(DOCUMENT),
        "sales-bi-v2",
    )

    assert evidence["verified"] is True
    assert evidence["approval_safe"] is True
    assert evidence["compatibility_warning"] is True
    replay_check = next(check for check in evidence["checks"] if check["code"] == "proposal.replay")
    assert replay_check["passed"] is False
    assert "no es comparable" in replay_check["detail"]


def test_semantic_error_does_not_mark_valid_technical_references_as_failed() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    proposal = valid_proposal()
    proposal["kpis"] = [
        {
            "code": "clientes_activos",
            "name": "Clientes activos",
            "formula": {"operation": "count_distinct", "measure": "importe_venta"},
            "unit": "clientes",
        }
    ]
    validation = validate_proposal(proposal, scope, DOCUMENT)

    evidence = verify_proposal_evidence(
        proposal,
        validation,
        scope,
        semantic_map,
        DOCUMENT,
        canonical_hash(DOCUMENT),
    )

    reference_check = next(
        check for check in evidence["checks"] if check["code"] == "references.current"
    )
    assert reference_check["passed"] is True
    assert evidence["approval_safe"] is False


def test_date_dimension_prefers_transaction_date_over_product_dates() -> None:
    scope = {
        "tables": [
            {
                "ref": "Production.Product",
                "columns": [
                    {"name": "ProductID", "pk": True},
                    {"name": "SellStartDate", "pk": False},
                    {"name": "SellEndDate", "pk": False},
                ],
                "foreign_keys": [],
            },
            {
                "ref": "Sales.SalesOrderHeader",
                "columns": [
                    {"name": "SalesOrderID", "pk": True},
                    {"name": "OrderDate", "pk": False},
                    {"name": "TotalDue", "pk": False},
                ],
                "foreign_keys": [],
            },
        ]
    }
    blueprint = {
        "summary": "Ventas por fecha.",
        "grain_description": "Una fila por pedido.",
        "fact_source": "Sales.SalesOrderHeader",
        "measures": [{"name": "importe_venta", "source_column": "TotalDue", "aggregation": "sum"}],
        "dimensions": [{"name": "dim_fecha", "source_table": "Production.Product"}],
        "kpis": [
            {
                "code": "ventas_totales",
                "name": "Ventas totales",
                "measure_index": 0,
                "operation": "sum",
                "unit": "moneda",
            }
        ],
        "assumptions": [],
        "warnings": [],
    }
    proposal = expand_proposal_blueprint(blueprint, scope, {"candidates": []})
    dimension = proposal["dimensions"][0]
    assert dimension["source_tables"] == ["Sales.SalesOrderHeader"]
    assert dimension["business_key"] == "OrderDate"


def test_requested_date_dimension_is_completed_when_model_omits_it() -> None:
    scope = {
        "tables": [
            {
                "ref": "Sales.SalesOrderDetail",
                "columns": [
                    {"name": "SalesOrderDetailID", "pk": True},
                    {"name": "LineTotal", "pk": False},
                ],
                "foreign_keys": [],
            },
            {
                "ref": "Sales.SalesOrderHeader",
                "columns": [
                    {"name": "SalesOrderID", "pk": True},
                    {"name": "OrderDate", "pk": False},
                    {"name": "TotalDue", "pk": False},
                ],
                "foreign_keys": [],
            },
        ]
    }
    blueprint = {
        "summary": "Ventas por fecha.",
        "grain_description": "Una fila por detalle vendido.",
        "fact_source": "Sales.SalesOrderDetail",
        "measures": [{"name": "importe_venta", "source_column": "LineTotal"}],
        "dimensions": [],
        "requested_dimensions": ["date"],
        "kpis": [],
        "assumptions": [],
        "warnings": [],
    }

    proposal = expand_proposal_blueprint(blueprint, scope, {"candidates": []})

    assert proposal["dimensions"] == [
        {
            "name": "dim_fecha",
            "source_tables": ["Sales.SalesOrderHeader"],
            "business_key": "OrderDate",
            "attributes": ["SalesOrderID", "TotalDue"],
        }
    ]
    assert proposal["warnings"] == []
    assert "se incorporó" in proposal["automatic_adjustments"][0]


def test_invented_table_and_free_sql_block_approval() -> None:
    semantic_map, _ = validated_semantic_candidates([semantic_response()], DOCUMENT)
    scope = derived_scope(DOCUMENT, semantic_map)
    proposal = valid_proposal()
    fact = proposal["fact"]
    plan = proposal["etl_plan"]
    assert isinstance(fact, dict) and isinstance(plan, list) and isinstance(plan[0], dict)
    fact["source_tables"] = ["Sales.DoesNotExist"]
    plan[0]["description"] = "SELECT * FROM Sales.OrderDetail"
    validation = validate_proposal(proposal, scope, DOCUMENT)
    codes = {issue["code"] for issue in validation["issues"]}
    assert validation["valid"] is False
    assert "reference.table_unknown" in codes
    assert "executable.detected" in codes
