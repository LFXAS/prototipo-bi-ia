from app.modules.analytics.service import _derived_recipe_value


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
