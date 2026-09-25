from __future__ import annotations

from copy import deepcopy

from app.modules.copilot.needs import assess_business_need

DOCUMENT = {
    "schemas": [
        {
            "name": "Sales",
            "tables": [
                {
                    "name": "SalesOrderDetail",
                    "columns": [
                        {"name": "SalesOrderDetailID", "data_type": "int"},
                        {"name": "SalesOrderID", "data_type": "int"},
                        {"name": "ProductID", "data_type": "int"},
                        {"name": "OrderQty", "data_type": "smallint"},
                        {"name": "LineTotal", "data_type": "numeric"},
                        {"name": "UnitPriceDiscount", "data_type": "numeric"},
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
                        {"name": "StandardCost", "data_type": "money"},
                    ],
                    "foreign_keys": [],
                }
            ],
        },
    ]
}


def request(goal: str) -> dict[str, object]:
    return {
        "snapshot_hash": "a" * 64,
        "goal": goal,
        "questions": [
            {
                "code": "top_products",
                "label": "Productos con mayor desempeño",
                "description": "Comparar productos por ventas y unidades.",
                "instruction": "Ordenar productos por importe o unidades vendidas.",
            }
        ],
        "periodicity": {"code": "month", "label": "Mensual"},
    }


def test_assessment_classifies_direct_and_derived_requirements() -> None:
    result = assess_business_need(
        DOCUMENT,
        request("Analizar ventas, costos, margen y venta por unidad por producto."),
    )

    requirements = {item["code"]: item for item in result["requirements"]}
    assert requirements["goal:sales_amount"]["status"] == "direct"
    assert requirements["goal:unit_cost"]["status"] == "direct"
    assert requirements["goal:gross_margin"]["status"] == "derivable"
    assert requirements["goal:sales_per_unit"]["formula"] == ("ventas netas ÷ unidades vendidas")
    assert result["can_continue"] is True
    assert len(result["assessment_hash"]) == 64


def test_assessment_never_hides_an_unavailable_cost_requirement() -> None:
    document = deepcopy(DOCUMENT)
    product = document["schemas"][1]["tables"][0]
    product["columns"] = [
        column for column in product["columns"] if column["name"] != "StandardCost"
    ]

    result = assess_business_need(
        document,
        request("Analizar ventas, costos y rentabilidad por producto."),
    )

    requirements = {item["code"]: item for item in result["requirements"]}
    assert requirements["goal:unit_cost"]["status"] == "unavailable"
    assert requirements["goal:gross_margin"]["status"] == "unavailable"
    assert "goal:unit_cost" in result["requires_acknowledgement"]
    assert "incorpore una fuente real" in requirements["goal:unit_cost"]["resolution"]


def test_assessment_marks_unrecognized_custom_question_as_ambiguous() -> None:
    business_request = request("Analizar ventas por producto.")
    business_request["questions"] = [
        {
            "code": "custom_question",
            "label": "Conocer el desempeño estratégico",
            "description": "Evaluar el comportamiento estratégico del negocio.",
            "instruction": "Explicar el desempeño estratégico.",
        }
    ]

    result = assess_business_need(DOCUMENT, business_request)

    requirement = next(
        item for item in result["requirements"] if item["code"] == "question:custom_question"
    )
    assert requirement["status"] == "ambiguous"
    assert requirement["evidence"] == []


def test_assessment_hash_changes_when_the_need_changes() -> None:
    first = assess_business_need(DOCUMENT, request("Analizar ventas por producto."))
    second = assess_business_need(DOCUMENT, request("Analizar ventas y costos por producto."))

    assert first["assessment_hash"] != second["assessment_hash"]
