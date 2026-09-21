from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class DomainOption:
    code: str
    label: str
    description: str
    required_term_groups: tuple[frozenset[str], ...]


@dataclass(frozen=True)
class DomainProfile:
    code: str
    label: str
    description: str
    question_options: tuple[DomainOption, ...]
    dimension_options: tuple[DomainOption, ...]
    periodicities: tuple[DomainOption, ...]
    destination_names: frozenset[str]
    dimension_destinations: tuple[tuple[str, str], ...]
    discovery_terms: frozenset[str]
    deprioritized_terms: frozenset[str]
    discovery_scope_max_tables: int

    @property
    def question_codes(self) -> frozenset[str]:
        return frozenset(option.code for option in self.question_options)

    @property
    def dimension_codes(self) -> frozenset[str]:
        return frozenset(option.code for option in self.dimension_options)


SALES_TERMS = frozenset({"sale", "sales", "venta", "ventas", "order", "pedido"})
DATE_TERMS = frozenset({"date", "datetime", "time", "fecha", "calendar", "year", "month"})
PRODUCT_TERMS = frozenset({"product", "producto", "item", "article"})
CUSTOMER_TERMS = frozenset({"customer", "cliente", "person", "store", "account"})
TERRITORY_TERMS = frozenset({"territory", "territorio", "region", "country", "state", "province"})


SALES_PROFILE = DomainProfile(
    code="ventas",
    label="Datamart de ventas",
    description=(
        "Construye una propuesta dimensional para analizar ventas, productos, clientes, "
        "territorios y su evolución temporal."
    ),
    question_options=(
        DomainOption(
            "sales_over_time",
            "Evolución de ventas en el tiempo",
            "Permite observar tendencias y comparar períodos de venta.",
            (SALES_TERMS, DATE_TERMS),
        ),
        DomainOption(
            "top_products",
            "Productos con mayor desempeño",
            "Permite ordenar productos por importe o unidades vendidas.",
            (SALES_TERMS, PRODUCT_TERMS),
        ),
        DomainOption(
            "customer_performance",
            "Desempeño por cliente",
            "Permite segmentar las ventas según el cliente asociado.",
            (SALES_TERMS, CUSTOMER_TERMS),
        ),
        DomainOption(
            "territory_performance",
            "Desempeño por territorio",
            "Permite comparar resultados comerciales por ubicación o territorio.",
            (SALES_TERMS, TERRITORY_TERMS),
        ),
    ),
    dimension_options=(
        DomainOption(
            "date",
            "Fecha",
            "Organiza el análisis por períodos de venta.",
            (DATE_TERMS,),
        ),
        DomainOption(
            "product",
            "Producto",
            "Describe los artículos incluidos en las ventas.",
            (PRODUCT_TERMS,),
        ),
        DomainOption(
            "customer",
            "Cliente",
            "Describe a la persona, cuenta o tienda que compra.",
            (CUSTOMER_TERMS,),
        ),
        DomainOption(
            "territory",
            "Territorio",
            "Describe la ubicación comercial asociada a la venta.",
            (TERRITORY_TERMS,),
        ),
    ),
    periodicities=(
        DomainOption(
            "day",
            "Diaria",
            "Agrupa resultados por día cuando existe una fecha de venta verificable.",
            (DATE_TERMS,),
        ),
        DomainOption(
            "week",
            "Semanal",
            "Agrupa resultados por semana cuando existe una fecha de venta verificable.",
            (DATE_TERMS,),
        ),
        DomainOption(
            "month",
            "Mensual",
            "Agrupa resultados por mes cuando existe una fecha de venta verificable.",
            (DATE_TERMS,),
        ),
        DomainOption(
            "quarter",
            "Trimestral",
            "Agrupa resultados por trimestre cuando existe una fecha de venta verificable.",
            (DATE_TERMS,),
        ),
        DomainOption(
            "year",
            "Anual",
            "Agrupa resultados por año cuando existe una fecha de venta verificable.",
            (DATE_TERMS,),
        ),
    ),
    destination_names=frozenset(
        {"fact_ventas", "dim_fecha", "dim_producto", "dim_cliente", "dim_territorio"}
    ),
    dimension_destinations=(
        ("date", "dim_fecha"),
        ("product", "dim_producto"),
        ("customer", "dim_cliente"),
        ("territory", "dim_territorio"),
    ),
    discovery_terms=frozenset(
        {
            "sale",
            "sales",
            "venta",
            "ventas",
            "order",
            "pedido",
            "detail",
            "line",
            "product",
            "producto",
            "customer",
            "cliente",
            "territory",
            "territorio",
            "date",
            "fecha",
            "amount",
            "total",
            "quantity",
            "qty",
            "cantidad",
        }
    ),
    deprioritized_terms=frozenset(
        {"purchase", "purchasing", "compra", "inventory", "inventario", "work"}
    ),
    discovery_scope_max_tables=6,
)

DOMAIN_PROFILES: dict[str, DomainProfile] = {SALES_PROFILE.code: SALES_PROFILE}


def default_needs_catalog_configuration() -> dict[str, object]:
    """Return the editable analysis guidance without preselecting a dimensional model."""
    return {
        "version": 2,
        "domain_code": SALES_PROFILE.code,
        "questions": [
            {
                "code": option.code,
                "label": option.label,
                "description": option.description,
                "prompt_instruction": option.description,
                "enabled": True,
            }
            for option in SALES_PROFILE.question_options
        ],
        "periodicities": [
            {
                "code": option.code,
                "label": option.label,
                "description": option.description,
                "enabled": True,
            }
            for option in SALES_PROFILE.periodicities
        ],
    }


def normalize_needs_catalog_configuration(value: object) -> dict[str, object]:
    """Validate domain guidance while keeping dimensional decisions in the LLM flow."""
    if not isinstance(value, dict):
        raise ValueError("El catálogo debe ser un objeto JSON.")
    if value.get("domain_code") != SALES_PROFILE.code:
        raise ValueError("La versión o el dominio del catálogo no es compatible.")
    defaults = default_needs_catalog_configuration()
    raw_questions = value.get("questions")
    if not isinstance(raw_questions, list) or not 1 <= len(raw_questions) <= 12:
        raise ValueError("Configure entre 1 y 12 preguntas de negocio.")
    questions: list[dict[str, object]] = []
    question_codes: set[str] = set()
    for item in raw_questions:
        if not isinstance(item, dict):
            raise ValueError("Cada pregunta debe tener una estructura válida.")
        code = str(item.get("code", "")).strip().casefold()
        label = " ".join(str(item.get("label", "")).split())
        description = " ".join(str(item.get("description", "")).split())
        prompt_instruction = " ".join(str(item.get("prompt_instruction", description)).split())
        enabled = item.get("enabled")
        if not re.fullmatch(r"[a-z][a-z0-9_-]{2,79}", code):
            raise ValueError("Cada pregunta debe conservar un identificador interno válido.")
        if code in question_codes:
            raise ValueError("No puede repetir una pregunta de negocio.")
        if not 3 <= len(label) <= 120:
            raise ValueError(f"La etiqueta {code} debe tener entre 3 y 120 caracteres.")
        if not 10 <= len(description) <= 300:
            raise ValueError(f"La explicación {code} debe tener entre 10 y 300 caracteres.")
        if not 10 <= len(prompt_instruction) <= 500:
            raise ValueError(
                f"La instrucción para la IA de {code} debe tener entre 10 y 500 caracteres."
            )
        if not isinstance(enabled, bool):
            raise ValueError(f"El estado {code} debe ser verdadero o falso.")
        question_codes.add(code)
        questions.append(
            {
                "code": code,
                "label": label,
                "description": description,
                "prompt_instruction": prompt_instruction,
                "enabled": enabled,
            }
        )

    raw_periodicities = value.get("periodicities")
    if not isinstance(raw_periodicities, list) or not 1 <= len(raw_periodicities) <= 5:
        raise ValueError("Configure entre 1 y 5 periodicidades.")
    supported = {option.code: option for option in SALES_PROFILE.periodicities}
    periodicities: list[dict[str, object]] = []
    periodicity_codes: set[str] = set()
    for item in raw_periodicities:
        if not isinstance(item, dict):
            raise ValueError("Cada periodicidad debe tener una estructura válida.")
        code = str(item.get("code", "")).strip().casefold()
        label = " ".join(str(item.get("label", "")).split())
        description = " ".join(str(item.get("description", "")).split())
        enabled = item.get("enabled")
        if code not in supported:
            raise ValueError(
                "La periodicidad no tiene una estrategia temporal implementada y validada."
            )
        if code in periodicity_codes:
            raise ValueError("No puede repetir una periodicidad.")
        if not 3 <= len(label) <= 100:
            raise ValueError(f"La etiqueta {code} debe tener entre 3 y 100 caracteres.")
        if not 10 <= len(description) <= 240:
            raise ValueError(f"La descripción {code} debe tener entre 10 y 240 caracteres.")
        if not isinstance(enabled, bool):
            raise ValueError(f"El estado {code} debe ser verdadero o falso.")
        periodicity_codes.add(code)
        periodicities.append(
            {
                "code": code,
                "label": label,
                "description": description,
                "enabled": enabled,
            }
        )

    # Upgrade the former single-period catalog without preserving its default goal or dimensions.
    if value.get("version") == 1:
        current = {str(item["code"]): item for item in periodicities}
        for item in cast(list[dict[str, object]], defaults["periodicities"]):
            current.setdefault(str(item["code"]), item)
        periodicities = list(current.values())

    return {
        "version": 2,
        "domain_code": SALES_PROFILE.code,
        "questions": questions,
        "periodicities": periodicities,
    }


def domain_profile(code: str) -> DomainProfile:
    """Return an enabled, versioned domain profile.

    Sprint 3 validates only sales. Future domains must provide their own prompts,
    catalogs and deterministic rules before being enabled in this registry.
    """
    try:
        return DOMAIN_PROFILES[code]
    except KeyError as exc:
        raise ValueError("El dominio solicitado no está habilitado.") from exc


def _tokens(value: object) -> set[str]:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(value))
    return {part for part in re.split(r"[^a-zA-Z0-9]+", text.casefold()) if part}


def _metadata_index(document: dict[str, Any]) -> tuple[set[str], dict[str, set[str]]]:
    all_tokens: set[str] = set()
    tables: dict[str, set[str]] = {}
    for schema in document.get("schemas", []):
        if not isinstance(schema, dict):
            continue
        schema_name = str(schema.get("name", ""))
        for table in schema.get("tables", []):
            if not isinstance(table, dict):
                continue
            table_name = str(table.get("name", ""))
            reference = f"{schema_name}.{table_name}"
            table_tokens = _tokens(schema_name) | _tokens(table_name)
            for column in table.get("columns", []):
                if not isinstance(column, dict):
                    continue
                table_tokens.update(_tokens(column.get("name", "")))
                table_tokens.update(_tokens(column.get("data_type", column.get("type", ""))))
            tables[reference] = table_tokens
            all_tokens.update(table_tokens)
    return all_tokens, tables


def _option_capability(
    option: DomainOption,
    all_tokens: set[str],
    tables: dict[str, set[str]],
    configured: dict[str, object],
) -> dict[str, object]:
    metadata_available = all(
        any(term in all_tokens for term in group) for group in option.required_term_groups
    )
    enabled = bool(configured["enabled"])
    available = enabled and metadata_available
    required_terms = set().union(*option.required_term_groups)
    evidence = [
        reference for reference, table_tokens in tables.items() if table_tokens & required_terms
    ][:3]
    return {
        "code": option.code,
        "label": configured["label"],
        "description": configured["description"],
        "available": available,
        "reason": (
            "La instantánea contiene metadatos compatibles con esta capacidad."
            if available
            else (
                "Esta opción está deshabilitada en el catálogo de necesidades analíticas."
                if not enabled
                else "La instantánea no contiene todavía los conceptos técnicos requeridos."
            )
        ),
        "evidence": evidence,
    }


def catalog_for_snapshot(
    document: dict[str, Any], configuration: dict[str, object] | None = None
) -> list[dict[str, object]]:
    """Build the enabled domain catalog from canonical metadata, without invoking an LLM."""
    all_tokens, tables = _metadata_index(document)
    configured_catalog = normalize_needs_catalog_configuration(
        configuration or default_needs_catalog_configuration()
    )
    question_entries = cast(list[dict[str, object]], configured_catalog["questions"])
    periodicity_entries = cast(list[dict[str, object]], configured_catalog["periodicities"])
    result: list[dict[str, object]] = []
    for profile in DOMAIN_PROFILES.values():
        metadata_available = any(term in all_tokens for term in SALES_TERMS)
        periodicity_profiles = {option.code: option for option in profile.periodicities}
        questions = [
            {
                "code": str(item["code"]),
                "label": item["label"],
                "description": item["description"],
                "available": bool(item["enabled"]) and metadata_available,
                "reason": (
                    "La pregunta orientará a la IA; no predefine tablas ni dimensiones."
                    if bool(item["enabled"]) and metadata_available
                    else (
                        "Esta pregunta está deshabilitada en el catálogo analítico."
                        if not bool(item["enabled"])
                        else "La fuente no presenta todavía un proceso de ventas reconocible."
                    )
                ),
                "evidence": [],
            }
            for item in question_entries
        ]
        periodicities = [
            _option_capability(periodicity_profiles[str(item["code"])], all_tokens, tables, item)
            for item in periodicity_entries
        ]
        domain_available = metadata_available and any(item["available"] for item in questions)
        result.append(
            {
                "code": profile.code,
                "label": profile.label,
                "description": profile.description,
                "available": domain_available,
                "reason": (
                    "La fuente permite iniciar una propuesta para este datamart."
                    if domain_available
                    else "No se detectaron capacidades suficientes para este datamart."
                ),
                "questions": questions,
                "periodicities": periodicities,
            }
        )
    return result
