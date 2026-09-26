from __future__ import annotations

import re
from typing import Any

from app.modules.copilot.service import canonical_hash, metadata_tables

BUILDER_VERSION = "sales-etl-v1"
SUPPORTED_AGGREGATIONS = {"sum", "count", "count_distinct", "average", "min", "max"}
SUPPORTED_RECIPE_KINDS = {"aggregate", "difference", "ratio", "share"}


def assess_dimensional_readiness(
    proposal: dict[str, Any], schema_document: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """Apply execution-grade BI checks that are stricter than structural approval.

    Sprint 3 proves that references exist. Materialization additionally requires useful
    dimension attributes, unambiguous keys and a grain that can be reconciled.
    """
    blockers: list[str] = []
    warnings: list[str] = []
    tables = metadata_tables(schema_document)
    dimensions = [item for item in proposal.get("dimensions", []) if isinstance(item, dict)]
    dimension_names = {str(item.get("name", "")) for item in dimensions}
    kpi_codes = {
        str(item.get("code", "")) for item in proposal.get("kpis", []) if isinstance(item, dict)
    }
    required_dimensions = {
        "sales_over_time": "dim_fecha",
        "top_products": "dim_producto",
        "customer_performance": "dim_cliente",
        "territory_performance": "dim_territorio",
    }
    for code, dimension_name in required_dimensions.items():
        if code in kpi_codes and dimension_name not in dimension_names:
            blockers.append(
                f"El indicador {code} requiere {dimension_name}; genere una versión que "
                "incluya esa perspectiva con atributos comprobados."
            )

    for dimension in dimensions:
        name = str(dimension.get("name", "dimensión"))
        sources = [str(item) for item in dimension.get("source_tables", [])]
        if len(sources) != 1:
            blockers.append(
                f"{name} debe tener una fuente principal inequívoca antes de materializarse."
            )
            continue
        source = sources[0]
        table = tables.get(source)
        if table is None:
            continue
        columns = {
            str(item.get("name", "")): item
            for item in table.get("columns", [])
            if isinstance(item, dict)
        }
        primary_keys = {
            column_name
            for column_name, column in columns.items()
            if bool(column.get("primary_key", False))
        }
        business_key = str(dimension.get("business_key", ""))
        if name != "dim_fecha" and business_key not in primary_keys:
            blockers.append(
                f"{name} usa {business_key or 'una clave vacía'} como clave de negocio, pero "
                f"no es clave primaria de {source}. Corrija la fuente o la clave."
            )
        if name != "dim_fecha" and len(primary_keys) > 1:
            blockers.append(
                f"{name} se apoya en {source}, una asociación con clave compuesta; seleccione "
                "la entidad descriptiva del negocio y no una tabla puente."
            )
        attributes = [str(item) for item in dimension.get("attributes", [])]
        descriptive = [
            attribute
            for attribute in attributes
            if attribute in columns
            and str(columns[attribute].get("data_type", "")).casefold()
            in {"char", "varchar", "nchar", "nvarchar", "text", "ntext"}
            and not re.match(
                r"^(rowguid|modifieddate|[a-z_]*id|[a-z_]*key)$", attribute, re.IGNORECASE
            )
        ]
        if name != "dim_fecha" and not descriptive:
            blockers.append(
                f"{name} no contiene un atributo descriptivo legible. Incorpore nombre, "
                "descripción, categoría o código de negocio antes de cargarla."
            )
        if name != "dim_fecha" and not isinstance(dimension.get("display_label"), dict):
            blockers.append(
                f"{name} no declara cómo resolver un nombre descriptivo mediante relaciones "
                "verificadas. Genere una propuesta nueva antes de ejecutar el ETL."
            )

    grain = str(proposal.get("grain", {}).get("description", "")).casefold()
    business_keys = {
        str(item).casefold() for item in proposal.get("fact", {}).get("business_keys", [])
    }
    if re.search(r"\b(mes|mensual|month)\b", grain) and any(
        "detail" in key or "detalle" in key for key in business_keys
    ):
        blockers.append(
            "La granularidad declara un resumen mensual, pero conserva claves de detalle. "
            "Defina una fila por detalle o una agregación mensual, no ambas."
        )
    if "dim_fecha" not in dimension_names:
        warnings.append(
            "La propuesta no incluye dimensión fecha; no podrá comparar períodos ni "
            "explicar tendencias temporales."
        )
    for measure in proposal.get("fact", {}).get("measures", []):
        if not isinstance(measure, dict):
            continue
        name = str(measure.get("name", "medida"))
        role = str(measure.get("semantic_role", ""))
        measure_columns = [str(item) for item in measure.get("source_columns", [])]
        calculation = measure.get("calculation")
        source_text = " ".join(measure_columns)
        discount_like = bool(re.search(r"discount|descuento", source_text, re.IGNORECASE))
        amount_like = bool(
            re.search(r"amount|importe|monto|total|value|valor", source_text, re.IGNORECASE)
        )
        if (
            role in {"sales_amount", "discount_amount"}
            and discount_like
            and not amount_like
            and not isinstance(calculation, dict)
        ):
            blockers.append(
                f"{name} usa {source_text} como importe, pero la columna parece una tasa. "
                "Cree una versión corregida con una receta controlada de precio, tasa y "
                "cantidad; no ejecute nuevamente esta versión."
            )
        if (
            role in {"sales_amount", "discount_amount"}
            and discount_like
            and isinstance(calculation, dict)
        ):
            operation = str(calculation.get("operation", ""))
            inputs = [str(item) for item in calculation.get("inputs", [])]
            non_discount = [
                item for item in inputs if not re.search(r"discount|descuento", item, re.IGNORECASE)
            ]
            has_price = any(
                re.search(r"price|precio", item, re.IGNORECASE) for item in non_discount
            )
            has_quantity = any(
                re.search(r"qty|quantity|cantidad|units|unidades", item, re.IGNORECASE)
                for item in non_discount
            )
            has_amount_base = any(
                re.search(
                    r"amount|importe|monto|value|valor|gross|bruto|subtotal",
                    item,
                    re.IGNORECASE,
                )
                for item in non_discount
            )
            if operation != "multiply" or not ((has_price and has_quantity) or has_amount_base):
                blockers.append(
                    f"{name} incluye una tasa de descuento, pero su receta monetaria está "
                    "incompleta. Genere una versión corregida con precio por tasa por cantidad "
                    "o con un importe base inequívoco por tasa."
                )
    return list(dict.fromkeys(blockers)), list(dict.fromkeys(warnings))


def compile_kpi_recipes(proposal: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    measures = {
        str(item.get("name")): item
        for item in proposal.get("fact", {}).get("measures", [])
        if isinstance(item, dict) and item.get("name")
    }
    recipes: list[dict[str, Any]] = []
    issues: list[str] = []
    for raw in proposal.get("kpis", []):
        if not isinstance(raw, dict):
            issues.append("Existe un KPI sin estructura reconocible.")
            continue
        code = str(raw.get("code", "")).strip()
        name = str(raw.get("name", code or "KPI sin nombre")).strip()
        kind = str(raw.get("formula_kind", "aggregate"))
        formula = raw.get("formula", {}) if isinstance(raw.get("formula"), dict) else {}
        if not code:
            issues.append(f"El KPI {name} no conserva un código trazable.")
            continue
        if kind not in SUPPORTED_RECIPE_KINDS:
            issues.append(f"El KPI {name} solicita la receta no soportada {kind}.")
            continue
        if kind == "aggregate":
            measure_name = str(formula.get("measure", raw.get("measure", "")))
            operation = str(formula.get("operation", raw.get("operation", "")))
            if measure_name not in measures:
                issues.append(f"El KPI {name} no referencia una medida comprobada.")
                continue
            if operation not in SUPPORTED_AGGREGATIONS:
                issues.append(f"El KPI {name} usa una agregación no permitida.")
                continue
            declared_unit = str(raw.get("unit", "valor"))
            measure_text = " ".join(
                [
                    measure_name,
                    *(str(item) for item in measures[measure_name].get("source_columns", [])),
                ]
            ).casefold()
            semantic_role = str(measures[measure_name].get("semantic_role", ""))
            if not semantic_role and re.search(
                r"amount|total|importe|monto|ventas|sales|linetotal", measure_text
            ):
                semantic_role = "sales_amount"
            normalized_unit = declared_unit
            adjustments: list[str] = []
            effective_name = name
            calculation = measures[measure_name].get("calculation")
            calculation_inputs = (
                [str(item) for item in calculation.get("inputs", [])]
                if isinstance(calculation, dict) and isinstance(calculation.get("inputs"), list)
                else []
            )
            name_tokens = set(re.findall(r"[a-záéíóúñ]+", name.casefold()))
            calculation_tokens = set(
                re.findall(r"[a-záéíóúñ]+", " ".join(calculation_inputs).casefold())
            )
            if (
                semantic_role == "sales_amount"
                and name_tokens & {"net", "neto", "neta", "netas", "netos"}
                and isinstance(calculation, dict)
                and calculation.get("operation") == "multiply"
                and not calculation_tokens & {"discount", "descuento"}
            ):
                effective_name = re.sub(r"\bnetas\b", "brutas", name, flags=re.IGNORECASE)
                effective_name = re.sub(r"\bneta\b", "bruta", effective_name, flags=re.IGNORECASE)
                effective_name = re.sub(r"\bnetos\b", "brutos", effective_name, flags=re.IGNORECASE)
                effective_name = re.sub(r"\bneto\b", "bruto", effective_name, flags=re.IGNORECASE)
                effective_name = re.sub(r"\bnet\b", "gross", effective_name, flags=re.IGNORECASE)
                adjustments.append(
                    "La receta comprobada calcula precio por cantidad sin descontar una "
                    "tasa; por ello se presenta como venta bruta y no como venta neta."
                )
            if semantic_role in {
                "sales_amount",
                "cost_amount",
                "discount_amount",
            } and declared_unit.casefold() not in {
                "moneda",
                "moneda de origen",
                "currency",
                "importe",
                "valor",
            }:
                normalized_unit = "moneda de origen"
                adjustments.append(
                    f"La unidad {declared_unit} no está comprobada en los metadatos; "
                    "se mostrará como moneda de origen hasta conciliar la divisa."
                )
            recipes.append(
                {
                    "code": code,
                    "name": effective_name,
                    "description": str(raw.get("description_es", raw.get("description", ""))),
                    "kind": "aggregate",
                    "unit": normalized_unit,
                    "declared_unit": declared_unit,
                    "adjustments": adjustments,
                    "periodicity": str(raw.get("periodicity", "inherit")),
                    "definition_version": "sales-kpi-v1",
                    "inputs": [measure_name],
                    "recipe": {
                        "template": "aggregate",
                        "measure": measure_name,
                        "operation": operation,
                    },
                }
            )
            continue
        inputs = raw.get("inputs", [])
        if not isinstance(inputs, list) or len(inputs) != 2:
            issues.append(f"El KPI {name} requiere exactamente dos entradas verificables.")
            continue
        normalized_inputs = [str(item) for item in inputs]
        if not all(
            item in measures or any(recipe["code"] == item for recipe in recipes)
            for item in normalized_inputs
        ):
            issues.append(f"El KPI {name} depende de medidas o indicadores no disponibles.")
            continue
        recipe: dict[str, Any] = {
            "template": kind,
            "numerator": normalized_inputs[0],
            "denominator": normalized_inputs[1],
            "zero_denominator": "null",
        }
        if kind == "difference":
            recipe = {
                "template": kind,
                "minuend": normalized_inputs[0],
                "subtrahend": normalized_inputs[1],
            }
        if kind == "share":
            recipe["multiply_by"] = 100
        recipes.append(
            {
                "code": code,
                "name": name,
                "description": str(raw.get("description_es", raw.get("description", ""))),
                "kind": kind,
                "unit": str(raw.get("unit", "porcentaje" if kind == "share" else "razón")),
                "periodicity": str(raw.get("periodicity", "inherit")),
                "definition_version": "sales-kpi-v1",
                "inputs": normalized_inputs,
                "recipe": recipe,
            }
        )
    if not recipes:
        issues.append("La propuesta no contiene ningún KPI calculable con recetas aprobadas.")
    return recipes, list(dict.fromkeys(issues))


def compile_transformation_plan(proposal: dict[str, Any]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    order = 1

    def add(code: str, stage: str, label: str, detail: str, severity: str = "required") -> None:
        nonlocal order
        plan.append(
            {
                "order": order,
                "code": code,
                "stage": stage,
                "label": label,
                "detail": detail,
                "severity": severity,
                "definition_version": "sales-transform-v1",
            }
        )
        order += 1

    add(
        "extract.approved_columns",
        "extract",
        "Extraer sólo columnas aprobadas",
        (
            "Lee únicamente referencias incluidas en el contrato y mantiene SQL Server "
            "en modo de sólo lectura."
        ),
    )
    add(
        "quality.required_keys",
        "clean",
        "Rechazar claves obligatorias vacías",
        "Las claves de negocio del hecho y de las dimensiones no se reemplazan silenciosamente.",
    )
    for dimension in proposal.get("dimensions", []):
        if not isinstance(dimension, dict):
            continue
        name = str(dimension.get("name", "dimensión"))
        add(
            f"clean.{name}.trim",
            "clean",
            f"Normalizar atributos de {name}",
            "Elimina espacios laterales y conserva los valores desconocidos como nulos trazables.",
        )
        add(
            f"localize.{name}.labels",
            "transform",
            f"Preparar etiquetas españolas de {name}",
            (
                "Detecta categorías descriptivas no sensibles: conserva el valor original y "
                "sólo agrega una etiqueta española cuando el idioma lo requiere y el analista "
                "aprueba el mapeo."
            ),
            "optional",
        )
        add(
            f"clean.{name}.deduplicate",
            "clean",
            f"Deduplicar {name} por clave de negocio",
            "Garantiza una fila por clave natural antes de asignar la clave sustituta.",
        )
        add(
            f"derive.{name}.surrogate_key",
            "transform",
            f"Generar clave sustituta de {name}",
            "Conserva también la clave de negocio para linaje y conciliación.",
        )
        if name == "dim_fecha":
            add(
                "derive.dim_fecha.parts",
                "transform",
                "Derivar atributos calendario",
                "Calcula fecha, año, trimestre, mes y día desde una fecha temporal validada.",
            )
    for measure in proposal.get("fact", {}).get("measures", []):
        if not isinstance(measure, dict):
            continue
        name = str(measure.get("name", "medida"))
        role = str(measure.get("semantic_role", "measure"))
        columns = ", ".join(str(item) for item in measure.get("source_columns", []))
        calculation = (
            measure.get("calculation") if isinstance(measure.get("calculation"), dict) else None
        )
        operation_labels = {
            "multiply": "multiplicación",
            "add": "suma por fila",
            "subtract": "resta por fila",
            "divide": "división protegida por fila",
        }
        operation_label = operation_labels.get(
            str(calculation.get("operation")) if calculation is not None else "",
            "una receta controlada",
        )
        detail = (
            f"Calcula {columns} mediante {operation_label} "
            "con columnas verificadas y sin SQL libre; luego conserva su función "
            f"{role}."
            if calculation is not None
            else (
                f"Convierte {columns or 'la columna aprobada'} al tipo analítico y "
                f"conserva su función {role}."
            )
        )
        add(
            f"transform.measure.{name}",
            "transform",
            f"{'Calcular' if calculation is not None else 'Preparar'} medida {name}",
            detail,
        )
    add(
        "quality.fact_grain",
        "clean",
        "Comprobar unicidad al grano aprobado",
        str(proposal.get("grain", {}).get("description", "Valida la granularidad del hecho.")),
    )
    add(
        "load.dimensions",
        "load",
        "Cargar dimensiones primero",
        "Carga dimensiones validadas antes del hecho para preservar integridad referencial.",
    )
    add(
        "load.fact",
        "load",
        "Cargar el hecho de ventas",
        "Materializa las claves y medidas sólo después de superar los controles bloqueantes.",
    )
    add(
        "validate.reconcile",
        "validate",
        "Conciliar OLTP y datamart",
        "Contrasta filas, pedidos, unidades, importes y KPI con período y filtros equivalentes.",
    )
    return plan


def proposal_overview(proposal: dict[str, Any]) -> dict[str, object]:
    return {
        "summary": str(proposal.get("summary", "Propuesta de ventas")),
        "grain": str(proposal.get("grain", {}).get("description", "Sin granularidad")),
        "fact_name": str(proposal.get("fact", {}).get("name", "")),
        "dimensions": [
            str(item.get("name"))
            for item in proposal.get("dimensions", [])
            if isinstance(item, dict) and item.get("name")
        ],
        "measures": [
            str(item.get("name"))
            for item in proposal.get("fact", {}).get("measures", [])
            if isinstance(item, dict) and item.get("name")
        ],
        "warnings": [str(item) for item in proposal.get("warnings", [])],
        "proposal_hash": canonical_hash(proposal),
    }
