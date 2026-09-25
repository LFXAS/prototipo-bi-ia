from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import deque
from typing import Any

NeedStatus = str


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


def _column_index(tables: dict[str, dict[str, Any]]) -> list[tuple[str, str, str]]:
    return [
        (reference, str(column.get("name", "")), _compact(column.get("name", "")))
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
            target = (
                f"{relation.get('referenced_schema', '')}.{relation.get('referenced_table', '')}"
            )
            if target in tables:
                graph[source].add(target)
                graph[target].add(source)
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


CAPABILITIES: dict[str, dict[str, object]] = {
    "sales_amount": {
        "label": "Ventas o ingresos",
        "triggers": ("venta", "ventas", "ingreso", "ingresos", "facturacion", "importe"),
        "columns": ("linetotal", "salesamount", "salestotal", "subtotal", "totaldue", "revenue"),
    },
    "quantity": {
        "label": "Unidades vendidas",
        "triggers": ("unidad", "unidades", "cantidad", "cantidades", "volumen"),
        "columns": ("orderqty", "quantity", "qty", "cantidad", "units"),
    },
    "transactions": {
        "label": "Número de transacciones o pedidos",
        "triggers": ("pedido", "pedidos", "transaccion", "transacciones", "ordenes"),
        "columns": ("salesorderid", "orderid", "transactionid", "pedidoid"),
    },
    "date": {
        "label": "Evolución temporal",
        "triggers": ("tiempo", "fecha", "periodo", "mensual", "trimestral", "anual", "tendencia"),
        "columns": ("orderdate", "salesdate", "transactiondate", "fecha", "date"),
    },
    "product": {
        "label": "Análisis por producto",
        "triggers": ("producto", "productos", "articulo", "articulos"),
        "columns": ("productid", "itemid", "productnumber", "productname"),
    },
    "customer": {
        "label": "Análisis por cliente",
        "triggers": ("cliente", "clientes", "comprador", "compradores"),
        "columns": ("customerid", "clientid", "personid", "accountnumber"),
    },
    "territory": {
        "label": "Análisis territorial",
        "triggers": ("territorio", "territorios", "region", "regiones", "pais", "geograf"),
        "columns": ("territoryid", "regionid", "countryregioncode", "territoryname"),
    },
    "unit_cost": {
        "label": "Costo unitario",
        "triggers": ("costo", "costos", "coste", "costes"),
        "columns": ("standardcost", "unitcost", "productcost", "costo"),
    },
    "unit_price": {
        "label": "Precio unitario",
        "triggers": (),
        "columns": ("unitprice", "salesprice", "precio"),
    },
    "discount_rate": {
        "label": "Descuento",
        "triggers": ("descuento", "descuentos"),
        "columns": ("unitpricediscount", "discountrate", "discountpct"),
    },
}


def _matches(text: str, values: tuple[str, ...]) -> bool:
    words = set(text.split())
    return any(value in words or value in text for value in values)


def _find_columns(index: list[tuple[str, str, str]], capability: str) -> list[tuple[str, str]]:
    patterns = CAPABILITIES[capability]["columns"]
    assert isinstance(patterns, tuple)
    for pattern in patterns:
        matches = [
            (reference, column)
            for reference, column, normalized in index
            if str(pattern) in normalized
        ]
        if matches:
            return matches
    return []


def _component(
    capability: str,
    index: list[tuple[str, str, str]],
) -> tuple[NeedStatus, list[str], str]:
    matches = _find_columns(index, capability)
    evidence = [f"{table}.{column}" for table, column in matches[:5]]
    if not matches:
        return (
            "unavailable",
            [],
            "No se encontró una columna compatible en la instantánea vigente.",
        )
    distinct_names = {_compact(column) for _, column in matches}
    if len(distinct_names) > 1 and capability in {"sales_amount", "date", "unit_cost"}:
        return (
            "ambiguous",
            evidence,
            (
                "Existen varias columnas candidatas; la plataforma debe validar su "
                "semántica antes de elegir."
            ),
        )
    return "direct", evidence, "Existe una columna candidata comprobada en los metadatos."


def _combined_requirement(
    code: str,
    label: str,
    request_text: str,
    components: list[str],
    index: list[tuple[str, str, str]],
    graph: dict[str, set[str]],
    formula: str | None = None,
) -> dict[str, object]:
    component_results = [_component(component, index) for component in components]
    missing = [
        components[i] for i, item in enumerate(component_results) if item[0] == "unavailable"
    ]
    ambiguous = [
        components[i] for i, item in enumerate(component_results) if item[0] == "ambiguous"
    ]
    evidence = list(dict.fromkeys(item for result in component_results for item in result[1]))
    source_sets = [
        {table for table, _ in _find_columns(index, component)} for component in components
    ]
    routes: list[list[str]] = []
    if len(source_sets) > 1 and all(source_sets):
        routes = [_path(graph, source_sets[0], destinations) for destinations in source_sets[1:]]
    if missing:
        status = "unavailable"
        resolution = (
            "No generar este requisito. Registre la limitación o incorpore una fuente "
            "real que aporte: "
            + ", ".join(str(CAPABILITIES[item]["label"]) for item in missing)
            + "."
        )
    elif ambiguous:
        status = "ambiguous"
        resolution = (
            "Revise las alternativas candidatas dentro de la plataforma y confirme la "
            "definición de negocio; "
            "ninguna se seleccionará por nombre solamente."
        )
    elif len(components) == 1:
        status = "direct"
        resolution = "Puede resolverse directamente con la referencia técnica indicada."
    elif len(components) > 1 and routes and all(routes):
        status = "derivable"
        resolution = (
            f"Puede calcularse de forma controlada como {formula}."
            if formula
            else (
                "Puede resolverse uniendo únicamente relaciones declaradas y conservando "
                "la granularidad."
            )
        )
        for route in routes:
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
        "status": status,
        "evidence": evidence[:8],
        "formula": formula,
        "resolution": resolution,
    }


def assess_business_need(
    document: dict[str, Any], business_request: dict[str, Any]
) -> dict[str, object]:
    """Classify every explicit business requirement against structural metadata only."""
    tables = _tables(document)
    index = _column_index(tables)
    graph = _graph(tables)
    goal = _plain(business_request.get("goal", ""))
    items: list[dict[str, object]] = []

    question_components = {
        "sales_over_time": ["sales_amount", "date"],
        "top_products": ["sales_amount", "quantity", "product"],
        "customer_performance": ["sales_amount", "customer"],
        "territory_performance": ["sales_amount", "territory"],
    }
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
            )
        )

    detected = {
        capability
        for capability, definition in CAPABILITIES.items()
        if _matches(goal, definition["triggers"])  # type: ignore[arg-type]
    }
    derived: list[tuple[str, str, list[str], str]] = []
    if "descuento" in goal or "descuentos" in goal:
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
    if any(term in goal for term in ("margen", "rentabilidad", "utilidad", "beneficio")):
        derived.append(
            (
                "gross_margin",
                "Margen bruto y rentabilidad",
                ["sales_amount", "unit_cost", "quantity"],
                "ventas netas − (costo unitario × unidades)",
            )
        )
    if "por unidad" in goal or "unitario" in goal or "unitaria" in goal:
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
            )
        )

    if not items:
        items.append(
            {
                "code": "goal:unclassified",
                "label": "Necesidad por precisar",
                "request_text": str(business_request.get("goal", "")),
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
            "La necesidad tiene respaldo suficiente para continuar, con decisiones pendientes."
            if blocking
            else "La necesidad tiene respaldo estructural suficiente para continuar."
        ),
    }
