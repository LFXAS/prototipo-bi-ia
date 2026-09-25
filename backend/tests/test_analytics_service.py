from types import SimpleNamespace

import pytest

from app.modules.analytics.service import _derived_recipe_value, run_safe_aggregate_query


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
        metrics_document={"kpis": [{"code": "total_units", "unit": "unidades"}]},
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
