from __future__ import annotations

from copy import deepcopy

from app.modules.etl.materializer import (
    _detect_currency_context,
    _resolve_kpi_currency_units,
    build_materialization_plan,
)
from app.modules.etl.models import EtlExecution
from app.modules.etl.router import _applied_semantic_document, _same_execution_contract
from app.modules.etl.service import (
    assess_dimensional_readiness,
    compile_kpi_recipes,
    compile_transformation_plan,
)


def proposal() -> dict[str, object]:
    return {
        "grain": {"description": "Una fila por detalle de pedido."},
        "fact": {
            "name": "fact_ventas",
            "measures": [
                {
                    "name": "importe_venta",
                    "source_columns": ["LineTotal"],
                    "aggregation": "sum",
                    "semantic_role": "sales_amount",
                },
                {
                    "name": "cantidad_vendida",
                    "source_columns": ["OrderQty"],
                    "aggregation": "sum",
                    "semantic_role": "quantity",
                },
            ],
        },
        "dimensions": [
            {
                "name": "dim_producto",
                "business_key": "ProductID",
                "attributes": ["Name", "Color"],
            },
            {
                "name": "dim_fecha",
                "business_key": "OrderDate",
                "attributes": ["OrderDate"],
            },
        ],
        "kpis": [
            {
                "code": "ventas_netas",
                "name": "Ventas netas",
                "formula": {"operation": "sum", "measure": "importe_venta"},
                "unit": "moneda",
            },
            {
                "code": "unidades_vendidas",
                "name": "Unidades vendidas",
                "formula": {"operation": "sum", "measure": "cantidad_vendida"},
                "unit": "unidades",
            },
        ],
        "warnings": [],
    }


def test_applied_semantic_review_creates_a_new_persistable_document() -> None:
    stored: dict[str, object] = {
        "status": "review_required",
        "mappings": [{"dimension": "dim_territorio"}],
    }

    result = _applied_semantic_document(
        stored,
        [
            {
                "dimension": "dim_territorio",
                "source_column": "group",
                "label_column": "group_es",
                "mappings": [{"original": "Europe", "label_es": "Europa"}],
            }
        ],
        reviewed_by="Analista BI <analista@example.test>",
        reviewed_at="2026-09-23T19:00:00+00:00",
        analyst_comment="Etiquetas territoriales revisadas.",
    )

    assert result is not stored
    assert stored["status"] == "review_required"
    assert result["status"] == "applied"
    assert result["reviewed_by"] == "Analista BI <analista@example.test>"
    assert result["analyst_comment"] == "Etiquetas territoriales revisadas."


def test_same_execution_contract_ignores_kpi_order_but_not_selection() -> None:
    execution = EtlExecution(
        selection_document={"selected_kpi_codes": ["ventas_netas", "unidades_vendidas"]}
    )

    assert _same_execution_contract(execution, ["unidades_vendidas", "ventas_netas"])
    assert not _same_execution_contract(execution, ["ventas_netas"])


class _CurrencyCursor:
    def __init__(self, values: list[str]) -> None:
        self.values = values
        self.query = ""

    def execute(self, query: str) -> None:
        self.query = query

    def fetchall(self) -> list[tuple[str]]:
        return [(value,) for value in self.values]


class _CurrencySource:
    def __init__(self, values: list[str]) -> None:
        self.cursor_instance = _CurrencyCursor(values)

    def cursor(self) -> _CurrencyCursor:
        return self.cursor_instance


def _currency_schema() -> dict[str, object]:
    return {
        "schemas": [
            {
                "name": "Sales",
                "tables": [
                    {
                        "name": "SalesOrderDetail",
                        "columns": [{"name": "SalesOrderID", "data_type": "int"}],
                        "foreign_keys": [
                            {
                                "referenced_schema": "Sales",
                                "referenced_table": "SalesOrderHeader",
                                "columns": ["SalesOrderID"],
                                "referenced_columns": ["SalesOrderID"],
                            }
                        ],
                    },
                    {
                        "name": "SalesOrderHeader",
                        "columns": [
                            {"name": "SalesOrderID", "data_type": "int"},
                            {"name": "CurrencyRateID", "data_type": "int"},
                        ],
                        "foreign_keys": [
                            {
                                "referenced_schema": "Sales",
                                "referenced_table": "CurrencyRate",
                                "columns": ["CurrencyRateID"],
                                "referenced_columns": ["CurrencyRateID"],
                            }
                        ],
                    },
                    {
                        "name": "CurrencyRate",
                        "columns": [
                            {"name": "CurrencyRateID", "data_type": "int"},
                            {"name": "FromCurrencyCode", "data_type": "nchar"},
                            {"name": "ToCurrencyCode", "data_type": "nchar"},
                        ],
                    },
                ],
            }
        ]
    }


def test_currency_is_verified_from_a_related_single_base_code() -> None:
    source = _CurrencySource(["USD"])
    candidate = proposal()
    candidate["fact"]["source_tables"] = ["Sales.SalesOrderDetail"]

    context = _detect_currency_context(source, candidate, _currency_schema())
    kpis = _resolve_kpi_currency_units(
        [
            {"code": "ventas", "unit": "moneda"},
            {"code": "pedidos", "unit": "pedidos"},
        ],
        context,
    )

    assert context["status"] == "verified"
    assert context["currency_code"] == "USD"
    assert context["source_reference"] == "Sales.CurrencyRate.FromCurrencyCode"
    assert kpis[0]["unit"] == "USD"
    assert kpis[1]["unit"] == "pedidos"
    assert "TOP (3)" in source.cursor_instance.query


def test_mixed_source_currencies_remain_unresolved() -> None:
    source = _CurrencySource(["USD", "EUR"])
    candidate = proposal()
    candidate["fact"]["source_tables"] = ["Sales.SalesOrderDetail"]

    context = _detect_currency_context(source, candidate, _currency_schema())

    assert context["status"] == "unresolved"


def test_compiles_variable_ai_kpis_into_versioned_recipes() -> None:
    recipes, issues = compile_kpi_recipes(proposal())

    assert issues == []
    assert [item["code"] for item in recipes] == ["ventas_netas", "unidades_vendidas"]
    assert all(item["definition_version"] == "sales-kpi-v1" for item in recipes)
    assert recipes[0]["recipe"] == {
        "template": "aggregate",
        "measure": "importe_venta",
        "operation": "sum",
    }


def test_unverified_currency_is_not_presented_as_a_fact() -> None:
    candidate = proposal()
    candidate["kpis"][0]["unit"] = "EUR"

    recipes, issues = compile_kpi_recipes(candidate)

    assert issues == []
    assert recipes[0]["unit"] == "moneda de origen"
    assert recipes[0]["declared_unit"] == "EUR"
    assert "no está comprobada" in recipes[0]["adjustments"][0]


def test_gross_sales_recipe_is_not_presented_as_net_sales() -> None:
    candidate = proposal()
    candidate["fact"]["measures"][0]["source_columns"] = ["UnitPrice", "OrderQty"]
    candidate["fact"]["measures"][0]["calculation"] = {
        "operation": "multiply",
        "inputs": ["UnitPrice", "OrderQty"],
    }

    recipes, issues = compile_kpi_recipes(candidate)

    assert issues == []
    assert recipes[0]["name"] == "Ventas brutas totales"
    assert "venta bruta" in recipes[0]["adjustments"][0]


def test_blocks_kpi_without_a_verified_measure() -> None:
    invalid = deepcopy(proposal())
    invalid["kpis"] = [
        {
            "code": "margen",
            "name": "Margen",
            "formula": {"operation": "sum", "measure": "utilidad_inexistente"},
        }
    ]

    recipes, issues = compile_kpi_recipes(invalid)

    assert recipes == []
    assert any("medida comprobada" in issue for issue in issues)
    assert any("ningún KPI calculable" in issue for issue in issues)


def test_transformation_plan_is_guided_auditable_and_localizes_without_overwrite() -> None:
    plan = compile_transformation_plan(proposal())
    codes = {str(item["code"]) for item in plan}

    assert "quality.required_keys" in codes
    assert "clean.dim_producto.deduplicate" in codes
    assert "derive.dim_fecha.parts" in codes
    assert "transform.measure.importe_venta" in codes
    assert "localize.dim_producto.labels" in codes
    localization = next(item for item in plan if item["code"] == "localize.dim_producto.labels")
    assert localization["severity"] == "optional"
    assert "conserva el valor original" in str(localization["detail"])
    assert plan[-1]["stage"] == "validate"


def test_execution_readiness_rejects_bridge_as_product_dimension() -> None:
    candidate = proposal()
    candidate["dimensions"] = [
        {
            "name": "dim_producto",
            "source_tables": ["Sales.SpecialOfferProduct"],
            "business_key": "SpecialOfferID",
            "attributes": ["ProductID", "rowguid", "ModifiedDate"],
        }
    ]
    candidate["kpis"] = [
        {
            "code": "top_products",
            "name": "Productos con mayor desempeño",
            "formula": {"operation": "sum", "measure": "importe_venta"},
        }
    ]
    schema = {
        "schemas": [
            {
                "name": "Sales",
                "tables": [
                    {
                        "name": "SpecialOfferProduct",
                        "columns": [
                            {"name": "SpecialOfferID", "data_type": "int", "primary_key": True},
                            {"name": "ProductID", "data_type": "int", "primary_key": True},
                            {
                                "name": "rowguid",
                                "data_type": "uniqueidentifier",
                                "primary_key": False,
                            },
                            {"name": "ModifiedDate", "data_type": "datetime", "primary_key": False},
                        ],
                    }
                ],
            }
        ]
    }

    blockers, _ = assess_dimensional_readiness(candidate, schema)

    assert any("tabla puente" in item for item in blockers)
    assert any("atributo descriptivo" in item for item in blockers)


def test_execution_readiness_accepts_descriptive_business_dimension() -> None:
    candidate = proposal()
    candidate["dimensions"] = [
        {
            "name": "dim_producto",
            "source_tables": ["Production.Product"],
            "business_key": "ProductID",
            "attributes": ["Name", "Color"],
            "display_label": {
                "target_name": "nombre_producto",
                "variants": [
                    {
                        "kind": "base_entity",
                        "source_table": "Production.Product",
                        "left_columns": [],
                        "right_columns": [],
                        "columns": ["Name"],
                        "operation": "first_non_empty",
                    }
                ],
                "fallback_column": "ProductID",
                "minimum_descriptive_coverage": 0.95,
            },
        }
    ]
    schema = {
        "schemas": [
            {
                "name": "Production",
                "tables": [
                    {
                        "name": "Product",
                        "columns": [
                            {"name": "ProductID", "data_type": "int", "primary_key": True},
                            {"name": "Name", "data_type": "nvarchar", "primary_key": False},
                            {"name": "Color", "data_type": "nvarchar", "primary_key": False},
                        ],
                    }
                ],
            }
        ]
    }

    blockers, warnings = assess_dimensional_readiness(candidate, schema)

    assert blockers == []
    assert any("dimensión fecha" in item for item in warnings)


def test_materializer_compiles_only_verified_tables_columns_and_foreign_keys() -> None:
    candidate = proposal()
    candidate["fact"]["measures"][1]["aggregation"] = "average"
    candidate["fact"]["source_tables"] = ["Sales.SalesOrderDetail"]
    candidate["fact"]["business_keys"] = ["SalesOrderID", "SalesOrderDetailID"]
    candidate["dimensions"] = [
        {
            "name": "dim_producto",
            "source_tables": ["Production.Product"],
            "business_key": "ProductID",
            "attributes": ["Name", "Color"],
        }
    ]
    schema = {
        "schemas": [
            {
                "name": "Sales",
                "tables": [
                    {
                        "name": "SalesOrderDetail",
                        "columns": [
                            {"name": "SalesOrderID", "data_type": "int"},
                            {"name": "SalesOrderDetailID", "data_type": "int"},
                            {"name": "ProductID", "data_type": "int"},
                            {"name": "LineTotal", "data_type": "numeric"},
                            {"name": "OrderQty", "data_type": "smallint"},
                        ],
                        "foreign_keys": [
                            {
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
                            {"name": "ProductID", "data_type": "int"},
                            {"name": "Name", "data_type": "nvarchar"},
                            {"name": "Color", "data_type": "nvarchar"},
                        ],
                        "foreign_keys": [],
                    }
                ],
            },
        ]
    }

    plan = build_materialization_plan(candidate, schema)

    assert plan.fact.name == "fact_ventas"
    assert "[Sales].[SalesOrderDetail] AS t0" in plan.fact.query
    assert "LEFT JOIN [Production].[Product]" in plan.fact.query
    assert "t0.[ProductID] = t1.[ProductID]" in plan.fact.query
    assert [column.target_name for column in plan.dimensions[0].attributes] == [
        "name",
        "color",
    ]
    assert [column.aggregation for column in plan.fact.measures] == ["sum", "average"]


def test_materializer_compiles_a_controlled_calculated_measure_without_free_sql() -> None:
    candidate = proposal()
    candidate["fact"]["source_tables"] = ["Sales.SalesOrderDetail"]
    candidate["fact"]["business_keys"] = ["SalesOrderID", "SalesOrderDetailID"]
    candidate["fact"]["measures"] = [
        {
            "name": "Descuento total",
            "source_columns": ["UnitPrice", "UnitPriceDiscount", "OrderQty"],
            "aggregation": "sum",
            "semantic_role": "sales_amount",
            "calculation": {
                "operation": "multiply",
                "inputs": ["UnitPrice", "UnitPriceDiscount", "OrderQty"],
                "null_policy": "preserve_null",
            },
        }
    ]
    candidate["dimensions"] = []
    schema = {
        "schemas": [
            {
                "name": "Sales",
                "tables": [
                    {
                        "name": "SalesOrderDetail",
                        "columns": [
                            {"name": "SalesOrderID", "data_type": "int"},
                            {"name": "SalesOrderDetailID", "data_type": "int"},
                            {"name": "UnitPrice", "data_type": "money"},
                            {"name": "UnitPriceDiscount", "data_type": "numeric"},
                            {"name": "OrderQty", "data_type": "smallint"},
                        ],
                        "foreign_keys": [],
                    }
                ],
            }
        ]
    }

    plan = build_materialization_plan(candidate, schema)

    assert plan.fact.measures[0].calculation_operation == "multiply"
    assert plan.fact.measures[0].calculation_inputs == (
        "UnitPrice",
        "UnitPriceDiscount",
        "OrderQty",
    )
    assert "CAST(t0.[UnitPrice] AS decimal(38, 10))" in plan.fact.query
    assert " * CAST(t0.[UnitPriceDiscount] AS decimal(38, 10))" in plan.fact.query
    assert " * CAST(t0.[OrderQty] AS decimal(38, 10))" in plan.fact.query


def test_materializer_joins_a_verified_cost_source_and_compiles_total_cost() -> None:
    candidate = proposal()
    candidate["fact"]["source_tables"] = ["Sales.SalesOrderDetail"]
    candidate["fact"]["business_keys"] = ["SalesOrderID", "SalesOrderDetailID"]
    candidate["fact"]["measures"] = [
        {
            "name": "costo_total",
            "source_columns": [
                "Sales.SalesOrderDetail.OrderQty",
                "Production.Product.StandardCost",
            ],
            "aggregation": "sum",
            "semantic_role": "cost_amount",
            "calculation": {
                "operation": "multiply",
                "inputs": [
                    "Sales.SalesOrderDetail.OrderQty",
                    "Production.Product.StandardCost",
                ],
            },
        }
    ]
    candidate["dimensions"] = []
    schema = {
        "schemas": [
            {
                "name": "Sales",
                "tables": [
                    {
                        "name": "SalesOrderDetail",
                        "columns": [
                            {"name": "SalesOrderID", "data_type": "int"},
                            {"name": "SalesOrderDetailID", "data_type": "int"},
                            {"name": "ProductID", "data_type": "int"},
                            {"name": "OrderQty", "data_type": "smallint"},
                        ],
                        "foreign_keys": [
                            {
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
                            {"name": "ProductID", "data_type": "int"},
                            {"name": "StandardCost", "data_type": "money"},
                        ],
                        "foreign_keys": [],
                    }
                ],
            },
        ]
    }

    plan = build_materialization_plan(candidate, schema)

    assert "LEFT JOIN [Production].[Product] AS t1" in plan.fact.query
    assert "CAST(t0.[OrderQty] AS decimal(38, 10))" in plan.fact.query
    assert "CAST(t1.[StandardCost] AS decimal(38, 10))" in plan.fact.query


def test_compiles_margin_and_per_unit_recipes_with_explicit_denominators() -> None:
    candidate = proposal()
    candidate["fact"]["measures"].append(
        {
            "name": "costo_total",
            "source_columns": ["StandardCost"],
            "aggregation": "sum",
            "semantic_role": "cost_amount",
        }
    )
    candidate["kpis"].extend(
        [
            {
                "code": "margen_bruto",
                "name": "Margen bruto",
                "formula_kind": "difference",
                "inputs": ["importe_venta", "costo_total"],
                "unit": "moneda de origen",
            },
            {
                "code": "margen_porcentaje",
                "name": "Margen bruto %",
                "formula_kind": "share",
                "inputs": ["margen_bruto", "importe_venta"],
                "unit": "porcentaje",
            },
            {
                "code": "costo_por_unidad",
                "name": "Costo por unidad",
                "formula_kind": "ratio",
                "inputs": ["costo_total", "cantidad_vendida"],
                "unit": "moneda de origen por unidad",
            },
        ]
    )

    recipes, issues = compile_kpi_recipes(candidate)
    indexed = {item["code"]: item for item in recipes}

    assert issues == []
    assert indexed["margen_bruto"]["recipe"] == {
        "template": "difference",
        "minuend": "importe_venta",
        "subtrahend": "costo_total",
    }
    assert indexed["margen_porcentaje"]["recipe"]["numerator"] == "margen_bruto"
    assert indexed["margen_porcentaje"]["recipe"]["denominator"] == "importe_venta"
    assert indexed["costo_por_unidad"]["recipe"]["denominator"] == "cantidad_vendida"


def test_execution_readiness_blocks_a_discount_rate_used_as_money() -> None:
    candidate = proposal()
    candidate["fact"]["measures"] = [
        {
            "name": "Descuento total",
            "source_columns": ["DiscountRate"],
            "aggregation": "sum",
            "semantic_role": "sales_amount",
        }
    ]

    blockers, _ = assess_dimensional_readiness(candidate, {"schemas": []})

    assert any("parece una tasa" in item for item in blockers)


def test_execution_readiness_blocks_an_incomplete_discount_recipe() -> None:
    candidate = proposal()
    candidate["fact"]["measures"] = [
        {
            "name": "Descuento total",
            "source_columns": ["UnitPriceDiscount", "OrderQty"],
            "aggregation": "sum",
            "semantic_role": "sales_amount",
            "calculation": {
                "operation": "multiply",
                "inputs": ["UnitPriceDiscount", "OrderQty"],
                "null_policy": "preserve_null",
            },
        }
    ]

    blockers, _ = assess_dimensional_readiness(candidate, {"schemas": []})

    assert any("receta monetaria está incompleta" in item for item in blockers)
