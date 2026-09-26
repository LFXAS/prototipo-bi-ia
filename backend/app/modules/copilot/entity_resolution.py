from __future__ import annotations

import re
import unicodedata
from copy import deepcopy
from typing import Any

_TEXT_TYPES = {"char", "nchar", "varchar", "nvarchar", "text", "ntext"}
_DESCRIPTIVE_TERMS = {
    "name",
    "nombre",
    "display",
    "label",
    "etiqueta",
    "title",
    "titulo",
    "first",
    "given",
    "primer",
    "middle",
    "segundo",
    "last",
    "family",
    "surname",
    "apellido",
    "legal",
    "razon",
    "denomination",
    "denominacion",
    "description",
    "descripcion",
}
_IDENTIFIER_TERMS = {
    "id",
    "key",
    "clave",
    "code",
    "codigo",
    "number",
    "numero",
    "account",
    "cuenta",
    "guid",
    "hash",
    "email",
    "correo",
    "phone",
    "telefono",
    "address",
    "direccion",
}
_PARTY_TERMS = {
    "customer",
    "client",
    "cliente",
    "buyer",
    "comprador",
    "person",
    "persona",
    "store",
    "tienda",
    "company",
    "empresa",
    "organization",
    "organizacion",
    "business",
    "entity",
    "entidad",
    "party",
    "subject",
    "sujeto",
    "holder",
    "titular",
}


def _tokens(value: object) -> set[str]:
    raw = unicodedata.normalize("NFKD", str(value))
    plain = "".join(character for character in raw if not unicodedata.combining(character))
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", plain)
    return {item for item in re.split(r"[^a-zA-Z0-9]+", separated.casefold()) if item}


def _column_type(column: dict[str, Any]) -> str:
    return str(column.get("type", column.get("data_type", ""))).casefold()


def _descriptive_columns(table: dict[str, Any]) -> list[str]:
    ranked: list[tuple[int, int, str]] = []
    for position, column in enumerate(table.get("columns", [])):
        if not isinstance(column, dict) or not column.get("name"):
            continue
        name = str(column["name"])
        tokens = _tokens(name)
        if not any(data_type in _column_type(column) for data_type in _TEXT_TYPES):
            continue
        if tokens & _IDENTIFIER_TERMS or not tokens & _DESCRIPTIVE_TERMS:
            continue
        score = 30 * len(tokens & _DESCRIPTIVE_TERMS)
        if tokens & {"name", "nombre", "denomination", "denominacion"}:
            score += 25
        if tokens & {"first", "given", "primer"}:
            score += 20
        if tokens & {"last", "family", "surname", "apellido"}:
            score += 18
        if tokens & {"middle", "segundo"}:
            score += 8
        ranked.append((-score, position, name))
    selected = sorted(ranked)
    names = [name for _, _, name in sorted(selected, key=lambda item: item[1])]
    personal = [name for name in names if _tokens(name) & {"first", "given", "primer"}]
    personal += [name for name in names if _tokens(name) & {"middle", "segundo"}]
    personal += [
        name for name in names if _tokens(name) & {"last", "family", "surname", "apellido"}
    ]
    if personal:
        return list(dict.fromkeys(personal))[:4]
    return [name for _, _, name in selected[:2]]


def _semantic_role(dimension: dict[str, Any], semantic_map: dict[str, Any]) -> str:
    source = next(iter(dimension.get("source_tables", [])), "")
    for candidate in semantic_map.get("candidates", []):
        if isinstance(candidate, dict) and source in candidate.get("technical_refs", []):
            return str(candidate.get("business_concept", dimension.get("name", "entity")))
    return str(dimension.get("name", "entity")).removeprefix("dim_")


def _variant_kind(reference: str, local_columns: list[str]) -> str:
    tokens = _tokens(reference) | _tokens(" ".join(local_columns))
    if tokens & {"person", "persona", "individual", "people"}:
        return "person"
    if tokens & {"store", "tienda", "company", "empresa", "organization", "business"}:
        return "organization"
    return "related_entity"


def _relation_matches_identity(role: str, target: str, local_columns: list[str]) -> bool:
    relation_tokens = _tokens(target) | _tokens(" ".join(local_columns))
    role_tokens = _tokens(role)
    if role_tokens & {"customer", "client", "cliente", "buyer", "comprador"}:
        return bool(relation_tokens & _PARTY_TERMS)
    return bool(relation_tokens & (role_tokens | _PARTY_TERMS))


def _display_target(role: str) -> str:
    localized = {
        "customer": "nombre_cliente",
        "client": "nombre_cliente",
        "cliente": "nombre_cliente",
        "product": "nombre_producto",
        "producto": "nombre_producto",
        "territory": "nombre_territorio",
        "territorio": "nombre_territorio",
    }
    return localized.get(role.casefold(), f"nombre_{role}" if role else "nombre_entidad")


def _type_target(role: str) -> str:
    localized = {
        "customer": "tipo_cliente",
        "client": "tipo_cliente",
        "cliente": "tipo_cliente",
        "product": "tipo_producto",
        "producto": "tipo_producto",
        "territory": "tipo_territorio",
        "territorio": "tipo_territorio",
    }
    return localized.get(role.casefold(), f"tipo_{role}" if role else "tipo_entidad")


def enrich_dimension_labels(
    dimensions: list[dict[str, Any]],
    scope: dict[str, Any],
    semantic_map: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Add verified label recipes from semantic role, relationships and column meaning."""
    tables = {
        str(item.get("ref")): item
        for item in scope.get("tables", [])
        if isinstance(item, dict) and item.get("ref")
    }
    enriched: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for original in dimensions:
        dimension = deepcopy(original)
        source = next(iter(dimension.get("source_tables", [])), "")
        role = _semantic_role(dimension, semantic_map)
        dimension["semantic_role"] = role
        if str(dimension.get("name")) == "dim_fecha" or source not in tables:
            enriched.append(dimension)
            continue

        direct_columns = _descriptive_columns(tables[source])
        variants: list[dict[str, Any]] = []
        if direct_columns:
            variants.append(
                {
                    "kind": "base_entity",
                    "source_table": source,
                    "left_columns": [],
                    "right_columns": [],
                    "columns": direct_columns,
                    "operation": "concat_space" if len(direct_columns) > 1 else "first_non_empty",
                }
            )
        else:
            for relation in tables[source].get("foreign_keys", []):
                if not isinstance(relation, dict):
                    continue
                target = (
                    f"{relation.get('referenced_schema', '')}."
                    f"{relation.get('referenced_table', '')}"
                )
                local_columns = [str(item) for item in relation.get("columns", [])]
                right_columns = [str(item) for item in relation.get("referenced_columns", [])]
                target_table = tables.get(target)
                if (
                    target_table is None
                    or not _relation_matches_identity(role, target, local_columns)
                    or len(local_columns) != len(right_columns)
                ):
                    continue
                columns = _descriptive_columns(target_table)
                if not columns:
                    continue
                variants.append(
                    {
                        "kind": _variant_kind(target, local_columns),
                        "source_table": target,
                        "left_columns": local_columns,
                        "right_columns": right_columns,
                        "columns": columns,
                        "operation": "concat_space" if len(columns) > 1 else "first_non_empty",
                    }
                )

        if variants:
            fallback_candidates = [
                str(item)
                for item in dimension.get("attributes", [])
                if _tokens(item) & {"account", "cuenta", "code", "codigo", "number", "numero"}
            ]
            dimension["display_label"] = {
                "target_name": _display_target(role),
                "type_target_name": _type_target(role),
                "variants": variants,
                "fallback_column": fallback_candidates[0]
                if fallback_candidates
                else str(dimension.get("business_key", "")),
                "minimum_descriptive_coverage": 0.95,
            }
            diagnostics.append(
                {
                    "dimension": dimension.get("name"),
                    "semantic_role": role,
                    "status": "resolved",
                    "message": "La identidad descriptiva usa relaciones y atributos comprobados.",
                    "variants": variants,
                }
            )
        else:
            diagnostics.append(
                {
                    "dimension": dimension.get("name"),
                    "semantic_role": role,
                    "status": "review_required",
                    "message": (
                        "No se encontró una etiqueta descriptiva inequívoca; revise las rutas "
                        "verificadas antes de publicar esta dimensión."
                    ),
                    "variants": [],
                }
            )
        enriched.append(dimension)
    return enriched, diagnostics
