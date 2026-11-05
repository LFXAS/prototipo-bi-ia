from __future__ import annotations

from copy import deepcopy

import pytest

from app.modules.copilot.needs import assess_business_need, requests_invoice_event


@pytest.mark.parametrize(
    ("goal", "expected"),
    [
        ("Analizar pedidos mensuales, sin asumir facturación.", False),
        ("Analizar pedidos y no facturas.", False),
        ("Analyze orders, not invoices.", False),
        ("Analyze orders without invoiced revenue.", False),
        ("Analizar facturas, no pedidos.", True),
        ("Analyze invoiced revenue, not orders.", True),
        ("No sólo facturas sino también pedidos.", True),
        ("Analizar importe sin excluir facturas.", True),
        ("Analizar importe; no excluir facturas.", True),
        ("Analyze amounts without excluding invoices.", True),
        ("Analyze amounts; do not exclude invoices.", True),
        ("Analizar importe; nunca incluir facturas.", False),
        ("Analyze amounts; never include invoices.", False),
    ],
)
def test_original_invoice_intent_distinguishes_positive_request_from_exclusion(goal, expected):
    business_request = request(goal)
    assert requests_invoice_event(business_request) is expected
    assessment = assess_business_need(DOCUMENT, business_request)
    assert (
        any(item["code"] == "goal:invoiced_sales" for item in assessment["requirements"])
        is expected
    )


def test_invoice_requested_by_original_question_is_not_lost():
    business_request = {
        "goal": "Comparar importes comerciales",
        "questions": [{"instruction": "Analizar facturas emitidas por mes, sin asumir cobros."}],
    }
    assert requests_invoice_event(business_request) is True


@pytest.mark.parametrize(
    "goal",
    [
        "Analizar importe; no excluir clientes ni productos, sin asumir costos.",
        "Analyze amounts; do not exclude customers nor products, without assuming costs.",
        "Analizar importe sin omitir clientes ni productos, excluyendo costos.",
        "Analyze amounts without omitting customers nor products, excluding costs.",
    ],
)
def test_negated_exclusion_keeps_all_entities_but_not_a_later_real_exclusion(goal):
    business_request = request(goal)
    business_request["questions"] = []
    requirements = assess_business_need(DOCUMENT, business_request)["requirements"]
    codes = {item["code"] for item in requirements}
    assert {"goal:customer", "goal:product"} <= codes
    assert not {"goal:unit_cost", "goal:total_cost", "goal:gross_margin"} & codes


@pytest.mark.parametrize(
    "goal",
    [
        "Conservar el importe de origen sin asumir moneda, utilidad ni composición fiscal. "
        "Limitar los indicadores a importe total, unidades totales, facturas distintas e "
        "importe promedio por factura.",
        "Keep the source amount without assuming currency, profit or tax composition. "
        "Limit indicators to total amount, total units, distinct invoices and average "
        "amount per invoice.",
    ],
)
def test_coordinated_caution_is_not_an_additional_margin_requirement(goal):
    business_request = request(goal)
    business_request["questions"] = []
    result = assess_business_need(DOCUMENT, business_request)
    requirements = {item["code"]: item for item in result["requirements"]}
    assert "goal:gross_margin" not in requirements
    assert "goal:unit_cost" not in requirements
    assert "goal:total_cost" not in requirements
    assert "goal:gross_margin" not in result["requires_acknowledgement"]
    assert {
        "goal:sales_amount",
        "goal:quantity",
        "goal:transactions",
        "goal:average_transaction",
        "goal:invoiced_sales",
    } <= requirements.keys()


@pytest.mark.parametrize(
    ("goal", "absent"),
    [
        (
            "Analizar ventas sin calcular costos ni descuentos.",
            {"unit_cost", "total_cost", "discount_amount"},
        ),
        (
            "Analyze sales without calculating costs or discounts.",
            {"unit_cost", "total_cost", "discount_amount"},
        ),
        (
            "Analizar ventas, no clientes, productos ni territorios.",
            {"customer", "product", "territory"},
        ),
        (
            "Analyze sales, not customers, products or territories.",
            {"customer", "product", "territory"},
        ),
        (
            "Comparar importe; excluir promedio por pedido y venta por unidad.",
            {"average_transaction", "sales_per_unit", "transactions", "quantity"},
        ),
        (
            "Compare amount; exclude average per order and sales per unit.",
            {"average_transaction", "sales_per_unit", "transactions", "quantity"},
        ),
        ("Analizar ventas sin cantidades ni fechas.", {"quantity", "date"}),
        ("Analyze sales without quantities or dates.", {"quantity", "date"}),
    ],
)
def test_exclusions_apply_to_all_capabilities_and_derived_formulas(goal, absent):
    business_request = request(goal)
    business_request["questions"] = []
    business_request["periodicity"] = {}
    result = assess_business_need(DOCUMENT, business_request)
    codes = {item["code"] for item in result["requirements"]}
    assert "goal:sales_amount" in codes
    assert not {f"goal:{capability}" for capability in absent} & codes


@pytest.mark.parametrize(
    "goal",
    [
        "Sin asumir moneda, calcular utilidad por producto.",
        "Without assuming currency, calculate profit by product.",
        "No analizar descuentos, sino margen por producto.",
        "Do not analyze discounts, but compare margin by product.",
        "No sólo ventas sino también utilidad por producto.",
        "Not only sales but also profit by product.",
        "Analizar ventas sin moneda y calcular margen por producto.",
        "Analyze sales without currency and calculate margin by product.",
        "No calcular utilidad. Comparar margen por producto.",
        "Do not calculate profit. Compare margin by product.",
    ],
)
def test_positive_margin_request_survives_exclusions_and_correlative_language(goal):
    document = deepcopy(DOCUMENT)
    document["schemas"][1]["tables"][0]["columns"] = [{"name": "ProductID", "data_type": "int"}]
    business_request = request(goal)
    business_request["questions"] = []
    result = assess_business_need(document, business_request)
    requirements = {item["code"]: item for item in result["requirements"]}
    assert requirements["goal:gross_margin"]["status"] == "unavailable"
    assert "goal:gross_margin" in result["requires_acknowledgement"]


@pytest.mark.parametrize("code", ["top_products", "custom_comparison"])
@pytest.mark.parametrize(
    "instruction",
    [
        "Comparar ventas por producto sin asumir costos, clientes ni cantidades.",
        "Compare sales by product without assuming costs, customers or quantity.",
    ],
)
def test_selected_question_scans_positive_instructions_without_readding_exclusions(
    code, instruction
):
    business_request = request("Comparar ventas por producto.")
    business_request["questions"] = [{"code": code, "instruction": instruction}]
    result = assess_business_need(DOCUMENT, business_request)
    question = next(item for item in result["requirements"] if item["code"] == f"question:{code}")
    assert set(question["components"]) == {"sales_amount", "product"}


def test_positive_selected_question_is_not_erased_by_an_opposite_goal_caution():
    business_request = request("Comparar ventas sin asumir costos.")
    business_request["questions"] = [
        {"code": "custom_cost", "instruction": "Calcular costos por producto."}
    ]
    result = assess_business_need(DOCUMENT, business_request)
    question = next(
        item for item in result["requirements"] if item["code"] == "question:custom_cost"
    )
    assert "unit_cost" in question["components"]


def test_question_with_only_exclusions_stays_ambiguous_without_fabricated_components():
    business_request = request("Comparar ventas por producto.")
    business_request["questions"] = [
        {"code": "custom_caution", "instruction": "No asumir utilidad, costos ni demanda."}
    ]
    result = assess_business_need(DOCUMENT, business_request)
    question = next(
        item for item in result["requirements"] if item["code"] == "question:custom_caution"
    )
    assert question["status"] == "ambiguous"
    assert question["components"] == []


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


def test_average_per_transaction_requires_sales_and_distinct_documents() -> None:
    result = assess_business_need(
        DOCUMENT,
        request("Comparar el importe promedio por transacción cada mes."),
    )
    requirements = {item["code"]: item for item in result["requirements"]}
    assert requirements["goal:average_transaction"]["status"] == "derivable"
    assert requirements["goal:average_transaction"]["components"] == [
        "sales_amount",
        "transactions",
    ]


def test_invoiced_sales_is_not_equated_with_orders() -> None:
    document = deepcopy(DOCUMENT)
    document["schemas"][0]["tables"].append(
        {
            "name": "InvoiceLines",
            "columns": [{"name": "InvoiceLineID"}, {"name": "InvoiceID"}],
            "foreign_keys": [],
        }
    )
    result = assess_business_need(
        document,
        request("Analizar ventas facturadas y promedio por factura distinta."),
    )
    requirements = {item["code"]: item for item in result["requirements"]}
    assert requirements["goal:invoiced_sales"]["status"] == "unavailable"
    assert requirements["goal:invoiced_sales"]["components"] == ["invoice_event"]
    assert requirements["goal:average_transaction"]["status"] == "unavailable"
    assert "goal:invoiced_sales" in result["requires_acknowledgement"]

    missing = assess_business_need(
        DOCUMENT,
        request("Analizar ventas facturadas y promedio por factura distinta."),
    )
    missing_requirements = {item["code"]: item for item in missing["requirements"]}
    assert missing_requirements["goal:invoiced_sales"]["status"] == "unavailable"


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


def test_assessment_keeps_sales_evidence_in_one_coherent_subgraph() -> None:
    document = {
        "schemas": [
            {
                "name": "Purchasing",
                "tables": [
                    {
                        "name": "PurchaseOrderDetail",
                        "columns": [
                            {"name": "PurchaseOrderID"},
                            {"name": "OrderQty", "data_type": "int"},
                            {"name": "LineTotal", "data_type": "decimal"},
                        ],
                        "foreign_keys": [
                            {
                                "columns": ["PurchaseOrderID"],
                                "referenced_schema": "Purchasing",
                                "referenced_table": "PurchaseOrderHeader",
                                "referenced_columns": ["PurchaseOrderID"],
                            }
                        ],
                    },
                    {
                        "name": "PurchaseOrderHeader",
                        "columns": [{"name": "PurchaseOrderID"}, {"name": "OrderDate"}],
                        "foreign_keys": [],
                    },
                ],
            },
            {
                "name": "CommercialSales",
                "tables": [
                    {
                        "name": "InvoiceLine",
                        "columns": [
                            {"name": "SalesOrderID"},
                            {"name": "OrderQty", "data_type": "int"},
                            {"name": "LineTotal", "data_type": "decimal"},
                        ],
                        "foreign_keys": [
                            {
                                "columns": ["SalesOrderID"],
                                "referenced_schema": "CommercialSales",
                                "referenced_table": "InvoiceHeader",
                                "referenced_columns": ["SalesOrderID"],
                            }
                        ],
                    },
                    {
                        "name": "InvoiceHeader",
                        "columns": [
                            {"name": "SalesOrderID"},
                            {"name": "OrderDate", "data_type": "date"},
                            {"name": "CustomerID"},
                        ],
                        "foreign_keys": [],
                    },
                ],
            },
        ]
    }
    business_request = {
        "snapshot_hash": "b" * 64,
        "goal": "Analizar ventas mensuales por cliente.",
        "questions": [
            {
                "code": "sales_over_time",
                "label": "Evolución de ventas en el tiempo",
                "description": "Comparar ventas por período.",
                "instruction": "Conservar el detalle.",
            }
        ],
        "periodicity": {"code": "month", "label": "Mensual"},
    }

    result = assess_business_need(document, business_request)

    requirement = next(
        item for item in result["requirements"] if item["code"] == "question:sales_over_time"
    )
    assert requirement["status"] == "derivable"
    assert "CommercialSales.InvoiceLine.LineTotal" in requirement["evidence"]
    assert "CommercialSales.InvoiceHeader.OrderDate" in requirement["evidence"]
    assert not any("Purchasing" in evidence for evidence in requirement["evidence"])


def test_assessment_derives_sales_without_database_specific_names() -> None:
    document = {
        "schemas": [
            {
                "name": "Commerce",
                "tables": [
                    {
                        "name": "OrderLines",
                        "columns": [
                            {"name": "OrderLineID", "data_type": "int"},
                            {"name": "OrderID", "data_type": "int"},
                            {"name": "StockItemID", "data_type": "int"},
                            {"name": "Quantity", "data_type": "int"},
                            {"name": "UnitPrice", "data_type": "decimal"},
                        ],
                        "foreign_keys": [
                            {
                                "columns": ["OrderID"],
                                "referenced_schema": "Commerce",
                                "referenced_table": "Orders",
                                "referenced_columns": ["OrderID"],
                            },
                            {
                                "columns": ["StockItemID"],
                                "referenced_schema": "Inventory",
                                "referenced_table": "StockItems",
                                "referenced_columns": ["StockItemID"],
                            },
                        ],
                    },
                    {
                        "name": "Orders",
                        "columns": [
                            {"name": "OrderID", "data_type": "int"},
                            {"name": "OrderDate", "data_type": "date"},
                            {"name": "CustomerID", "data_type": "int"},
                        ],
                        "foreign_keys": [],
                    },
                ],
            },
            {
                "name": "Inventory",
                "tables": [
                    {
                        "name": "StockItems",
                        "columns": [
                            {"name": "StockItemID", "data_type": "int"},
                            {"name": "StockItemName", "data_type": "nvarchar"},
                        ],
                        "foreign_keys": [],
                    },
                    {
                        "name": "StockItemHoldings",
                        "columns": [
                            {"name": "StockItemID", "data_type": "int"},
                            {"name": "LastCostPrice", "data_type": "decimal"},
                        ],
                        "foreign_keys": [
                            {
                                "columns": ["StockItemID"],
                                "referenced_schema": "Inventory",
                                "referenced_table": "StockItems",
                                "referenced_columns": ["StockItemID"],
                            }
                        ],
                    },
                ],
            },
        ]
    }
    business_request = {
        "snapshot_hash": "c" * 64,
        "goal": "Analizar ventas, unidades, costos y margen por producto y período.",
        "questions": [],
        "periodicity": {"code": "month", "label": "Mensual"},
    }

    result = assess_business_need(document, business_request)

    requirements = {item["code"]: item for item in result["requirements"]}
    assert requirements["goal:sales_amount"]["status"] == "derivable"
    assert requirements["goal:sales_amount"]["resolution"] == (
        "Puede calcularse de forma controlada como precio unitario × cantidad."
    )
    assert "Commerce.OrderLines.UnitPrice" in requirements["goal:sales_amount"]["evidence"]
    assert "Commerce.OrderLines.Quantity" in requirements["goal:sales_amount"]["evidence"]
    # The cost table points to the product, not the other way around. Without
    # evidence of one-to-one cardinality a reverse path could multiply sales.
    assert requirements["goal:unit_cost"]["status"] == "unavailable"
    assert requirements["goal:gross_margin"]["status"] == "unavailable"


def test_disconnected_components_cannot_claim_a_calculable_margin() -> None:
    document = deepcopy(DOCUMENT)
    document["schemas"][0]["tables"][0]["foreign_keys"] = []
    result = assess_business_need(
        document, request("Analizar ventas, costos y margen por producto.")
    )
    requirements = {item["code"]: item for item in result["requirements"]}

    assert requirements["goal:unit_cost"]["status"] == "unavailable"
    assert requirements["goal:product"]["evidence"] == ["Sales.SalesOrderDetail.ProductID"]
    assert requirements["goal:gross_margin"]["status"] == "unavailable"
    assert "goal:gross_margin" in result["requires_acknowledgement"]


def test_numeric_and_temporal_names_do_not_override_incompatible_types() -> None:
    document = deepcopy(DOCUMENT)
    detail = document["schemas"][0]["tables"][0]
    for column in detail["columns"]:
        if column["name"] in {"LineTotal", "OrderQty"}:
            column["data_type"] = "nvarchar"
    detail["columns"].append({"name": "OrderDate", "data_type": "nvarchar"})
    result = assess_business_need(document, request("Analizar ventas y unidades mensuales."))
    requirements = {item["code"]: item for item in result["requirements"]}

    for code in ("sales_amount", "quantity", "date"):
        assert requirements[f"goal:{code}"]["status"] == "unavailable"


def test_legacy_missing_types_are_pending_confirmation_not_proof() -> None:
    document = deepcopy(DOCUMENT)
    for column in document["schemas"][0]["tables"][0]["columns"]:
        column.pop("data_type", None)
    result = assess_business_need(document, request("Analizar ventas y unidades por producto."))
    requirements = {item["code"]: item for item in result["requirements"]}

    assert requirements["goal:sales_amount"]["status"] == "ambiguous"
    assert "goal:sales_amount" in result["requires_acknowledgement"]
    assert "tipos" in requirements["goal:sales_amount"]["resolution"]


def test_purchase_only_metadata_does_not_prove_sales() -> None:
    document = deepcopy(DOCUMENT)
    document["schemas"][0]["name"] = "Purchasing"
    document["schemas"][0]["tables"][0]["name"] = "PurchaseOrderDetail"
    result = assess_business_need(document, request("Analizar ventas y unidades por producto."))
    requirements = {item["code"]: item for item in result["requirements"]}

    assert requirements["goal:sales_amount"]["status"] == "unavailable"
    assert requirements["goal:quantity"]["status"] == "unavailable"
    assert not any("Purchase" in ref for item in result["requirements"] for ref in item["evidence"])


def test_invoice_requirement_uses_invoice_amount_identity_and_date_together() -> None:
    document = deepcopy(DOCUMENT)
    document["schemas"][0]["tables"].extend(
        [
            {
                "name": "InvoiceLines",
                "columns": [
                    {"name": "InvoiceID", "data_type": "int"},
                    {"name": "ExtendedPrice", "data_type": "decimal"},
                    {"name": "Quantity", "data_type": "int"},
                ],
                "foreign_keys": [
                    {
                        "columns": ["InvoiceID"],
                        "referenced_schema": "Sales",
                        "referenced_table": "Invoices",
                        "referenced_columns": ["InvoiceID"],
                    }
                ],
            },
            {
                "name": "Invoices",
                "columns": [
                    {"name": "InvoiceID", "data_type": "int"},
                    {"name": "InvoiceDate", "data_type": "date"},
                    {"name": "OrderDate", "data_type": "date"},
                ],
                "foreign_keys": [],
            },
        ]
    )
    result = assess_business_need(
        document, request("Analizar ventas facturadas mensuales y promedio por factura.")
    )
    requirements = {item["code"]: item for item in result["requirements"]}

    assert requirements["goal:invoiced_sales"]["status"] == "derivable"
    evidence = requirements["goal:invoiced_sales"]["evidence"]
    assert "Sales.InvoiceLines.ExtendedPrice" in evidence
    assert "Sales.InvoiceLines.InvoiceID" in evidence
    assert "Sales.Invoices.InvoiceDate" in evidence
    assert not any("Order" in ref for ref in evidence)
    assert requirements["goal:average_transaction"]["status"] == "derivable"


def test_general_spanish_metadata_and_english_goal_are_supported() -> None:
    document = {
        "schemas": [
            {
                "name": "Comercial",
                "tables": [
                    {
                        "name": "Facturas",
                        "columns": [
                            {"name": "IdFactura", "data_type": "int"},
                            {"name": "ImporteTotal", "data_type": "numeric(12,2)"},
                            {"name": "CantidadVendida", "data_type": "integer"},
                            {"name": "FechaEmision", "data_type": "date"},
                            {"name": "IdCliente", "data_type": "int"},
                        ],
                        "foreign_keys": [],
                    }
                ],
            }
        ]
    }
    business_request = request(
        "Analyze monthly invoiced revenue, units and average per invoice by customer."
    )
    business_request["questions"] = []
    result = assess_business_need(document, business_request)
    requirements = {item["code"]: item for item in result["requirements"]}

    assert requirements["goal:invoiced_sales"]["status"] == "derivable"
    assert requirements["goal:sales_amount"]["status"] == "direct"
    assert requirements["goal:quantity"]["status"] == "direct"
    assert requirements["goal:customer"]["status"] == "direct"
    assert requirements["goal:average_transaction"]["status"] == "derivable"
    assert result["requires_acknowledgement"] == []
    assert "no garantiza cobertura completa" in result["summary"]


def test_viability_does_not_depend_on_metadata_table_order() -> None:
    document = deepcopy(DOCUMENT)
    business_request = request("Analizar ventas y costos por producto.")
    original = assess_business_need(document, business_request)
    document["schemas"].reverse()
    for schema in document["schemas"]:
        schema["tables"].reverse()
        for table in schema["tables"]:
            table["columns"].reverse()

    assert assess_business_need(document, business_request) == original


def test_reverse_foreign_key_does_not_make_header_sales_compatible_with_line_grain() -> None:
    document = {
        "schemas": [
            {
                "name": "Sales",
                "tables": [
                    {
                        "name": "Orders",
                        "columns": [
                            {"name": "OrderID", "data_type": "int", "primary_key": True},
                            {"name": "SalesAmount", "data_type": "decimal"},
                        ],
                        "foreign_keys": [],
                    },
                    {
                        "name": "Lines",
                        "columns": [
                            {"name": "OrderID", "data_type": "int"},
                            {"name": "ProductID", "data_type": "int"},
                            {"name": "Quantity", "data_type": "int"},
                        ],
                        "foreign_keys": [
                            {
                                "columns": ["OrderID"],
                                "referenced_schema": "Sales",
                                "referenced_table": "Orders",
                                "referenced_columns": ["OrderID"],
                            }
                        ],
                    },
                ],
            }
        ]
    }
    result = assess_business_need(document, request("Analizar ventas por producto y unidades."))
    requirements = {item["code"]: item for item in result["requirements"]}

    assert requirements["goal:sales_amount"]["status"] == "direct"
    assert requirements["goal:product"]["status"] == "unavailable"
    assert requirements["question:top_products"]["status"] == "unavailable"


def test_amount_alias_on_coherent_fact_wins_over_first_global_alias() -> None:
    document = deepcopy(DOCUMENT)
    detail = document["schemas"][0]["tables"][0]
    for column in detail["columns"]:
        if column["name"] == "LineTotal":
            column["name"] = "SalesAmount"
    document["schemas"][0]["tables"].append(
        {
            "name": "DailyTotals",
            "columns": [{"name": "LineTotal", "data_type": "decimal"}],
            "foreign_keys": [],
        }
    )
    result = assess_business_need(document, request("Analizar ventas por producto y unidades."))
    requirements = {item["code"]: item for item in result["requirements"]}

    assert requirements["goal:sales_amount"]["status"] == "direct"
    assert requirements["goal:sales_amount"]["evidence"] == ["Sales.SalesOrderDetail.SalesAmount"]
    assert requirements["question:top_products"]["status"] == "derivable"


def test_an_unrelated_date_name_is_not_proof_of_sales_time() -> None:
    document = deepcopy(DOCUMENT)
    document["schemas"][0]["tables"][0]["columns"].append(
        {
            "name": "BirthDate",
            "data_type": "date",
        }
    )
    result = assess_business_need(document, request("Analizar ventas mensuales por producto."))
    requirements = {item["code"]: item for item in result["requirements"]}

    assert requirements["goal:date"]["status"] == "ambiguous"


def test_commercial_header_date_wins_over_audit_date_on_fact_only_when_reachable() -> None:
    document = deepcopy(DOCUMENT)
    detail = document["schemas"][0]["tables"][0]
    detail["columns"].append({"name": "ModifiedDate", "data_type": "datetime"})
    document["schemas"][0]["tables"].append(
        {
            "name": "OrderHeader",
            "columns": [
                {"name": "SalesOrderID", "data_type": "int", "primary_key": True},
                {"name": "OrderDate", "data_type": "date"},
            ],
            "foreign_keys": [],
        }
    )
    detail["foreign_keys"].append(
        {
            "columns": ["SalesOrderID"],
            "referenced_schema": "Sales",
            "referenced_table": "OrderHeader",
            "referenced_columns": ["SalesOrderID"],
        }
    )
    business_request = request("Analizar ventas mensuales por producto y conservar pedidos.")

    result = assess_business_need(document, business_request)
    temporal = next(item for item in result["requirements"] if item["code"] == "goal:date")
    assert temporal["status"] == "direct"
    assert "Sales.OrderHeader.OrderDate" in temporal["evidence"]
    assert not any("ModifiedDate" in ref for ref in temporal["evidence"])

    detail["foreign_keys"].pop()
    disconnected = assess_business_need(document, business_request)
    temporal = next(item for item in disconnected["requirements"] if item["code"] == "goal:date")
    assert temporal["status"] == "ambiguous"
    assert temporal["evidence"] == ["Sales.SalesOrderDetail.ModifiedDate"]


def test_selected_periodicity_requires_a_reachable_date_even_when_goal_omits_time() -> None:
    document = deepcopy(DOCUMENT)
    document["schemas"][0]["tables"].append(
        {
            "name": "OtherEvents",
            "columns": [{"name": "OrderDate", "data_type": "date"}],
            "foreign_keys": [],
        }
    )
    business_request = request(
        "Comparar ventas y unidades por producto para priorizar el catálogo."
    )

    for periodicity in ("day", "week", "month", "quarter", "year"):
        business_request["periodicity"] = {"code": periodicity}
        result = assess_business_need(document, business_request)
        temporal = next(item for item in result["requirements"] if item["code"] == "goal:date")
        assert temporal["status"] == "unavailable"
        assert temporal["evidence"] == []
        assert "goal:date" in result["requires_acknowledgement"]
