from types import SimpleNamespace

import pytest

from app.modules.analytics.service import (
    _derived_recipe_value,
    _display_name_for_recipe,
    _display_unit_for_recipe,
    _order_scope_note,
    _remember_resolved_measure,
    _resolve_kpi_values,
    _unique_recipes,
    execution_has_materialized_data,
    run_safe_aggregate_query,
)


def test_order_based_dashboard_discloses_non_invoiced_scope() -> None:
    metadata = {
        "schemas": [{"name": "Sales", "tables": [{"name": "OrderLines"}, {"name": "InvoiceLines"}]}]
    }
    order_proposal = {"grain": {"source_tables": ["Sales.OrderLines"]}}
    invoice_proposal = {"grain": {"source_tables": ["Sales.InvoiceLines"]}}

    assert "no equivalen" in _order_scope_note(order_proposal, metadata)
    assert _order_scope_note(invoice_proposal, metadata) == ""


def test_financial_metrics_resolve_in_order_with_explicit_denominators() -> None:
    values = {"ventas": 1000.0, "costo": 650.0, "unidades": 50.0}
    margin = _derived_recipe_value(
        {
            "kind": "difference",
            "recipe": {
                "template": "difference",
                "minuend": "ventas",
                "subtrahend": "costo",
            },
        },
        values,
    )
    assert margin == 350.0
    values["margen"] = margin

    assert (
        _derived_recipe_value(
            {
                "kind": "share",
                "recipe": {
                    "template": "share",
                    "numerator": "margen",
                    "denominator": "ventas",
                    "multiply_by": 100,
                },
            },
            values,
        )
        == 35.0
    )
    assert (
        _derived_recipe_value(
            {
                "kind": "ratio",
                "recipe": {
                    "template": "ratio",
                    "numerator": "costo",
                    "denominator": "unidades",
                },
            },
            values,
        )
        == 13.0
    )


def test_ratio_with_zero_denominator_is_not_calculable() -> None:
    result = _derived_recipe_value(
        {
            "kind": "ratio",
            "recipe": {
                "template": "ratio",
                "numerator": "ventas",
                "denominator": "unidades",
            },
        },
        {"ventas": 100.0, "unidades": 0.0},
    )

    assert result is None


def test_legacy_provider_labels_resolve_against_physical_measure_ids() -> None:
    result = _derived_recipe_value(
        {
            "kind": "ratio",
            "recipe": {
                "template": "ratio",
                "numerator": "Importe de ventas neto",
                "denominator": "Cantidad vendida",
            },
        },
        {"importe_de_ventas_neto": 1100.0, "cantidad_vendida": 10.0},
    )

    assert result == 110.0


def test_per_unit_ratios_are_presented_as_averages_with_verified_currency() -> None:
    execution = SimpleNamespace(
        metrics_document={
            "currency_context": {"status": "verified", "currency_code": "USD"},
            "kpis": [
                {
                    "code": "costo_por_unidad",
                    "unit": "moneda de origen por unidad",
                }
            ],
        }
    )
    recipe = {"code": "costo_por_unidad", "name": "Costo por unidad"}

    assert _display_name_for_recipe(recipe) == "Costo promedio por unidad vendida"
    assert _display_unit_for_recipe(execution, recipe) == "USD por unidad"


def test_legacy_average_of_line_amount_is_not_labeled_as_unit_price() -> None:
    recipe = {
        "code": "KPI_AVG_PRICE_UNIT",
        "name": "Precio promedio por unidad",
        "kind": "aggregate",
        "recipe": {
            "operation": "average",
            "measure": "Importe de ventas neto",
        },
    }

    assert _display_name_for_recipe(recipe) == "Importe promedio por línea de venta"


def test_legacy_average_of_line_amount_is_not_labeled_as_transaction_average() -> None:
    recipe = {
        "code": "AVG_TRANSACTION",
        "name": "Importe promedio por transacción",
        "kind": "aggregate",
        "recipe": {"operation": "average", "measure": "importe_venta_linea"},
    }

    assert _display_name_for_recipe(recipe) == "Importe promedio por línea de venta"


def test_runtime_dashboard_hides_equivalent_provider_aggregate_aliases() -> None:
    recipes = [
        {
            "code": "ventas_totales",
            "kind": "aggregate",
            "recipe": {"operation": "sum", "measure": "importe_venta"},
        },
        {
            "code": "ventas_por_producto",
            "kind": "aggregate",
            "recipe": {"operation": "sum", "measure": "importe_venta"},
        },
        {
            "code": "venta_por_unidad",
            "kind": "ratio",
            "recipe": {"numerator": "importe_venta", "denominator": "cantidad"},
        },
    ]

    assert [item["code"] for item in _unique_recipes(recipes)] == [
        "ventas_totales",
        "venta_por_unidad",
    ]


def test_average_alias_cannot_overwrite_sum_used_by_derived_ratio() -> None:
    values: dict[str, float] = {}
    _remember_resolved_measure(values, "sum", "importe_venta", 1100.0)
    _remember_resolved_measure(values, "average", "importe_venta", 90.0)
    _remember_resolved_measure(values, "sum", "cantidad", 10.0)

    result = _derived_recipe_value(
        {
            "kind": "ratio",
            "recipe": {"numerator": "importe_venta", "denominator": "cantidad"},
        },
        values,
    )

    assert result == 110.0


class _KpiResolutionSession:
    async def scalar(self, statement: object, params: dict[str, object]) -> float:
        del params
        sql = str(statement)
        values = {
            'f."importe_neto"': 1100.0,
            'f."cantidad_vendida"': 10.0,
            'f."costo_total"': 650.0,
            'f."importe_bruto"': 1100.0,
        }
        return next(value for column, value in values.items() if column in sql)


@pytest.mark.asyncio
async def test_derived_kpis_resolve_declared_fact_measure_without_redundant_card() -> None:
    recipes = [
        {
            "code": "ventas_totales",
            "kind": "aggregate",
            "recipe": {"operation": "sum", "measure": "importe_neto"},
        },
        {
            "code": "unidades_totales",
            "kind": "aggregate",
            "recipe": {"operation": "sum", "measure": "cantidad_vendida"},
        },
        {
            "code": "costo_total",
            "kind": "aggregate",
            "recipe": {"operation": "sum", "measure": "costo_total"},
        },
        {
            "code": "margen_porcentaje",
            "kind": "share",
            "recipe": {
                "numerator": "margen_bruto",
                "denominator": "importe_bruto",
                "multiply_by": 100,
            },
        },
        {
            "code": "venta_por_unidad",
            "kind": "ratio",
            "recipe": {
                "numerator": "importe_bruto",
                "denominator": "cantidad_vendida",
            },
        },
        {
            "code": "margen_bruto",
            "kind": "difference",
            "recipe": {"minuend": "importe_bruto", "subtrahend": "costo_total"},
        },
    ]
    fact_document = {
        "measures": [
            {"name": "importe_neto", "aggregation": "sum"},
            {"name": "importe_bruto", "aggregation": "sum"},
            {"name": "cantidad_vendida", "aggregation": "sum"},
            {"name": "costo_total", "aggregation": "sum"},
        ]
    }

    values = await _resolve_kpi_values(
        _KpiResolutionSession(),  # type: ignore[arg-type]
        recipes,
        fact_document,
        {"importe_neto", "importe_bruto", "cantidad_vendida", "costo_total"},
        'FROM "mart_ventas_e11"."fact_ventas" f WHERE true',
        {},
    )

    assert values["margen_bruto"] == 450.0
    assert values["margen_porcentaje"] == pytest.approx(40.9090909)
    assert values["venta_por_unidad"] == 110.0


class _FakeResult:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def scalars(self) -> list[object]:
        return self.values

    def all(self) -> list[object]:
        return self.values


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.columns = {
            "fact_ventas": {
                "etl_execution_id",
                "dim_producto_sk",
                "dim_territorio_sk",
                "quantity",
            },
            "dim_producto": {"surrogate_key", "etl_execution_id", "name"},
            "dim_territorio": {"surrogate_key", "etl_execution_id", "group_es"},
        }

    async def execute(self, statement: object, params: dict[str, object]) -> _FakeResult:
        sql = str(statement)
        self.calls.append((sql, params))
        if "information_schema.columns" in sql:
            return _FakeResult(sorted(self.columns[str(params["table"])]))
        return _FakeResult(
            [
                SimpleNamespace(label="Bicicleta A", value=60),
                SimpleNamespace(label="Bicicleta B", value=25),
            ]
        )

    async def scalar(self, statement: object, params: dict[str, object]) -> int:
        self.calls.append((str(statement), params))
        return 100


@pytest.mark.asyncio
async def test_execution_catalog_requires_owned_physical_rows() -> None:
    session = _FakeSession()
    execution = SimpleNamespace(
        id=7,
        metrics_document={"destination_schema": "mart_ventas_e7"},
    )
    proposal = SimpleNamespace(proposal_document={"fact": {"name": "fact_ventas"}})

    assert await execution_has_materialized_data(
        session,
        execution,
        proposal,  # type: ignore[arg-type]
    )
    column_call = next(call for call in session.calls if "information_schema.columns" in call[0])
    assert column_call[1]["schema"] == "mart_ventas_e7"


@pytest.mark.asyncio
async def test_safe_aggregate_applies_non_visual_territory_and_full_denominator() -> None:
    session = _FakeSession()
    execution = SimpleNamespace(
        id=7,
        plan_document={
            "kpi_recipes": [
                {
                    "code": "total_units",
                    "name": "Unidades vendidas",
                    "kind": "aggregate",
                    "recipe": {"operation": "sum", "measure": "quantity"},
                }
            ]
        },
        metrics_document={
            "destination_schema": "mart_ventas_e7",
            "kpis": [{"code": "total_units", "unit": "unidades"}],
        },
    )
    proposal = SimpleNamespace(
        proposal_document={
            "fact": {"name": "fact_ventas"},
            "dimensions": [
                {"name": "dim_producto", "business_key": "name", "attributes": ["name"]},
                {
                    "name": "dim_territorio",
                    "business_key": "group_es",
                    "attributes": ["group_es"],
                },
            ],
        }
    )

    result = await run_safe_aggregate_query(
        session,  # type: ignore[arg-type]
        execution,  # type: ignore[arg-type]
        proposal,  # type: ignore[arg-type]
        metric_code="total_units",
        dimension="product",
        top_n=5,
        order="desc",
        year=None,
        territory="Europe",
    )

    assert result.territory == "Europe"
    assert result.top_n == 5
    assert result.denominator_value == 100
    assert result.points[0].share == 60
    grouped_call = next(call for call in session.calls if "GROUP BY 1" in call[0])
    assert 't."group_es" = :territory' in grouped_call[0]
    assert grouped_call[1]["territory"] == "Europe"
    assert grouped_call[1]["ranking_limit"] == 5
    assert "antes de limitar al Top 5" in result.denominator_definition
    assert '"mart_ventas_e7"."fact_ventas"' in grouped_call[0]
