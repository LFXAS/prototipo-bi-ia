from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.copilot import router
from app.modules.copilot.domains import catalog_for_snapshot, default_needs_catalog_configuration
from app.modules.copilot.need_advisor import consent_target
from app.modules.copilot.schemas import BusinessNeedInput, NeedSuggestionInput, ProposalCreate


def _metadata(language: str) -> dict:
    # Both a Spanish and an English sales structure use the same selection guard.
    schema, table, amount, date = (
        ("Comercial", "Ventas", "Importe", "Fecha")
        if language == "es"
        else ("Business", "Sales", "Amount", "Date")
    )
    return {
        "schemas": [
            {
                "name": schema,
                "tables": [
                    {
                        "name": table,
                        "columns": [
                            {"name": amount, "data_type": "decimal"},
                            {"name": date, "data_type": "date"},
                        ],
                    }
                ],
            }
        ]
    }


def _custom_catalog() -> dict:
    catalog = default_needs_catalog_configuration()
    catalog["questions"].append(
        {
            "code": "custom_sales_scope",
            "label": "Comparación comercial adicional",
            "description": "Comparar las ventas según el criterio revisado del negocio.",
            "prompt_instruction": "Comparar las ventas según el criterio revisado del negocio.",
            "enabled": True,
        }
    )
    return catalog


@pytest.mark.parametrize("language", ["es", "en"])
def test_current_custom_question_is_preserved_only_for_its_source_catalog(language):
    payload = BusinessNeedInput(
        metadata_snapshot_id=1,
        business_goal="Comparar mensualmente las ventas registradas.",
        business_questions=["sales_over_time", "custom_sales_scope"],
    )
    before = payload.model_dump()
    custom = _custom_catalog()
    router._validate_catalog_selection(payload, catalog_for_snapshot(_metadata(language), custom))
    assert payload.model_dump() == before

    # Moving the same draft to another source must not copy its custom catalog.
    with pytest.raises(HTTPException) as caught:
        router._validate_catalog_selection(payload, catalog_for_snapshot(_metadata(language)))
    assert caught.value.status_code == 422
    assert "Una pregunta guardada" in caught.value.detail
    assert "custom_sales_scope" not in caught.value.detail
    assert payload.model_dump() == before


@pytest.mark.parametrize("language", ["es", "en"])
def test_disabled_or_unsupported_choices_use_business_labels_without_rewriting_input(language):
    catalog = _custom_catalog()
    catalog["questions"][-1]["enabled"] = False
    catalog["periodicities"][2]["enabled"] = False  # month
    payload = BusinessNeedInput(
        metadata_snapshot_id=1,
        business_goal="Comparar mensualmente las ventas registradas.",
        business_questions=["custom_sales_scope", "top_products"],
    )
    before = payload.model_dump()
    with pytest.raises(HTTPException) as caught:
        router._validate_catalog_selection(
            payload, catalog_for_snapshot(_metadata(language), catalog)
        )
    assert caught.value.status_code == 422
    assert "Comparación comercial adicional" in caught.value.detail
    assert "Productos con mayor desempeño" in caught.value.detail
    assert "periodicidad" in caught.value.detail
    assert "custom_sales_scope" not in caught.value.detail
    assert "Regrese al paso Necesidad" in caught.value.detail
    assert payload.model_dump() == before


def test_suggestions_can_start_without_questions_but_still_validate_the_period():
    payload = NeedSuggestionInput(metadata_snapshot_id=1)
    catalog = catalog_for_snapshot(_metadata("es"))
    router._validate_catalog_selection(payload, catalog)
    invalid = payload.model_copy(update={"periodicity": "unsupported"})
    with pytest.raises(HTTPException) as caught:
        router._validate_catalog_selection(invalid, catalog)
    assert "periodicidad" in caught.value.detail


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["suggest", "formulate", "viability", "generate"])
async def test_stale_draft_is_rejected_before_a_provider_call_or_persistence(
    monkeypatch, operation
):
    # Reproduce the PDF: a saved draft contains three custom IDs absent from the catalog.
    removed_codes = ["custom_1795629214911", "custom_1795629691223", "custom_1795629771033"]
    snapshot = SimpleNamespace(id=3, data_connection_id=2, schema_document=_metadata("en"))
    connection = SimpleNamespace(id=2, is_active=True)
    configuration = SimpleNamespace(
        id=1, provider_kind="test", base_url="https://example.invalid", model_id="any-model"
    )
    session = AsyncMock()
    session.get.side_effect = [snapshot, connection]
    monkeypatch.setattr(router, "_latest_snapshot", AsyncMock(return_value=snapshot))
    monkeypatch.setattr(router, "_readiness", AsyncMock(return_value=SimpleNamespace(ready=True)))
    monkeypatch.setattr(router, "_active_configuration", AsyncMock(return_value=configuration))
    catalog = default_needs_catalog_configuration()
    original_catalog = deepcopy(catalog)
    lookup = AsyncMock(return_value=catalog)
    monkeypatch.setattr(router, "_needs_catalog", lookup)
    advice = AsyncMock()
    generation = AsyncMock()
    monkeypatch.setattr(router, "_generate_need_advice", advice)
    monkeypatch.setattr(router, "generate_json", generation)
    base = {
        "metadata_snapshot_id": snapshot.id,
        "business_goal": "Comparar mensualmente las ventas registradas.",
        "business_questions": ["sales_over_time", *removed_codes],
        "metadata_consent_target": consent_target(configuration),
    }
    if operation == "generate":
        payload = ProposalCreate(**base, viability_hash="a" * 64)
        action = router.create_proposal
    elif operation == "suggest":
        payload = NeedSuggestionInput(**base)
        action = router.suggest_business_needs
    else:
        payload = BusinessNeedInput(**base)
        action = (
            router.formulate_business_need
            if operation == "formulate"
            else router.validate_business_need_viability
        )
    original_payload = payload.model_dump()
    with pytest.raises(HTTPException) as caught:
        await action(payload, SimpleNamespace(id=1), session)
    assert caught.value.status_code == 422
    assert "3 preguntas guardadas" in caught.value.detail
    assert "catálogo vigente de esta fuente" in caught.value.detail
    assert all(code not in caught.value.detail for code in removed_codes)
    advice.assert_not_awaited()
    generation.assert_not_awaited()
    session.add.assert_not_called()
    session.commit.assert_not_awaited()
    lookup.assert_awaited_once_with(session, "ventas", connection.id)
    assert payload.model_dump() == original_payload
    assert catalog == original_catalog
