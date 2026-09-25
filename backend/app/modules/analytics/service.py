from __future__ import annotations

import re
from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.copilot.models import BiProposal
from app.modules.etl.models import EtlExecution
from app.modules.metadata.models import MetadataSnapshot

from .schemas import (
    AnalyticsDashboardRead,
    AnalyticsFiltersRead,
    AnalyticsInsightRead,
    AnalyticsMetricRead,
    AnalyticsOptionRead,
    AnalyticsPointRead,
    AnalyticsQualityRead,
    AnalyticsVisualRead,
)

MART_SCHEMA = "mart_ventas"
_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


class AnalyticsUnavailableError(RuntimeError):
    """Raised when the current materialized mart cannot support a dashboard."""


def _safe_identifier(value: object) -> str:
    normalized = re.sub(r"[^a-z0-9_]+", "_", str(value).strip().lower()).strip("_")
    if not _IDENTIFIER.fullmatch(normalized):
        raise AnalyticsUnavailableError("El contrato contiene un identificador no permitido.")
    return normalized


def _quoted(value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise AnalyticsUnavailableError("El contrato contiene un identificador no permitido.")
    return f'"{value}"'


def _number(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal | int | float):
        return float(value)
    return float(str(value))


def _dict_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _dimension_document(proposal: BiProposal, aliases: Iterable[str]) -> dict[str, Any] | None:
    normalized_aliases = tuple(item.casefold() for item in aliases)
    for item in _dict_items(proposal.proposal_document.get("dimensions")):
        name = str(item.get("name", ""))
        if any(alias in name.casefold() for alias in normalized_aliases):
            return item
    return None


async def _table_columns(session: AsyncSession, table_name: str) -> set[str]:
    rows = (
        await session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = :schema AND table_name = :table"
            ),
            {"schema": MART_SCHEMA, "table": table_name},
        )
    ).scalars()
    return {str(item) for item in rows}


def _preferred_column(
    columns: set[str], candidates: Iterable[object], *, fallback: str | None = None
) -> str | None:
    for raw in candidates:
        try:
            candidate = _safe_identifier(raw)
        except AnalyticsUnavailableError:
            continue
        if candidate in columns:
            return candidate
    return fallback if fallback in columns else None


def _aggregate_expression(operation: str, measure: str) -> str:
    column = f"f.{_quoted(measure)}"
    expressions = {
        "sum": f"COALESCE(SUM({column}), 0)",
        "average": f"COALESCE(AVG({column}), 0)",
        "count": f"COUNT({column})",
        "count_distinct": f"COUNT(DISTINCT {column})",
        "min": f"COALESCE(MIN({column}), 0)",
        "max": f"COALESCE(MAX({column}), 0)",
    }
    expression = expressions.get(operation)
    if expression is None:
        raise AnalyticsUnavailableError(
            "El indicador seleccionado no admite todavía una visualización agrupada segura."
        )
    return expression


def _recipe_parts(recipe: dict[str, Any]) -> tuple[str, str] | None:
    if recipe.get("kind") != "aggregate":
        return None
    detail = recipe.get("recipe")
    if not isinstance(detail, dict):
        return None
    operation = str(detail.get("operation", ""))
    try:
        measure = _safe_identifier(detail.get("measure", ""))
    except AnalyticsUnavailableError:
        return None
    if operation not in {"sum", "average", "count", "count_distinct", "min", "max"}:
        return None
    return operation, measure


def _unit_for_recipe(execution: EtlExecution, recipe: dict[str, Any]) -> str:
    code = str(recipe.get("code", ""))
    for item in _dict_items(execution.metrics_document.get("kpis")):
        if str(item.get("code")) == code:
            return str(item.get("unit", recipe.get("unit", "valor")))
    return str(recipe.get("unit", "valor"))


def _display_unit_for_recipe(execution: EtlExecution, recipe: dict[str, Any]) -> str:
    unit = _unit_for_recipe(execution, recipe)
    if unit.casefold() not in {"count", "conteo"}:
        return unit
    semantic_text = f"{recipe.get('code', '')} {recipe.get('name', '')}".casefold()
    if "pedido" in semantic_text or "order" in semantic_text or "transaction" in semantic_text:
        return "pedidos"
    if "cliente" in semantic_text or "customer" in semantic_text:
        return "clientes"
    return "registros"


def _insights(visuals: list[AnalyticsVisualRead], unit: str) -> list[AnalyticsInsightRead]:
    insights: list[AnalyticsInsightRead] = []
    timeline = next((item for item in visuals if item.code == "trend"), None)
    if timeline and timeline.points:
        peak = max(timeline.points, key=lambda item: item.value)
        first = timeline.points[0]
        last = timeline.points[-1]
        if first.value:
            change = ((last.value - first.value) / abs(first.value)) * 100
            tone = "positive" if change >= 0 else "attention"
            insights.append(
                AnalyticsInsightRead(
                    code="period_change",
                    title="Variación entre extremos visibles",
                    statement=(
                        f"El valor observado en {last.label} fue "
                        f"{abs(change):.1f}% {'mayor' if change >= 0 else 'menor'} "
                        f"que en {first.label}."
                    ),
                    evidence=(
                        f"Comparación directa de {first.value:,.2f} y {last.value:,.2f} "
                        f"{unit}; no prueba una tendencia ni causalidad y los meses extremos "
                        "pueden tener cobertura parcial."
                    ),
                    tone=tone,
                )
            )
        insights.append(
            AnalyticsInsightRead(
                code="peak_period",
                title="Período de mayor valor",
                statement=f"{peak.label} concentra el valor mensual más alto de la selección.",
                evidence=f"Valor conciliado: {peak.value:,.2f} {unit}.",
                tone="positive",
            )
        )
    for visual_code, insight_code, title in (
        ("products", "leading_product", "Producto con mayor contribución"),
        ("territories", "leading_territory", "Territorio con mayor contribución"),
        ("customers", "leading_customer", "Cliente con mayor contribución"),
    ):
        visual = next((item for item in visuals if item.code == visual_code), None)
        if visual and visual.points:
            leader = visual.points[0]
            share = f" ({leader.share:.1f}% del total mostrado)" if leader.share is not None else ""
            insights.append(
                AnalyticsInsightRead(
                    code=insight_code,
                    title=title,
                    statement=f"{leader.label} ocupa la primera posición{share}.",
                    evidence=(
                        f"Resultado agrupado y calculado desde el datamart reconciliado: "
                        f"{leader.value:,.2f} {unit}."
                    ),
                )
            )
    return insights[:4]


async def build_dashboard(
    session: AsyncSession,
    execution: EtlExecution,
    proposal: BiProposal,
    snapshot: MetadataSnapshot,
    *,
    metric_code: str | None,
    year: int | None,
    territory: str | None,
) -> AnalyticsDashboardRead:
    del snapshot  # Reserved for connector-neutral semantic expansion.
    fact_document = proposal.proposal_document.get("fact")
    if not isinstance(fact_document, dict):
        raise AnalyticsUnavailableError("La propuesta no conserva un hecho analítico válido.")
    fact_name = _safe_identifier(fact_document.get("name", ""))
    fact_columns = await _table_columns(session, fact_name)
    if not fact_columns:
        raise AnalyticsUnavailableError(
            "El datamart materializado no está disponible. Abra el expediente ETL y "
            "valide la carga."
        )
    row_count = await session.scalar(
        text(
            f"SELECT COUNT(*) FROM {_quoted(MART_SCHEMA)}.{_quoted(fact_name)} "
            "WHERE etl_execution_id = :execution_id"
        ),
        {"execution_id": execution.id},
    )
    if not row_count:
        raise AnalyticsUnavailableError(
            "Esta ejecución ya no corresponde a las tablas publicadas. Use la ejecución vigente."
        )

    recipes = _dict_items(execution.plan_document.get("kpi_recipes"))
    chartable = [item for item in recipes if _recipe_parts(item) is not None]
    if not chartable:
        raise AnalyticsUnavailableError("La ejecución no contiene indicadores agrupables.")
    selected_recipe = next(
        (item for item in chartable if str(item.get("code")) == metric_code), chartable[0]
    )
    selected_parts = _recipe_parts(selected_recipe)
    if selected_parts is None:
        raise AnalyticsUnavailableError("El indicador seleccionado no tiene una receta segura.")
    operation, measure = selected_parts
    if measure not in fact_columns:
        raise AnalyticsUnavailableError("La medida seleccionada no existe en el datamart vigente.")
    expression = _aggregate_expression(operation, measure)

    date_dimension = _dimension_document(proposal, ("fecha", "date", "time"))
    product_dimension = _dimension_document(proposal, ("producto", "product"))
    customer_dimension = _dimension_document(proposal, ("cliente", "customer", "client"))
    territory_dimension = _dimension_document(proposal, ("territorio", "territory", "region"))
    if date_dimension is None:
        raise AnalyticsUnavailableError(
            "La propuesta no contiene una dimensión temporal para construir el análisis."
        )

    date_table = _safe_identifier(date_dimension.get("name", ""))
    date_columns = await _table_columns(session, date_table)
    date_column = _preferred_column(
        date_columns,
        [date_dimension.get("business_key", ""), "fecha", "orderdate", "date"],
    )
    if date_column is None:
        raise AnalyticsUnavailableError("No se encontró una fecha validada para el análisis.")

    joins = [
        f"JOIN {_quoted(MART_SCHEMA)}.{_quoted(date_table)} d "
        f"ON f.{_quoted(date_table + '_sk')} = d.surrogate_key "
        "AND d.etl_execution_id = :execution_id"
    ]
    where = ["f.etl_execution_id = :execution_id"]
    params: dict[str, object] = {"execution_id": execution.id}
    if year is not None:
        where.append(f"EXTRACT(YEAR FROM d.{_quoted(date_column)}) = :year")
        params["year"] = year

    territory_label: str | None = None
    territory_table: str | None = None
    territory_columns: set[str] = set()
    if territory_dimension is not None:
        territory_table = _safe_identifier(territory_dimension.get("name", ""))
        territory_columns = await _table_columns(session, territory_table)
        territory_label = _preferred_column(
            territory_columns,
            [
                "group_es",
                "name_es",
                "nombre",
                "name",
                "group",
                "countryregioncode",
                territory_dimension.get("business_key", ""),
            ],
        )
        if territory_label:
            joins.append(
                f"JOIN {_quoted(MART_SCHEMA)}.{_quoted(territory_table)} t "
                f"ON f.{_quoted(territory_table + '_sk')} = t.surrogate_key "
                "AND t.etl_execution_id = :execution_id"
            )
            if territory:
                where.append(f"t.{_quoted(territory_label)} = :territory")
                params["territory"] = territory

    from_sql = (
        f"FROM {_quoted(MART_SCHEMA)}.{_quoted(fact_name)} f "
        + " ".join(joins)
        + " WHERE "
        + " AND ".join(where)
    )

    years = [
        AnalyticsOptionRead(value=str(item), label=str(item))
        for item in (
            await session.execute(
                text(
                    f"SELECT DISTINCT EXTRACT(YEAR FROM d.{_quoted(date_column)})::int AS value "
                    f"FROM {_quoted(MART_SCHEMA)}.{_quoted(fact_name)} f "
                    f"JOIN {_quoted(MART_SCHEMA)}.{_quoted(date_table)} d "
                    f"ON f.{_quoted(date_table + '_sk')} = d.surrogate_key "
                    "WHERE f.etl_execution_id = :execution_id "
                    "AND d.etl_execution_id = :execution_id ORDER BY value"
                ),
                {"execution_id": execution.id},
            )
        ).scalars()
    ]
    territories: list[AnalyticsOptionRead] = []
    if territory_table and territory_label:
        territory_values = (
            await session.execute(
                text(
                    f"SELECT DISTINCT t.{_quoted(territory_label)} "
                    f"FROM {_quoted(MART_SCHEMA)}.{_quoted(fact_name)} f "
                    f"JOIN {_quoted(MART_SCHEMA)}.{_quoted(territory_table)} t "
                    f"ON f.{_quoted(territory_table + '_sk')} = t.surrogate_key "
                    "WHERE f.etl_execution_id = :execution_id "
                    "AND t.etl_execution_id = :execution_id "
                    f"AND t.{_quoted(territory_label)} IS NOT NULL ORDER BY 1"
                ),
                {"execution_id": execution.id},
            )
        ).scalars()
        territories = [
            AnalyticsOptionRead(value=str(item), label=str(item)) for item in territory_values
        ]

    kpis: list[AnalyticsMetricRead] = []
    resolved_values: dict[str, float] = {}
    for recipe in recipes:
        parts = _recipe_parts(recipe)
        value: float | None = None
        if parts is not None and parts[1] in fact_columns:
            result = await session.scalar(
                text(f"SELECT {_aggregate_expression(parts[0], parts[1])} {from_sql}"), params
            )
            value = _number(result)
        elif recipe.get("kind") in {"ratio", "share"}:
            detail = recipe.get("recipe")
            if isinstance(detail, dict):
                numerator = resolved_values.get(str(detail.get("numerator")))
                denominator = resolved_values.get(str(detail.get("denominator")))
                if numerator is not None and denominator:
                    value = numerator / denominator
                    if recipe.get("kind") == "share":
                        value *= float(detail.get("multiply_by", 100))
        code = str(recipe.get("code", ""))
        if value is not None:
            resolved_values[code] = value
        kpis.append(
            AnalyticsMetricRead(
                code=code,
                name=str(recipe.get("name", code)),
                value=value,
                unit=_display_unit_for_recipe(execution, recipe),
                status="reconciled" if value is not None else "not_calculable",
            )
        )

    timeline_rows = (
        await session.execute(
            text(
                f"SELECT EXTRACT(YEAR FROM d.{_quoted(date_column)})::int AS year, "
                f"EXTRACT(MONTH FROM d.{_quoted(date_column)})::int AS month, "
                f"{expression} AS value "
                f"{from_sql} GROUP BY 1, 2 ORDER BY 1, 2"
            ),
            params,
        )
    ).all()
    month_names = (
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic",
    )
    timeline = [
        AnalyticsPointRead(
            key=f"{row.year:04d}-{row.month:02d}",
            label=f"{month_names[row.month - 1]} {row.year}",
            value=_number(row.value),
        )
        for row in timeline_rows
    ]
    metric_name = str(selected_recipe.get("name", selected_recipe.get("code", "Indicador")))
    metric_unit = _display_unit_for_recipe(execution, selected_recipe)
    visuals = [
        AnalyticsVisualRead(
            code="trend",
            title="Evolución en el tiempo",
            subtitle=f"{metric_name} por mes",
            kind="line",
            dimension="Fecha",
            points=timeline,
        )
    ]

    async def add_ranking(
        dimension: dict[str, Any] | None,
        *,
        code: str,
        title: str,
        aliases: list[object],
        table_alias: str,
        limit: int,
    ) -> None:
        if dimension is None:
            return
        table_name = _safe_identifier(dimension.get("name", ""))
        columns = await _table_columns(session, table_name)
        raw_attributes = dimension.get("attributes", [])
        attributes = raw_attributes if isinstance(raw_attributes, list) else []
        label_column = _preferred_column(
            columns,
            [*aliases, *attributes, dimension.get("business_key", "")],
        )
        if label_column is None:
            return
        local_joins = [*joins]
        if not any(f" {table_alias} " in item for item in local_joins):
            local_joins.append(
                f"JOIN {_quoted(MART_SCHEMA)}.{_quoted(table_name)} {table_alias} "
                f"ON f.{_quoted(table_name + '_sk')} = {table_alias}.surrogate_key "
                f"AND {table_alias}.etl_execution_id = :execution_id"
            )
        local_from = (
            f"FROM {_quoted(MART_SCHEMA)}.{_quoted(fact_name)} f "
            + " ".join(local_joins)
            + " WHERE "
            + " AND ".join(where)
        )
        rows = (
            await session.execute(
                text(
                    "SELECT COALESCE(NULLIF(TRIM("
                    f"{table_alias}.{_quoted(label_column)}::text), ''), "
                    f"'Sin etiqueta') AS label, {expression} AS value {local_from} "
                    "GROUP BY 1 ORDER BY value DESC NULLS LAST LIMIT :ranking_limit"
                ),
                {**params, "ranking_limit": limit},
            )
        ).all()
        total = sum(_number(row.value) for row in rows)
        points = [
            AnalyticsPointRead(
                key=str(index + 1),
                label=str(row.label),
                value=_number(row.value),
                share=(_number(row.value) / total * 100) if total else None,
            )
            for index, row in enumerate(rows)
        ]
        visuals.append(
            AnalyticsVisualRead(
                code=code,
                title=title,
                subtitle=f"{metric_name}; principales {len(points)} categorías",
                kind="donut" if code == "territories" and len(points) <= 8 else "bar",
                dimension=title,
                points=points,
            )
        )

    await add_ranking(
        product_dimension,
        code="products",
        title="Productos líderes",
        aliases=["name_es", "nombre", "name", "productnumber"],
        table_alias="p",
        limit=8,
    )
    await add_ranking(
        territory_dimension,
        code="territories",
        title="Distribución territorial",
        aliases=["group_es", "name_es", "nombre", "name", "group", "countryregioncode"],
        table_alias="t",
        limit=8,
    )
    await add_ranking(
        customer_dimension,
        code="customers",
        title="Clientes principales",
        aliases=["nombre_cliente", "name_es", "nombre", "name"],
        table_alias="c",
        limit=8,
    )

    reconciliation = execution.metrics_document.get("reconciliation", {})
    reconciliation = reconciliation if isinstance(reconciliation, dict) else {}
    tables = _dict_items(execution.metrics_document.get("tables"))
    currency = execution.metrics_document.get("currency_context", {})
    currency = currency if isinstance(currency, dict) else {}
    overview = execution.plan_document.get("overview", {})
    overview = overview if isinstance(overview, dict) else {}
    period_label = "Todos los períodos"
    if year is not None:
        period_label = str(year)
    if territory:
        period_label += f" · {territory}"
    return AnalyticsDashboardRead(
        execution_id=execution.id,
        proposal_id=proposal.id,
        title="Panel ejecutivo de ventas",
        description=str(overview.get("summary", "Análisis del datamart reconciliado.")),
        grain=str(overview.get("grain", "Granularidad aprobada")),
        refreshed_at=execution.finished_at or execution.created_at,
        currency_code=str(currency.get("currency_code", "moneda de origen")),
        currency_status=str(currency.get("status", "unverified")),
        reconciliation_passed=bool(reconciliation.get("passed")),
        period_label=period_label,
        metric_code=str(selected_recipe.get("code", "")),
        available_metrics=[
            AnalyticsOptionRead(value=str(item.get("code", "")), label=str(item.get("name", "")))
            for item in chartable
        ],
        filters=AnalyticsFiltersRead(
            years=years,
            territories=territories,
            selected_year=year,
            selected_territory=territory,
        ),
        kpis=kpis,
        visuals=visuals,
        insights=_insights(visuals, metric_unit),
        quality=AnalyticsQualityRead(
            source_rows=int(reconciliation.get("source_rows", 0)),
            datamart_rows=int(reconciliation.get("datamart_rows", 0)),
            difference_rows=int(reconciliation.get("difference_rows", 0)),
            reconciliation_passed=bool(reconciliation.get("passed")),
            tables_loaded=len(tables),
        ),
        guidance=[
            "Todos los valores proceden de la ejecución ETL conciliada indicada en el encabezado.",
            "Los filtros vuelven a calcular KPI y visualizaciones; no modifican el datamart.",
            "Los hallazgos describen asociaciones numéricas y no atribuyen causas no demostradas.",
        ],
    )
