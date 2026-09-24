from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import psycopg
import pyodbc  # type: ignore[import-not-found]

from app.core.config import settings
from app.modules.copilot.service import metadata_tables
from app.modules.parameters.connections import build_connection_string
from app.modules.parameters.models import DataConnection

DESTINATION_SCHEMA = "mart_ventas"
_GENERIC_MONEY_UNITS = {"currency", "importe", "moneda", "moneda de origen", "valor"}
_CURRENCY_SOURCE_COLUMNS = (
    "basecurrencycode",
    "fromcurrencycode",
    "sourcecurrencycode",
    "currencycode",
)


@dataclass(frozen=True)
class SourceColumn:
    source_name: str
    target_name: str
    data_type: str
    aggregation: str = "raw"
    calculation_operation: str | None = None
    calculation_inputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class DimensionPlan:
    name: str
    source_ref: str
    business_key: SourceColumn
    attributes: list[SourceColumn]
    query: str


@dataclass(frozen=True)
class FactPlan:
    name: str
    query: str
    keys: list[SourceColumn]
    measures: list[SourceColumn]
    dimension_aliases: dict[str, str]


@dataclass(frozen=True)
class MaterializationPlan:
    dimensions: list[DimensionPlan]
    fact: FactPlan


def _safe_identifier(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    if not normalized or normalized[0].isdigit():
        normalized = f"campo_{normalized}"
    return normalized[:55]


def _sqlserver_identifier(value: str) -> str:
    return "[" + value.replace("]", "]]") + "]"


def _source_table(reference: str) -> str:
    schema_name, table_name = reference.split(".", 1)
    return f"{_sqlserver_identifier(schema_name)}.{_sqlserver_identifier(table_name)}"


def _postgres_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _calculated_source_expression(column: SourceColumn, alias: str = "t0") -> str:
    if column.calculation_operation is None:
        return f"{alias}.{_sqlserver_identifier(column.source_name)}"
    inputs = [
        f"CAST({alias}.{_sqlserver_identifier(name)} AS decimal(38, 10))"
        for name in column.calculation_inputs
    ]
    operation = column.calculation_operation
    if operation == "multiply":
        return "(" + " * ".join(inputs) + ")"
    if operation == "add":
        return "(" + " + ".join(inputs) + ")"
    if operation == "subtract" and len(inputs) == 2:
        return f"({inputs[0]} - {inputs[1]})"
    if operation == "divide" and len(inputs) == 2:
        return f"({inputs[0]} / NULLIF({inputs[1]}, 0))"
    raise ValueError("La receta de medida calculada no pertenece al catálogo permitido.")


def _column_type(table: dict[str, Any], column_name: str) -> str:
    for column in table.get("columns", []):
        if isinstance(column, dict) and str(column.get("name")) == column_name:
            return str(column.get("data_type", "nvarchar"))
    return "nvarchar"


def _relations(
    schema_document: dict[str, Any],
) -> dict[str, list[tuple[str, list[str], list[str]]]]:
    graph: dict[str, list[tuple[str, list[str], list[str]]]] = {
        reference: [] for reference in metadata_tables(schema_document)
    }
    for source, table in metadata_tables(schema_document).items():
        for relation in table.get("foreign_keys", []):
            if not isinstance(relation, dict):
                continue
            target = (
                f"{relation.get('referenced_schema', '')}.{relation.get('referenced_table', '')}"
            )
            if target not in graph:
                continue
            source_columns = [str(item) for item in relation.get("columns", [])]
            target_columns = [str(item) for item in relation.get("referenced_columns", [])]
            graph[source].append((target, source_columns, target_columns))
            graph[target].append((source, target_columns, source_columns))
    return graph


def _shortest_path(
    graph: dict[str, list[tuple[str, list[str], list[str]]]], start: str, target: str
) -> list[tuple[str, str, list[str], list[str]]]:
    queue: deque[tuple[str, list[tuple[str, str, list[str], list[str]]]]] = deque([(start, [])])
    visited = {start}
    while queue:
        current, path = queue.popleft()
        if current == target:
            return path
        for neighbor, current_columns, neighbor_columns in graph.get(current, []):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            queue.append(
                (
                    neighbor,
                    [*path, (current, neighbor, current_columns, neighbor_columns)],
                )
            )
    raise ValueError(f"No existe una relación declarada entre {start} y {target}.")


def build_materialization_plan(
    proposal: dict[str, Any], schema_document: dict[str, Any]
) -> MaterializationPlan:
    tables = metadata_tables(schema_document)
    fact = proposal.get("fact", {})
    fact_sources = [str(item) for item in fact.get("source_tables", [])]
    if len(fact_sources) != 1 or fact_sources[0] not in tables:
        raise ValueError("El hecho debe conservar una única fuente comprobada.")
    fact_source = fact_sources[0]
    graph = _relations(schema_document)
    dimensions: list[DimensionPlan] = []
    for raw in proposal.get("dimensions", []):
        if not isinstance(raw, dict):
            continue
        name = _safe_identifier(str(raw.get("name", "dimension")))
        sources = [str(item) for item in raw.get("source_tables", [])]
        if len(sources) != 1 or sources[0] not in tables:
            raise ValueError(f"{name} no conserva una fuente dimensional inequívoca.")
        source_ref = sources[0]
        table = tables[source_ref]
        used_targets: set[str] = set()
        business_key_name = str(raw.get("business_key", ""))
        target_key = _safe_identifier(business_key_name)
        attributes: list[SourceColumn] = []
        for attribute in raw.get("attributes", []):
            source_name = str(attribute)
            target_name = _safe_identifier(source_name)
            if target_name == target_key or target_name in used_targets:
                continue
            attributes.append(
                SourceColumn(source_name, target_name, _column_type(table, source_name))
            )
            used_targets.add(target_name)
        key = SourceColumn(
            business_key_name,
            target_key,
            _column_type(table, business_key_name),
        )
        selected = [key, *attributes]
        select_sql = ", ".join(_sqlserver_identifier(item.source_name) for item in selected)
        query = (
            f"SELECT {select_sql} FROM {_source_table(source_ref)} "
            f"WHERE {_sqlserver_identifier(business_key_name)} IS NOT NULL "
            f"ORDER BY {_sqlserver_identifier(business_key_name)}"
        )
        dimensions.append(DimensionPlan(name, source_ref, key, attributes, query))

    alias_by_table = {fact_source: "t0"}
    joins: list[str] = []
    joined_edges: set[tuple[str, str]] = set()
    for dimension in dimensions:
        path = _shortest_path(graph, fact_source, dimension.source_ref)
        for left_ref, right_ref, left_columns, right_columns in path:
            edge = (left_ref, right_ref)
            reverse_edge = (right_ref, left_ref)
            if edge in joined_edges or reverse_edge in joined_edges:
                continue
            left_alias = alias_by_table.get(left_ref)
            if left_alias is None:
                raise ValueError(
                    "El árbol de relaciones no pudo construirse de forma determinística."
                )
            right_alias = alias_by_table.setdefault(right_ref, f"t{len(alias_by_table)}")
            conditions = " AND ".join(
                f"{left_alias}.{_sqlserver_identifier(left)} = "
                f"{right_alias}.{_sqlserver_identifier(right)}"
                for left, right in zip(left_columns, right_columns, strict=True)
            )
            joins.append(f"LEFT JOIN {_source_table(right_ref)} AS {right_alias} ON {conditions}")
            joined_edges.add(edge)

    fact_table = tables[fact_source]
    keys = [
        SourceColumn(str(name), _safe_identifier(str(name)), _column_type(fact_table, str(name)))
        for name in fact.get("business_keys", [])
    ]
    measures: list[SourceColumn] = []
    for measure in fact.get("measures", []):
        if not isinstance(measure, dict):
            continue
        source_columns = [str(item) for item in measure.get("source_columns", [])]
        calculation = (
            measure.get("calculation") if isinstance(measure.get("calculation"), dict) else None
        )
        if calculation is None and len(source_columns) != 1:
            raise ValueError("Cada medida directa debe tener una entrada comprobada.")
        if calculation is not None:
            operation = str(calculation.get("operation", ""))
            calculation_inputs = tuple(str(item) for item in calculation.get("inputs", []))
            fact_column_names = {str(item.get("name")) for item in fact_table.get("columns", [])}
            valid_width = 2 <= len(calculation_inputs) <= 4
            if operation in {"subtract", "divide"}:
                valid_width = len(calculation_inputs) == 2
            if (
                operation not in {"multiply", "add", "subtract", "divide"}
                or not valid_width
                or list(calculation_inputs) != source_columns
                or any(name not in fact_column_names for name in calculation_inputs)
            ):
                raise ValueError("La medida calculada no conserva una receta verificable.")
        else:
            operation = None
            calculation_inputs = ()
        source_name = source_columns[0]
        measures.append(
            SourceColumn(
                source_name,
                _safe_identifier(str(measure.get("name", source_name))),
                "decimal" if calculation is not None else _column_type(fact_table, source_name),
                str(measure.get("aggregation", "sum")),
                operation,
                calculation_inputs,
            )
        )
    select_parts = [
        f"t0.{_sqlserver_identifier(item.source_name)} AS {_sqlserver_identifier(item.target_name)}"
        for item in keys
    ]
    select_parts.extend(
        f"{_calculated_source_expression(item)} AS {_sqlserver_identifier(item.target_name)}"
        for item in measures
    )
    dimension_aliases: dict[str, str] = {}
    for dimension in dimensions:
        alias = alias_by_table[dimension.source_ref]
        result_alias = f"__{dimension.name}_bk"
        dimension_aliases[dimension.name] = result_alias
        select_parts.append(
            f"{alias}.{_sqlserver_identifier(dimension.business_key.source_name)} "
            f"AS {_sqlserver_identifier(result_alias)}"
        )
    query = (
        "SELECT "
        + ", ".join(select_parts)
        + f" FROM {_source_table(fact_source)} AS t0 "
        + " ".join(joins)
        + " ORDER BY "
        + ", ".join(f"t0.{_sqlserver_identifier(item.source_name)}" for item in keys)
    )
    return MaterializationPlan(
        dimensions=dimensions,
        fact=FactPlan(
            _safe_identifier(str(fact.get("name", "fact_ventas"))),
            query,
            keys,
            measures,
            dimension_aliases,
        ),
    )


def _postgres_type(data_type: str) -> str:
    value = data_type.casefold()
    if value in {"tinyint", "smallint", "int", "bigint"}:
        return "BIGINT"
    if value in {"decimal", "numeric", "money", "smallmoney", "float", "real"}:
        return "NUMERIC"
    if value in {"date"}:
        return "DATE"
    if value in {"datetime", "datetime2", "smalldatetime", "datetimeoffset"}:
        return "TIMESTAMP"
    if value in {"bit"}:
        return "BOOLEAN"
    return "TEXT"


def _clean_value(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _target_connection_string() -> str:
    return (
        f"host={settings.postgres_host} port={settings.postgres_port} "
        f"dbname={settings.postgres_db} user={settings.postgres_user} "
        f"password={settings.postgres_password.get_secret_value()}"
    )


def _detect_currency_context(
    source: Any, proposal: dict[str, Any], schema_document: dict[str, Any]
) -> dict[str, Any]:
    """Resolve one source/base currency only when relational evidence is unambiguous."""
    tables = metadata_tables(schema_document)
    fact_sources = [str(item) for item in proposal.get("fact", {}).get("source_tables", [])]
    if len(fact_sources) != 1 or fact_sources[0] not in tables:
        return {
            "status": "unresolved",
            "message": "No fue posible vincular la divisa con la fuente del hecho.",
        }
    graph = _relations(schema_document)
    candidates: list[tuple[int, str, str, str | None]] = []
    for reference, table in tables.items():
        try:
            _shortest_path(graph, fact_sources[0], reference)
        except ValueError:
            continue
        columns = {
            str(item.get("name", "")).casefold(): str(item.get("name", ""))
            for item in table.get("columns", [])
            if isinstance(item, dict)
        }
        target_column = columns.get("tocurrencycode") or columns.get("targetcurrencycode")
        for priority, normalized_name in enumerate(_CURRENCY_SOURCE_COLUMNS):
            if normalized_name in columns:
                candidates.append((priority, reference, columns[normalized_name], target_column))
                break
    for _, reference, source_column, target_column in sorted(candidates):
        cursor = source.cursor()
        cursor.execute(
            "SELECT DISTINCT TOP (3) "
            f"{_sqlserver_identifier(source_column)} FROM {_source_table(reference)} "
            f"WHERE {_sqlserver_identifier(source_column)} IS NOT NULL"
        )
        codes = sorted(
            {
                str(row[0]).strip().upper()
                for row in cursor.fetchall()
                if row[0] is not None and re.fullmatch(r"[A-Za-z]{3}", str(row[0]).strip())
            }
        )
        if len(codes) != 1:
            continue
        code = codes[0]
        return {
            "status": "verified",
            "currency_code": code,
            "basis": "source_or_base_currency",
            "source_reference": f"{reference}.{source_column}",
            "target_currency_column": (
                f"{reference}.{target_column}" if target_column is not None else None
            ),
            "message": (
                f"La divisa {code} fue comprobada como moneda de origen o base mediante "
                f"{reference}.{source_column}."
            ),
        }
    return {
        "status": "unresolved",
        "message": (
            "La fuente no demuestra una única divisa de origen o base. Los importes se "
            "mantienen como moneda de origen para evitar una etiqueta incorrecta."
        ),
    }


def _resolve_kpi_currency_units(
    kpis: list[dict[str, Any]], currency_context: dict[str, Any]
) -> list[dict[str, Any]]:
    code = str(currency_context.get("currency_code", ""))
    if currency_context.get("status") != "verified" or not re.fullmatch(r"[A-Z]{3}", code):
        return [dict(item) for item in kpis]
    resolved: list[dict[str, Any]] = []
    for item in kpis:
        unit = str(item.get("unit", ""))
        resolved.append(
            {
                **item,
                "unit": code if unit.casefold() in _GENERIC_MONEY_UNITS else unit,
                "unit_evidence": (
                    currency_context.get("source_reference")
                    if unit.casefold() in _GENERIC_MONEY_UNITS
                    else None
                ),
            }
        )
    return resolved


def enrich_currency_metrics(
    metrics: dict[str, Any],
    proposal: dict[str, Any],
    schema_document: dict[str, Any],
    source_configuration: DataConnection,
    source_password: str,
) -> dict[str, Any]:
    """Verify currency without repeating extraction, transformation or loading."""
    source = pyodbc.connect(
        build_connection_string(source_configuration, source_password), timeout=30
    )
    try:
        context = _detect_currency_context(source, proposal, schema_document)
    finally:
        source.close()
    raw_kpis = metrics.get("kpis", [])
    kpis = [item for item in raw_kpis if isinstance(item, dict)]
    return {
        **metrics,
        "currency_context": context,
        "kpis": _resolve_kpi_currency_units(kpis, context),
    }


def materialize_sales(
    execution_id: int,
    proposal: dict[str, Any],
    schema_document: dict[str, Any],
    source_configuration: DataConnection,
    source_password: str,
    selected_recipes: list[dict[str, Any]],
) -> dict[str, Any]:
    plan = build_materialization_plan(proposal, schema_document)
    source = pyodbc.connect(
        build_connection_string(source_configuration, source_password), timeout=60
    )
    target = psycopg.connect(_target_connection_string())
    currency_context = _detect_currency_context(source, proposal, schema_document)
    table_metrics: list[dict[str, Any]] = []
    dimension_lookups: dict[str, dict[object, int]] = {}
    localization_candidates: list[dict[str, Any]] = []
    try:
        with target.transaction(), target.cursor() as target_cursor:
            target_cursor.execute(
                f"CREATE SCHEMA IF NOT EXISTS {_postgres_identifier(DESTINATION_SCHEMA)}"
            )
            for dimension in plan.dimensions:
                temp_name = f"__next_{execution_id}_{dimension.name}"
                columns = [dimension.business_key, *dimension.attributes]
                definitions = (
                    ["surrogate_key BIGINT PRIMARY KEY"]
                    + [
                        f"{_postgres_identifier(item.target_name)} {_postgres_type(item.data_type)}"
                        for item in columns
                    ]
                    + ["etl_execution_id BIGINT NOT NULL"]
                )
                date_attributes = dimension.name == "dim_fecha"
                if date_attributes:
                    definitions[-1:-1] = [
                        "anio BIGINT NOT NULL",
                        "trimestre BIGINT NOT NULL",
                        "mes BIGINT NOT NULL",
                        "dia BIGINT NOT NULL",
                    ]
                target_cursor.execute(
                    f"DROP TABLE IF EXISTS {_postgres_identifier(DESTINATION_SCHEMA)}."
                    f"{_postgres_identifier(temp_name)}"
                )
                target_cursor.execute(
                    f"CREATE TABLE {_postgres_identifier(DESTINATION_SCHEMA)}."
                    f"{_postgres_identifier(temp_name)} ({', '.join(definitions)})"
                )
                source_cursor = source.cursor()
                source_cursor.execute(dimension.query)
                rows = source_cursor.fetchall()
                for attribute_index, attribute in enumerate(dimension.attributes, start=1):
                    if not re.search(
                        r"color|group|category|categoria|status|estado|type|tipo|class|clase|style|estilo|region",
                        attribute.source_name,
                        re.IGNORECASE,
                    ):
                        continue
                    values = sorted(
                        {
                            str(row[attribute_index]).strip()
                            for row in rows
                            if row[attribute_index] is not None
                            and 0 < len(str(row[attribute_index]).strip()) <= 80
                        }
                    )
                    if 0 < len(values) <= 50:
                        localization_candidates.append(
                            {
                                "dimension": dimension.name,
                                "source_column": attribute.source_name,
                                "target_column": attribute.target_name,
                                "values": values,
                            }
                        )
                seen: set[object] = set()
                payload: list[tuple[object, ...]] = []
                lookup: dict[object, int] = {}
                for row in rows:
                    natural_key = _clean_value(row[0])
                    if natural_key in seen:
                        continue
                    seen.add(natural_key)
                    surrogate_key = len(payload) + 1
                    lookup[natural_key] = surrogate_key
                    derived: tuple[object, ...] = ()
                    if date_attributes and isinstance(natural_key, date | datetime):
                        derived = (
                            natural_key.year,
                            ((natural_key.month - 1) // 3) + 1,
                            natural_key.month,
                            natural_key.day,
                        )
                    payload.append(
                        (
                            surrogate_key,
                            *(_clean_value(value) for value in row),
                            *derived,
                            execution_id,
                        )
                    )
                placeholders = ", ".join(
                    ["%s"] * (len(columns) + 2 + (4 if date_attributes else 0))
                )
                target_cursor.executemany(
                    f"INSERT INTO {_postgres_identifier(DESTINATION_SCHEMA)}."
                    f"{_postgres_identifier(temp_name)} VALUES ({placeholders})",
                    payload,
                )
                dimension_lookups[dimension.name] = lookup
                table_metrics.append(
                    {
                        "table": dimension.name,
                        "source_rows": len(rows),
                        "loaded_rows": len(payload),
                        "deduplicated_rows": len(rows) - len(payload),
                    }
                )

            fact_temp = f"__next_{execution_id}_{plan.fact.name}"
            fact_columns = [*plan.fact.keys, *plan.fact.measures]
            fact_definitions = [
                f"{_postgres_identifier(item.target_name)} {_postgres_type(item.data_type)}"
                for item in fact_columns
            ]
            fact_definitions.extend(
                f"{_postgres_identifier(name + '_sk')} BIGINT"
                for name in plan.fact.dimension_aliases
            )
            fact_definitions.append("etl_execution_id BIGINT NOT NULL")
            target_cursor.execute(
                f"DROP TABLE IF EXISTS {_postgres_identifier(DESTINATION_SCHEMA)}."
                f"{_postgres_identifier(fact_temp)}"
            )
            target_cursor.execute(
                f"CREATE TABLE {_postgres_identifier(DESTINATION_SCHEMA)}."
                f"{_postgres_identifier(fact_temp)} ({', '.join(fact_definitions)})"
            )
            source_cursor = source.cursor()
            source_cursor.execute(plan.fact.query)
            rows_read = 0
            rows_rejected = 0
            source_sums = {measure.target_name: Decimal("0") for measure in plan.fact.measures}
            source_counts = {measure.target_name: 0 for measure in plan.fact.measures}
            source_distinct: dict[str, set[Any]] = {
                measure.target_name: set()
                for measure in plan.fact.measures
                if measure.aggregation == "count_distinct"
            }
            source_extremes: dict[str, Decimal | None] = {
                measure.target_name: None
                for measure in plan.fact.measures
                if measure.aggregation in {"min", "max"}
            }
            insert_width = len(fact_columns) + len(plan.fact.dimension_aliases) + 1
            insert_sql = (
                f"INSERT INTO {_postgres_identifier(DESTINATION_SCHEMA)}."
                f"{_postgres_identifier(fact_temp)} VALUES ({', '.join(['%s'] * insert_width)})"
            )
            while True:
                rows = source_cursor.fetchmany(2000)
                if not rows:
                    break
                batch: list[tuple[object, ...]] = []
                for row in rows:
                    rows_read += 1
                    base_values = [_clean_value(value) for value in row[: len(fact_columns)]]
                    if any(value is None for value in base_values[: len(plan.fact.keys)]):
                        rows_rejected += 1
                        continue
                    for index, measure in enumerate(plan.fact.measures, start=len(plan.fact.keys)):
                        source_value = base_values[index]
                        if source_value is not None:
                            source_counts[measure.target_name] += 1
                            if measure.aggregation in {"sum", "average"}:
                                source_sums[measure.target_name] += Decimal(str(source_value))
                            elif measure.aggregation == "count_distinct":
                                source_distinct[measure.target_name].add(source_value)
                            elif measure.aggregation in {"min", "max"}:
                                numeric_value = Decimal(str(source_value))
                                current = source_extremes[measure.target_name]
                                if (
                                    current is None
                                    or (measure.aggregation == "min" and numeric_value < current)
                                    or (measure.aggregation == "max" and numeric_value > current)
                                ):
                                    source_extremes[measure.target_name] = numeric_value
                    dimension_values = row[len(fact_columns) :]
                    surrogate_values = [
                        dimension_lookups[name].get(_clean_value(value))
                        for name, value in zip(
                            plan.fact.dimension_aliases, dimension_values, strict=True
                        )
                    ]
                    batch.append((*base_values, *surrogate_values, execution_id))
                target_cursor.executemany(insert_sql, batch)
            source_totals: dict[str, Decimal] = {}
            for measure in plan.fact.measures:
                name = measure.target_name
                if measure.aggregation == "sum":
                    source_totals[name] = source_sums[name]
                elif measure.aggregation == "average":
                    source_totals[name] = (
                        source_sums[name] / Decimal(source_counts[name])
                        if source_counts[name]
                        else Decimal("0")
                    )
                elif measure.aggregation == "count":
                    source_totals[name] = Decimal(source_counts[name])
                elif measure.aggregation == "count_distinct":
                    source_totals[name] = Decimal(len(source_distinct[name]))
                elif measure.aggregation in {"min", "max"}:
                    source_totals[name] = source_extremes[name] or Decimal("0")
                else:
                    raise ValueError(f"La agregación {measure.aggregation} no puede conciliarse.")

            aggregate_sql = {
                "sum": "SUM({column})",
                "average": "AVG({column})",
                "count": "COUNT({column})",
                "count_distinct": "COUNT(DISTINCT {column})",
                "min": "MIN({column})",
                "max": "MAX({column})",
            }
            totals_sql = ", ".join(
                "COALESCE("
                + aggregate_sql[measure.aggregation].format(
                    column=_postgres_identifier(measure.target_name)
                )
                + ", 0)"
                for measure in plan.fact.measures
            )
            target_cursor.execute(
                f"SELECT COUNT(*){', ' if totals_sql else ''}{totals_sql} FROM "
                f"{_postgres_identifier(DESTINATION_SCHEMA)}."
                f"{_postgres_identifier(fact_temp)}"
            )
            target_result = target_cursor.fetchone()
            if target_result is None:
                raise ValueError("No fue posible comprobar la carga temporal del hecho.")
            loaded_rows = int(target_result[0])
            target_totals = {
                measure.target_name: Decimal(str(target_result[index]))
                for index, measure in enumerate(plan.fact.measures, start=1)
            }
            total_differences: dict[str, Decimal] = {}
            for measure in plan.fact.measures:
                name = measure.target_name
                difference = source_totals[name] - target_totals.get(name, Decimal("0"))
                if measure.aggregation == "average" and abs(difference) <= Decimal("1e-12"):
                    difference = Decimal("0")
                total_differences[name] = difference
            table_metrics.append(
                {
                    "table": plan.fact.name,
                    "source_rows": rows_read,
                    "loaded_rows": loaded_rows,
                    "rejected_rows": rows_rejected,
                }
            )

            stable_names = [plan.fact.name, *(item.name for item in plan.dimensions)]
            for stable_name in stable_names:
                target_cursor.execute(
                    f"DROP TABLE IF EXISTS {_postgres_identifier(DESTINATION_SCHEMA)}."
                    f"{_postgres_identifier(stable_name)}"
                )
            for dimension in plan.dimensions:
                temp_name = f"__next_{execution_id}_{dimension.name}"
                target_cursor.execute(
                    f"ALTER TABLE {_postgres_identifier(DESTINATION_SCHEMA)}."
                    f"{_postgres_identifier(temp_name)} RENAME TO "
                    f"{_postgres_identifier(dimension.name)}"
                )
            target_cursor.execute(
                f"ALTER TABLE {_postgres_identifier(DESTINATION_SCHEMA)}."
                f"{_postgres_identifier(fact_temp)} RENAME TO "
                f"{_postgres_identifier(plan.fact.name)}"
            )
            kpis: list[dict[str, Any]] = []
            kpi_values: dict[str, Decimal | None] = {}
            measure_names = {
                measure.target_name: measure.target_name for measure in plan.fact.measures
            }

            def resolve_input(value: object) -> Decimal | None:
                input_name = str(value)
                if input_name in kpi_values:
                    return kpi_values[input_name]
                return target_totals.get(_safe_identifier(input_name))

            for recipe in selected_recipes:
                details = recipe.get("recipe", {})
                kpi_value: Decimal | None = None
                if recipe.get("kind") == "aggregate":
                    measure_target = _safe_identifier(str(details.get("measure", "")))
                    if measure_target not in measure_names:
                        raise ValueError("Una receta KPI perdió su medida materializada.")
                    operation = str(details.get("operation", ""))
                    sql_operation = {
                        "sum": "SUM",
                        "count": "COUNT",
                        "count_distinct": "COUNT(DISTINCT",
                        "average": "AVG",
                        "min": "MIN",
                        "max": "MAX",
                    }.get(operation)
                    if sql_operation is None:
                        raise ValueError("Una receta KPI usa una agregación no implementada.")
                    column_sql = _postgres_identifier(measure_target)
                    expression = (
                        f"COUNT(DISTINCT {column_sql})"
                        if operation == "count_distinct"
                        else f"{sql_operation}({column_sql})"
                    )
                    target_cursor.execute(
                        f"SELECT {expression} FROM "
                        f"{_postgres_identifier(DESTINATION_SCHEMA)}."
                        f"{_postgres_identifier(plan.fact.name)}"
                    )
                    result = target_cursor.fetchone()
                    kpi_value = (
                        Decimal(str(result[0]))
                        if result is not None and result[0] is not None
                        else None
                    )
                elif recipe.get("kind") in {"ratio", "share"}:
                    numerator = resolve_input(details.get("numerator"))
                    denominator = resolve_input(details.get("denominator"))
                    if (
                        numerator is not None
                        and denominator is not None
                        and denominator != Decimal("0")
                    ):
                        kpi_value = numerator / denominator
                        if recipe.get("kind") == "share":
                            kpi_value *= Decimal(str(details.get("multiply_by", 100)))
                code = str(recipe.get("code", ""))
                kpi_values[code] = kpi_value
                kpis.append(
                    {
                        "code": code,
                        "name": recipe.get("name"),
                        "value": str(kpi_value) if kpi_value is not None else None,
                        "unit": recipe.get("unit"),
                        "status": ("reconciled" if kpi_value is not None else "not_calculable"),
                    }
                )
            reconciliation_passed = (
                rows_rejected == 0
                and rows_read == loaded_rows
                and all(value == 0 for value in total_differences.values())
            )
            return {
                "destination_schema": DESTINATION_SCHEMA,
                "tables": table_metrics,
                "reconciliation": {
                    "source_rows": rows_read,
                    "datamart_rows": loaded_rows,
                    "difference_rows": rows_read - loaded_rows,
                    "source_measure_totals": {
                        key: str(value) for key, value in source_totals.items()
                    },
                    "datamart_measure_totals": {
                        key: str(value) for key, value in target_totals.items()
                    },
                    "measure_differences": {
                        key: str(value) for key, value in total_differences.items()
                    },
                    "passed": reconciliation_passed,
                },
                "kpis": _resolve_kpi_currency_units(kpis, currency_context),
                "currency_context": currency_context,
                "semantic_interpretation": {
                    "policy": "preserve-original-add-spanish-label",
                    "status": "metadata_ready",
                    "message": (
                        "Los valores originales fueron preservados. Los mapeos categóricos "
                        "requieren revisión antes de publicar etiquetas españolas."
                    ),
                },
                "_localization_candidates": localization_candidates,
            }
    finally:
        source.close()
        target.close()


def apply_spanish_labels(execution_id: int, mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add reviewed Spanish labels without replacing source values."""
    applied: list[dict[str, Any]] = []
    with (
        psycopg.connect(_target_connection_string()) as connection,
        connection.transaction(),
        connection.cursor() as cursor,
    ):
        for item in mappings:
            dimension = _safe_identifier(str(item.get("dimension", "")))
            source_column = _safe_identifier(str(item.get("target_column", "")))
            label_column = f"{source_column}_es"[:60]
            values = item.get("mappings", [])
            if not dimension or not source_column or not isinstance(values, list):
                continue
            cursor.execute(
                f"ALTER TABLE {_postgres_identifier(DESTINATION_SCHEMA)}."
                f"{_postgres_identifier(dimension)} ADD COLUMN IF NOT EXISTS "
                f"{_postgres_identifier(label_column)} TEXT"
            )
            covered = 0
            for mapping in values:
                if not isinstance(mapping, dict):
                    continue
                original = str(mapping.get("original", ""))
                label_es = str(mapping.get("label_es", ""))
                if not original or not label_es:
                    continue
                cursor.execute(
                    f"UPDATE {_postgres_identifier(DESTINATION_SCHEMA)}."
                    f"{_postgres_identifier(dimension)} SET "
                    f"{_postgres_identifier(label_column)} = %s WHERE "
                    f"{_postgres_identifier(source_column)} = %s AND "
                    "etl_execution_id = %s",
                    (label_es, original, execution_id),
                )
                covered += cursor.rowcount
            applied.append(
                {
                    "dimension": dimension,
                    "source_column": source_column,
                    "label_column": label_column,
                    "values_covered": covered,
                    "mappings": values,
                }
            )
    return applied


def discover_spanish_label_candidates(execution_id: int) -> list[dict[str, Any]]:
    """Rediscover safe low-cardinality categories from an already loaded datamart."""
    candidates: list[dict[str, Any]] = []
    eligible_name = re.compile(
        r"color|group|category|categoria|status|estado|type|tipo|class|clase|style|estilo|region",
        re.IGNORECASE,
    )
    with psycopg.connect(_target_connection_string()) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name LIKE 'dim_%%'
              AND data_type IN ('text', 'character varying', 'character')
            ORDER BY table_name, ordinal_position
            """,
            (DESTINATION_SCHEMA,),
        )
        for table_name, column_name in cursor.fetchall():
            table = str(table_name)
            column = str(column_name)
            if column.endswith("_es") or not eligible_name.search(column):
                continue
            cursor.execute(
                f"SELECT DISTINCT {_postgres_identifier(column)} FROM "
                f"{_postgres_identifier(DESTINATION_SCHEMA)}.{_postgres_identifier(table)} "
                f"WHERE etl_execution_id = %s AND {_postgres_identifier(column)} IS NOT NULL "
                f"LIMIT 51",
                (execution_id,),
            )
            values = sorted(
                {
                    str(row[0]).strip()
                    for row in cursor.fetchall()
                    if 0 < len(str(row[0]).strip()) <= 80
                }
            )
            if 0 < len(values) <= 50:
                candidates.append(
                    {
                        "dimension": table,
                        "source_column": column,
                        "target_column": column,
                        "values": values,
                    }
                )
    return candidates
