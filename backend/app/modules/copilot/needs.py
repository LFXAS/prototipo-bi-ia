from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import deque
from typing import Any

NeedStatus = str
ColumnEvidence = tuple[str, str, str, str]

NUMERIC_TYPES = {
    "tinyint",
    "smallint",
    "int",
    "integer",
    "bigint",
    "decimal",
    "numeric",
    "money",
    "smallmoney",
    "float",
    "real",
    "double",
    "double precision",
    "number",
}
TEMPORAL_TYPES = {"date", "datetime", "datetime2", "smalldatetime", "datetimeoffset"}
NUMERIC_CAPABILITIES = {"sales_amount", "quantity", "unit_cost", "unit_price", "discount_rate"}


def _plain(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _compact(value: object) -> str:
    return _plain(value).replace(" ", "")


def _tables(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for schema in document.get("schemas", []):
        if not isinstance(schema, dict):
            continue
        schema_name = str(schema.get("name", ""))
        for table in schema.get("tables", []):
            if isinstance(table, dict):
                result[f"{schema_name}.{table.get('name', '')}"] = table
    return result


def _column_index(tables: dict[str, dict[str, Any]]) -> list[ColumnEvidence]:
    return [
        (
            reference,
            str(column.get("name", "")),
            _compact(column.get("name", "")),
            re.sub(r"\([^)]*\)", "", str(column.get("data_type", ""))).strip().casefold(),
        )
        for reference, table in tables.items()
        for column in table.get("columns", [])
        if isinstance(column, dict) and column.get("name")
    ]


def _graph(tables: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {reference: set() for reference in tables}
    for source, table in tables.items():
        for relation in table.get("foreign_keys", []):
            if not isinstance(relation, dict):
                continue
            relation_columns = {
                _compact(column)
                for column in [
                    *relation.get("columns", []),
                    *relation.get("referenced_columns", []),
                ]
            }
            if relation_columns & {
                "createdby",
                "lasteditedby",
                "modifiedby",
                "updatedby",
            }:
                continue
            target = (
                f"{relation.get('referenced_schema', '')}.{relation.get('referenced_table', '')}"
            )
            source_columns = {str(item.get("name")) for item in table.get("columns", [])}
            target_columns = {
                str(item.get("name")) for item in tables.get(target, {}).get("columns", [])
            }
            left = relation.get("columns", [])
            right = relation.get("referenced_columns", [])
            if (
                target in tables
                and left
                and len(left) == len(right)
                and set(left) <= source_columns
                and set(right) <= target_columns
            ):
                # A declared FK follows the many-to-one direction. The reverse
                # traversal can multiply the fact grain and is not evidence here.
                graph[source].add(target)
    return graph


def _path(graph: dict[str, set[str]], starts: set[str], destinations: set[str]) -> list[str]:
    queue = deque((start, [start]) for start in sorted(starts))
    visited = set(starts)
    while queue:
        current, route = queue.popleft()
        if current in destinations:
            return route
        for neighbor in sorted(graph.get(current, set())):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, [*route, neighbor]))
    return []


def _sales_context_score(reference: str) -> int:
    """Prefer a sales subgraph without depending on one product's table names."""
    normalized = _compact(reference)
    positive = (
        "sales",
        "venta",
        "revenue",
        "invoice",
        "order",
        "commerce",
        "commercial",
        "billing",
        "customer",
        "cliente",
    )
    negative = (
        "purchase",
        "purchasing",
        "procurement",
        "vendor",
        "proveedor",
        "compra",
        "stockitemtransaction",
        "inventorytransaction",
    )
    return sum(token in normalized for token in positive) - sum(
        token in normalized for token in negative
    )


def _non_sales_event(reference: str) -> bool:
    return any(
        token in _compact(reference)
        for token in (
            "purchase",
            "purchasing",
            "procurement",
            "compra",
            "stockitemtransaction",
            "inventorytransaction",
            "movimientoinventario",
        )
    )


def _invoice_index(index: list[ColumnEvidence]) -> list[ColumnEvidence]:
    """Keep invoice event measures separate from order and purchasing evidence."""
    invoice_tables = {
        table
        for table, _, name, _ in index
        if "invoice" in _compact(table)
        or "factura" in _compact(table)
        or name in {"invoiceid", "facturaid", "idfactura"}
    }
    event_columns = {
        (table, column)
        for capability in (
            "sales_amount",
            "quantity",
            "unit_price",
            "discount_rate",
            "transactions",
            "date",
        )
        for table, column in _find_columns(index, capability)
    }
    return [
        item
        for item in index
        if (item[0], item[1]) not in event_columns
        or (
            item[0] in invoice_tables
            and not any(
                token in item[2]
                for token in ("orderid", "pedidoid", "idpedido", "orderdate", "fechapedido")
            )
        )
    ]


def _coherent_anchor(
    index: list[ColumnEvidence],
    graph: dict[str, set[str]],
    components: list[str],
) -> set[str]:
    """Choose one evidence subgraph that can explain the complete business need."""
    anchor_capability = next(
        (
            capability
            for capability in dict.fromkeys(
                ("sales_amount", "quantity", "transactions", "unit_price", *components)
            )
            if capability in components and _find_columns(index, capability)
        ),
        None,
    )
    if anchor_capability is None:
        return set()
    anchors = sorted({table for table, _ in _find_columns(index, anchor_capability)})
    ranked: list[tuple[int, int, int, str]] = []
    for anchor in anchors:
        missing = 0
        distance = 0
        for component in dict.fromkeys(components):
            destinations = {table for table, _ in _find_columns(index, component)}
            route = _path(graph, {anchor}, destinations) if destinations else []
            if not route:
                missing += 1
            else:
                distance += len(route) - 1
        # Business coherence wins over a merely shorter route. Operational databases
        # often connect sales, purchases and inventory through shared entities; choosing
        # by distance first can therefore explain a sales request with the wrong event.
        ranked.append((missing, -_sales_context_score(anchor), distance, anchor))
    return {min(ranked)[3]} if ranked else set()


def _nearest_match(
    matches: list[tuple[str, str]],
    anchors: set[str],
    graph: dict[str, set[str]],
) -> tuple[tuple[str, str] | None, list[str]]:
    if not matches:
        return None, []
    ranked: list[tuple[int, int, int, str, str, list[str]]] = []
    for position, (table, column) in enumerate(matches):
        route = _path(graph, anchors, {table}) if anchors else [table]
        if route:
            ranked.append(
                (len(route) - 1, -_sales_context_score(table), position, table, column, route)
            )
    if not ranked:
        return None, []
    _, _, _, table, column, route = min(ranked)
    return (table, column), route


CAPABILITIES: dict[str, dict[str, object]] = {
    "sales_amount": {
        "label": "Ventas o ingresos",
        "triggers": (
            "venta",
            "ventas",
            "ingreso",
            "ingresos",
            "facturacion",
            "importe",
            "sales",
            "revenue",
            "amount",
            "invoiced",
        ),
        "columns": (
            "linetotal",
            "extendedprice",
            "salesamount",
            "salestotal",
            "importetotal",
            "totalventa",
            "importeventa",
            "subtotal",
            "totaldue",
            "revenue",
        ),
    },
    "quantity": {
        "label": "Unidades vendidas",
        "triggers": (
            "unidad",
            "unidades",
            "cantidad",
            "cantidades",
            "volumen",
            "units",
            "quantity",
            "volume",
        ),
        "columns": ("orderqty", "quantity", "qty", "cantidadvendida", "cantidad", "units"),
    },
    "transactions": {
        "label": "Número de transacciones o pedidos",
        "triggers": (
            "pedido",
            "pedidos",
            "transaccion",
            "transacciones",
            "ordenes",
            "factura",
            "facturas",
            "invoice",
            "invoices",
            "order",
            "orders",
            "transaction",
            "transactions",
        ),
        "columns": (
            "salesorderid",
            "orderid",
            "transactionid",
            "pedidoid",
            "invoiceid",
            "facturaid",
            "idfactura",
            "idpedido",
            "idtransaccion",
        ),
    },
    "date": {
        "label": "Evolución temporal",
        "triggers": (
            "tiempo",
            "fecha",
            "periodo",
            "mensual",
            "trimestral",
            "anual",
            "tendencia",
            "monthly",
            "quarterly",
            "yearly",
            "annual",
            "daily",
            "date",
            "period",
            "time",
        ),
        "columns": (
            "invoicedate",
            "fechafactura",
            "fechaemision",
            "orderdate",
            "salesdate",
            "transactiondate",
            "fechaventa",
            "fecha",
            "date",
        ),
    },
    "product": {
        "label": "Análisis por producto",
        "triggers": (
            "producto",
            "productos",
            "articulo",
            "articulos",
            "product",
            "products",
            "item",
            "items",
        ),
        "columns": (
            "productid",
            "itemid",
            "stockitemid",
            "productnumber",
            "productname",
            "itemname",
            "stockitemname",
            "idproducto",
            "idarticulo",
            "nombreproducto",
            "nombrearticulo",
        ),
    },
    "customer": {
        "label": "Análisis por cliente",
        "triggers": (
            "cliente",
            "clientes",
            "comprador",
            "compradores",
            "customer",
            "customers",
            "client",
            "clients",
        ),
        "columns": (
            "customerid",
            "clientid",
            "idcliente",
            "nombrecliente",
            "customername",
            "personid",
            "accountnumber",
        ),
    },
    "territory": {
        "label": "Análisis territorial",
        "triggers": (
            "territorio",
            "territorios",
            "region",
            "regiones",
            "pais",
            "geograf",
            "territory",
            "territories",
            "country",
            "geograph",
        ),
        "columns": (
            "territoryid",
            "regionid",
            "countryregioncode",
            "territoryname",
            "salesterritory",
            "countryid",
            "stateprovinceid",
            "cityid",
            "idterritorio",
            "idregion",
            "idpais",
            "idciudad",
        ),
    },
    "unit_cost": {
        "label": "Costo unitario",
        "triggers": ("costo", "costos", "coste", "costes", "cost", "costs"),
        "columns": (
            "standardcost",
            "unitcost",
            "productcost",
            "lastcostprice",
            "costprice",
            "costo",
            "costounitario",
            "costeunitario",
        ),
    },
    "unit_price": {
        "label": "Precio unitario",
        "triggers": (),
        "columns": ("unitprice", "salesprice", "preciounitario", "precio"),
    },
    "discount_rate": {
        "label": "Descuento",
        "triggers": ("descuento", "descuentos", "discount", "discounts"),
        "columns": (
            "unitpricediscount",
            "discountrate",
            "discountpct",
            "tasadescuento",
            "porcentajedescuento",
        ),
    },
}


def _matches(text: str, values: tuple[str, ...]) -> bool:
    words = set(text.split())
    return any(value in words or value in text for value in values)


def _find_columns(index: list[ColumnEvidence], capability: str) -> list[tuple[str, str]]:
    patterns = CAPABILITIES[capability]["columns"]
    assert isinstance(patterns, tuple)
    expected_types = (
        NUMERIC_TYPES
        if capability in NUMERIC_CAPABILITIES
        else TEMPORAL_TYPES
        if capability == "date"
        else None
    )
    candidates = [
        item for item in index if not item[3] or expected_types is None or item[3] in expected_types
    ]
    exact_tables = {table for table, _, name, _ in candidates if name in patterns}
    ranked = [
        (patterns.index(name) if name in patterns else len(patterns), table, column)
        for table, column, name, _ in candidates
        if name in patterns
        or (table not in exact_tables and any(str(pattern) in name for pattern in patterns))
    ]
    return [(table, column) for _, table, column in sorted(ranked)]


def _component(
    capability: str,
    index: list[ColumnEvidence],
    graph: dict[str, set[str]],
    anchors: set[str],
) -> tuple[NeedStatus, list[str], str]:
    matches = _find_columns(index, capability)
    patterns = CAPABILITIES[capability]["columns"]
    assert isinstance(patterns, tuple)
    exact_matches = [match for match in matches if _compact(match[1]) in patterns]
    selected, route = _nearest_match(exact_matches, anchors, graph)
    if selected is None:
        # An audit date on the fact must not eclipse a commercial date on its
        # declared header. Disconnected exact matches still cannot become evidence.
        selected, route = _nearest_match(matches, anchors, graph)
    if selected is None:
        return (
            "unavailable",
            [],
            "No se encontró una referencia de tipo compatible y una ruta que conserve el hecho.",
        )
    table, column = selected
    evidence = [f"{table}.{column}"]
    if len(route) > 1:
        evidence.append("Ruta declarada: " + " → ".join(route))
    data_type = next(kind for ref, name, _, kind in index if (ref, name) == selected)
    if not data_type and capability in NUMERIC_CAPABILITIES | {"date"}:
        return (
            "ambiguous",
            evidence,
            "La instantánea no registra el tipo de esta columna; actualice los metadatos "
            "antes de confirmar el cálculo.",
        )
    distinct_names = {_compact(name) for ref, name in matches if ref == table}
    loose_semantic_match = _compact(column) not in patterns
    if capability in {"sales_amount", "date", "unit_cost"} and (
        len(distinct_names) > 1 or loose_semantic_match
    ):
        return (
            "ambiguous",
            evidence,
            (
                "El nombre es genérico o existen varias columnas candidatas; "
                "la plataforma debe validar su semántica antes de elegir."
            ),
        )
    return "direct", evidence, "Existe una columna candidata comprobada en los metadatos."


def _combined_requirement(
    code: str,
    label: str,
    request_text: str,
    components: list[str],
    index: list[ColumnEvidence],
    graph: dict[str, set[str]],
    formula: str | None = None,
    preferred_anchors: set[str] | None = None,
) -> dict[str, object]:
    anchors = preferred_anchors or _coherent_anchor(index, graph, components)
    component_results = [_component(component, index, graph, anchors) for component in components]
    derived_component_evidence: list[str] = []
    derived_component_routes: list[list[str]] = []
    derived_component_formulas: list[str] = []
    for position, component in enumerate(components):
        if component != "sales_amount" or component_results[position][0] != "unavailable":
            continue
        price = _component("unit_price", index, graph, anchors)
        quantity = _component("quantity", index, graph, anchors)
        price_match, price_route = _nearest_match(
            _find_columns(index, "unit_price"), anchors, graph
        )
        quantity_match, quantity_route = _nearest_match(
            _find_columns(index, "quantity"), anchors, graph
        )
        if price_match is None or quantity_match is None:
            continue
        price_table, price_column = price_match
        quantity_table, quantity_column = quantity_match
        if price_table != quantity_table and not _path(graph, {price_table}, {quantity_table}):
            continue
        derived_component_evidence.extend(
            [f"{price_table}.{price_column}", f"{quantity_table}.{quantity_column}"]
        )
        derived_component_routes.extend(route for route in (price_route, quantity_route) if route)
        derived_component_formulas.append("precio unitario × cantidad")
        component_results[position] = (
            "derivable" if price[0] == quantity[0] == "direct" else "ambiguous",
            derived_component_evidence,
            "El importe se puede derivar con componentes relacionados y verificables.",
        )
    missing = [
        components[i] for i, item in enumerate(component_results) if item[0] == "unavailable"
    ]
    ambiguous = [
        components[i] for i, item in enumerate(component_results) if item[0] == "ambiguous"
    ]
    evidence = [reference for result in component_results for reference in result[1]]
    evidence.extend(derived_component_evidence)
    evidence = list(dict.fromkeys(evidence))
    if missing:
        status = "unavailable"
        resolution = (
            "No generar este requisito. Registre la limitación o incorpore una fuente "
            "real con tipos compatibles y relaciones hacia claves únicas que aporte: "
            + ", ".join(str(CAPABILITIES[item]["label"]) for item in missing)
            + "."
        )
    elif ambiguous:
        status = "ambiguous"
        resolution = (
            "Revise las alternativas candidatas dentro de la plataforma y confirme la "
            "definición de negocio y los tipos registrados en los metadatos; "
            "ninguna se seleccionará por nombre solamente."
        )
    elif len(components) == 1 and component_results[0][0] == "direct":
        status = "direct"
        resolution = "Puede resolverse directamente con la referencia técnica indicada."
    elif all(item[0] in {"direct", "derivable"} for item in component_results):
        status = "derivable"
        effective_formula = formula or " y ".join(dict.fromkeys(derived_component_formulas))
        resolution = (
            f"Puede calcularse de forma controlada como {effective_formula}."
            if effective_formula
            else (
                "Puede resolverse uniendo únicamente relaciones declaradas y conservando "
                "la granularidad."
            )
        )
        for route in derived_component_routes:
            if len(route) > 1:
                evidence.append("Ruta declarada: " + " → ".join(route))
    else:
        status = "unavailable"
        resolution = (
            "Los componentes existen, pero no hay una ruta de relación declarada que "
            "permita combinarlos sin inventar un join."
        )
    return {
        "code": code,
        "label": label,
        "request_text": request_text,
        "components": components,
        "status": status,
        "evidence": evidence[:8],
        "formula": formula,
        "resolution": resolution,
    }


def assess_business_need(
    document: dict[str, Any], business_request: dict[str, Any]
) -> dict[str, object]:
    """Classify every explicit business requirement against structural metadata only."""
    tables = {
        reference: table
        for reference, table in _tables(document).items()
        if not _non_sales_event(reference)
    }
    index = _column_index(tables)
    graph = _graph(tables)
    goal = _plain(business_request.get("goal", ""))
    periodicity = business_request.get("periodicity", {})
    requires_date = isinstance(periodicity, dict) and periodicity.get("code") in {
        "day",
        "week",
        "month",
        "quarter",
        "year",
    }
    invoice_requested = bool(
        re.search(
            r"\b(factura(?:s)?|facturad[ao]s?|facturacion|invoice(?:s|d)?|invoiced|billing)\b", goal
        )
    )
    if invoice_requested:
        index = _invoice_index(index)
    items: list[dict[str, object]] = []

    question_components = {
        "sales_over_time": ["sales_amount", "date"],
        "top_products": ["sales_amount", "quantity", "product"],
        "customer_performance": ["sales_amount", "customer"],
        "territory_performance": ["sales_amount", "territory"],
    }
    requested_components = [
        capability
        for capability, definition in CAPABILITIES.items()
        if _matches(goal, definition["triggers"])  # type: ignore[arg-type]
    ]
    if requires_date:
        requested_components.append("date")
    for question in business_request.get("questions", []):
        if isinstance(question, dict):
            requested_components.extend(question_components.get(str(question.get("code")), []))
    preferred_anchors = _coherent_anchor(index, graph, requested_components)
    for question in business_request.get("questions", []):
        if not isinstance(question, dict):
            continue
        code = str(question.get("code", "question"))
        text = " ".join(
            str(question.get(key, "")) for key in ("label", "description", "instruction")
        )
        normalized = _plain(text)
        components = question_components.get(code)
        if components is None:
            components = [
                capability
                for capability, definition in CAPABILITIES.items()
                if _matches(normalized, definition["triggers"])  # type: ignore[arg-type]
            ]
        if not components:
            items.append(
                {
                    "code": f"question:{code}",
                    "label": str(question.get("label", "Pregunta de negocio")),
                    "request_text": text,
                    "components": [],
                    "status": "ambiguous",
                    "evidence": [],
                    "formula": None,
                    "resolution": (
                        "La pregunta es válida como orientación, pero debe precisar qué "
                        "indicador y segmentación espera."
                    ),
                }
            )
            continue
        items.append(
            _combined_requirement(
                f"question:{code}",
                str(question.get("label", "Pregunta de negocio")),
                text,
                components,
                index,
                graph,
                preferred_anchors=preferred_anchors,
            )
        )

    detected = {
        capability
        for capability, definition in CAPABILITIES.items()
        if _matches(goal, definition["triggers"])  # type: ignore[arg-type]
    }
    if requires_date:
        detected.add("date")
    derived: list[tuple[str, str, list[str], str]] = []
    if "discount_rate" in detected:
        derived.append(
            (
                "discount_amount",
                "Descuento monetario",
                ["unit_price", "discount_rate", "quantity"],
                "precio unitario × tasa de descuento × cantidad",
            )
        )
        detected.discard("discount_rate")
    if "unit_cost" in detected:
        derived.append(
            (
                "total_cost",
                "Costo total",
                ["unit_cost", "quantity"],
                "costo unitario × unidades vendidas",
            )
        )
    if any(
        term in goal
        for term in (
            "margen",
            "rentabilidad",
            "utilidad",
            "beneficio",
            "margin",
            "profitability",
            "profit",
        )
    ):
        derived.append(
            (
                "gross_margin",
                "Margen bruto y rentabilidad",
                ["sales_amount", "unit_cost", "quantity"],
                "ventas netas − (costo unitario × unidades)",
            )
        )
    if "por unidad" in goal or "unitario" in goal or "unitaria" in goal or "per unit" in goal:
        if "sales_amount" in detected or "venta" in goal:
            derived.append(
                (
                    "sales_per_unit",
                    "Venta por unidad",
                    ["sales_amount", "quantity"],
                    "ventas netas ÷ unidades vendidas",
                )
            )
        if "unit_cost" in detected or "costo" in goal or "coste" in goal:
            derived.append(
                (
                    "cost_per_unit",
                    "Costo por unidad",
                    ["unit_cost"],
                    "costo unitario trazable de la fuente",
                )
            )
    if re.search(
        r"\b(promedio|media|average|avg)\b.*\b(transaccion(?:es)?|pedido(?:s)?|transaction(?:s)?|order(?:s)?|factura(?:s)?|invoice(?:s)?)\b",
        goal,
    ):
        derived.append(
            (
                "average_transaction",
                "Importe promedio por transacción",
                ["sales_amount", "transactions"],
                "ventas totales ÷ documentos comerciales distintos",
            )
        )
    if invoice_requested:
        invoice_index = [
            item
            for item in index
            if (item[0], item[1]) not in _find_columns(index, "transactions")
            or item[2] in {"invoiceid", "facturaid", "idfactura"}
        ]
        invoice_requirement = _combined_requirement(
            "goal:invoiced_sales",
            "Ventas facturadas",
            str(business_request.get("goal", "")),
            ["sales_amount", "transactions", "date"],
            invoice_index,
            graph,
            preferred_anchors=preferred_anchors,
        )
        # Keep the public semantic code used by proposal generation while proving
        # amount, document identity and date together in the invoice subgraph.
        invoice_requirement["components"] = ["invoice_event"]
        invoice_requirement["resolution"] = (
            str(invoice_requirement["resolution"])
            + " Los pedidos por sí solos no prueban una venta facturada."
        )
        items.append(invoice_requirement)
    for capability in sorted(detected):
        definition = CAPABILITIES[capability]
        items.append(
            _combined_requirement(
                f"goal:{capability}",
                str(definition["label"]),
                str(business_request.get("goal", "")),
                [capability],
                index,
                graph,
                preferred_anchors=preferred_anchors,
            )
        )
    for code, label, components, formula in derived:
        items.append(
            _combined_requirement(
                f"goal:{code}",
                label,
                str(business_request.get("goal", "")),
                components,
                index,
                graph,
                formula,
                preferred_anchors,
            )
        )

    if not items:
        items.append(
            {
                "code": "goal:unclassified",
                "label": "Necesidad por precisar",
                "request_text": str(business_request.get("goal", "")),
                "components": [],
                "status": "ambiguous",
                "evidence": [],
                "formula": None,
                "resolution": (
                    "Indique al menos un indicador, una comparación o una segmentación "
                    "de negocio verificable."
                ),
            }
        )

    unique = {str(item["code"]): item for item in items}
    items = list(unique.values())
    counts = {
        status: sum(item["status"] == status for item in items)
        for status in ("direct", "derivable", "ambiguous", "unavailable")
    }
    hash_input = {
        "snapshot": business_request.get("snapshot_hash", ""),
        "goal": business_request.get("goal", ""),
        "questions": business_request.get("questions", []),
        "periodicity": business_request.get("periodicity", {}),
        "requirements": items,
    }
    assessment_hash = hashlib.sha256(
        json.dumps(hash_input, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    blocking = [
        str(item["code"]) for item in items if item["status"] in {"ambiguous", "unavailable"}
    ]
    return {
        "assessment_hash": assessment_hash,
        "requirements": items,
        "counts": counts,
        "requires_acknowledgement": blocking,
        "can_continue": bool(items) and counts["direct"] + counts["derivable"] > 0,
        "summary": (
            "Se identificó respaldo estructural parcial, con decisiones pendientes. "
            if blocking
            else "Los requisitos reconocidos tienen referencias estructurales compatibles. "
        )
        + "Esta comprobación no garantiza cobertura completa del texto, calidad ni "
        "disponibilidad de datos; la propuesta y el ETL deben verificarse después.",
    }
