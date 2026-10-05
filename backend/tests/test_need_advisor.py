from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.copilot.need_advisor import (
    combine_assessment,
    consent_target,
    metadata_context,
    review_input_hash,
    reviewed_dimensions,
    validate_draft,
)


def document() -> dict:
    return {
        "password": "never-send",
        "schemas": [
            {
                "name": "Comercial",
                "tables": [
                    {
                        "name": "Detalle",
                        "rows": [{"Importe": 999}],
                        "columns": [
                            {"name": "Id", "data_type": "int", "primary_key": True},
                            {"name": "Importe", "data_type": "decimal"},
                            {"name": "IdFactura", "data_type": "int"},
                        ],
                        "foreign_keys": [
                            {
                                "columns": ["IdFactura"],
                                "referenced_schema": "Comercial",
                                "referenced_table": "Cabecera",
                                "referenced_columns": ["Id"],
                            }
                        ],
                    },
                    {
                        "name": "Cabecera",
                        "columns": [
                            {"name": "Id", "data_type": "int", "primary_key": True},
                            {"name": "Emitida", "data_type": "date"},
                        ],
                        "foreign_keys": [],
                    },
                ],
            }
        ],
    }


def draft() -> dict:
    return {
        "suggested_goal": "Analizar el importe facturado por mes para comparar períodos.",
        "rationale": "Importes y fecha del mismo evento.",
        "scope_supported": True,
        "anchor_table": "Comercial.Detalle",
        "limitations": [],
        "requirements": [
            {
                "label": "Importe",
                "request_text": "importe facturado",
                "kind": "measure",
                "capability": "sales_amount",
                "status": "direct",
                "references": ["Comercial.Detalle.Importe"],
                "formula": "",
                "reason": "Importe registrado; confirmar impuestos.",
            },
            {
                "label": "Período",
                "request_text": "por mes",
                "kind": "date",
                "capability": "date",
                "status": "derivable",
                "references": ["Comercial.Cabecera.Emitida"],
                "formula": "agrupar por mes",
                "reason": "Fecha por FK declarada.",
            },
        ],
    }


def test_context_is_structural_allowlist_and_stable() -> None:
    original = document()
    context = metadata_context(original)
    assert "never-send" not in str(context)
    assert "999" not in str(context)
    assert "decimal" in str(context)
    assert "target_columns" in str(context)
    original["schemas"][0]["tables"].reverse()
    assert metadata_context(original) == context


def test_grounding_accepts_generic_names_but_not_invented_columns() -> None:
    assert validate_draft(document(), draft())["usable"] is True
    invented = draft()
    invented["requirements"][0]["references"] = ["Comercial.Detalle.Clima"]
    checked = validate_draft(document(), invented)
    assert checked["usable"] is False
    assert checked["requirements"][0]["status"] == "unavailable"
    assert "Comercial.Detalle.Clima" not in checked["evidence"]


def test_grounding_rejects_wrong_types_and_reverse_fanout() -> None:
    wrong_type = document()
    wrong_type["schemas"][0]["tables"][0]["columns"][1]["data_type"] = "nvarchar"
    assert not validate_draft(wrong_type, draft())["usable"]
    reversed_join = draft()
    reversed_join["anchor_table"] = "Comercial.Cabecera"
    assert not validate_draft(document(), reversed_join)["usable"]


def test_disconnected_tables_and_incomplete_composite_fk_are_not_supported() -> None:
    disconnected = document()
    disconnected["schemas"][0]["tables"][0]["foreign_keys"] = []
    assert not validate_draft(disconnected, draft())["usable"]
    malformed = document()
    malformed["schemas"][0]["tables"][0]["foreign_keys"][0]["referenced_columns"].append("Other")
    assert not validate_draft(malformed, draft())["usable"]


def test_unsupported_intent_and_semantic_limits_are_not_hidden() -> None:
    response = draft()
    response["requirements"].append(
        {
            "label": "Pronóstico por clima",
            "request_text": "pronosticar según clima",
            "kind": "unsupported",
            "capability": "other",
            "status": "unavailable",
            "references": [],
            "formula": "",
            "reason": "Sin datos de clima ni módulo predictivo.",
        }
    )
    response["limitations"] = ["Factura emitida no demuestra cobro."]
    checked = validate_draft(document(), response)
    assert not checked["usable"]
    assessment = combine_assessment({"requirements": [], "can_continue": True}, checked, "input")
    assert assessment["counts"]["unavailable"] == 1
    assert "ai:2" in assessment["requires_acknowledgement"]
    assert "ai:limitation:0" in assessment["requires_acknowledgement"]
    assert "no garantía" in assessment["review_notice"]


def test_review_binds_source_goal_questions_period_and_contract_not_exclusions() -> None:
    request = {
        "domain": "ventas",
        "goal": "Analizar ventas mensuales",
        "questions": [],
        "periodicity": {"code": "month"},
    }
    first = review_input_hash(1, "a", request)
    assert review_input_hash(2, "a", request) != first
    assert review_input_hash(1, "b", request) != first
    for key, value in (
        ("goal", "otro objetivo"),
        ("questions", ["productos"]),
        ("periodicity", {"code": "day"}),
    ):
        assert review_input_hash(1, "a", {**request, key: value}) != first
    assert review_input_hash(1, "a", {**request, "excluded_concepts": ["test"]}) == first


@pytest.mark.asyncio
async def test_no_external_call_without_consent_to_exact_destination(monkeypatch) -> None:
    from app.modules.copilot import router

    configuration = SimpleNamespace(
        id=1, provider_kind="anthropic", base_url="https://api.anthropic.com", model_id="test"
    )
    monkeypatch.setattr(router, "_active_configuration", AsyncMock(return_value=configuration))
    outbound = AsyncMock()
    monkeypatch.setattr(router, "generate_json", outbound)
    snapshot = SimpleNamespace(schema_document=document(), content_hash="hash")
    for unauthorized in (None, "previous-provider"):
        with pytest.raises(HTTPException) as error:
            await router._generate_need_advice(
                snapshot, {"goal": "test"}, "analyze", unauthorized, AsyncMock()
            )
        assert error.value.status_code == 422
    outbound.assert_not_called()
    changed = deepcopy(configuration)
    changed.base_url = "https://different.invalid"
    assert consent_target(changed) != consent_target(configuration)


@pytest.mark.asyncio
async def test_advice_sends_only_structural_context_to_mock_provider(monkeypatch) -> None:
    from app.modules.copilot import router

    configuration = SimpleNamespace(
        id=1, provider_kind="test", base_url="https://example.invalid", model_id="test"
    )
    monkeypatch.setattr(router, "_active_configuration", AsyncMock(return_value=configuration))
    monkeypatch.setattr(router, "_credential", AsyncMock(return_value=None))
    monkeypatch.setattr(router, "_parameter", AsyncMock(return_value=30))
    outbound = AsyncMock(return_value=draft())
    monkeypatch.setattr(router, "generate_json", outbound)
    snapshot = SimpleNamespace(schema_document=document(), content_hash="hash")
    await router._generate_need_advice(
        snapshot,
        {"goal": draft()["suggested_goal"]},
        "analyze",
        consent_target(configuration),
        AsyncMock(),
    )
    sent = outbound.call_args.args[2]
    assert sent["metadata"] == metadata_context(document())
    assert sent["mode"] == "analyze"
    assert "never-send" not in str(sent)


def test_derived_metric_cannot_hide_missing_operand_or_unsupported_scope() -> None:
    response = draft()
    item = response["requirements"][0]
    item.update(
        {
            "kind": "derived_measure",
            "capability": "gross_margin",
            "status": "derivable",
            "formula": "ventas - costo histórico",
        }
    )
    response["limitations"] = ["No existen costos históricos."]
    checked = validate_draft(document(), response)
    assert not checked["usable"]
    assert checked["requirements"][0]["status"] == "unavailable"
    response = draft()
    response["scope_supported"] = False
    checked = validate_draft(document(), response)
    assert not checked["usable"]
    assert checked["requirements"][-1]["code"] == "ai:scope"


@pytest.mark.asyncio
async def test_analysis_cannot_silently_change_the_goal(monkeypatch) -> None:
    from app.modules.copilot import router

    configuration = SimpleNamespace(
        id=1, provider_kind="test", base_url="https://example.invalid", model_id="test"
    )
    monkeypatch.setattr(router, "_active_configuration", AsyncMock(return_value=configuration))
    monkeypatch.setattr(router, "_credential", AsyncMock(return_value=None))
    monkeypatch.setattr(router, "_parameter", AsyncMock(return_value=30))
    outbound = AsyncMock(return_value=draft())
    monkeypatch.setattr(router, "generate_json", outbound)
    snapshot = SimpleNamespace(schema_document=document(), content_hash="hash")
    with pytest.raises(HTTPException) as error:
        await router._generate_need_advice(
            snapshot,
            {"goal": "Un objetivo diferente que no puede sustituirse"},
            "analyze",
            consent_target(configuration),
            AsyncMock(),
        )
    assert error.value.status_code == 502
    assert outbound.await_count == 2
    assert "exact_goal" in outbound.await_args.args[2]["validation_feedback"][0]


@pytest.mark.asyncio
async def test_analysis_repairs_changed_goal_once_without_replacing_it_locally(monkeypatch) -> None:
    from app.modules.copilot import router

    configuration = SimpleNamespace(
        id=1, provider_kind="test", base_url="https://example.invalid", model_id="test"
    )
    monkeypatch.setattr(router, "_active_configuration", AsyncMock(return_value=configuration))
    monkeypatch.setattr(router, "_credential", AsyncMock(return_value=None))
    monkeypatch.setattr(router, "_parameter", AsyncMock(return_value=30))
    exact_goal = "Analizar importe registrado mensual sin asumir el tratamiento tributario."
    repaired = draft()
    repaired["suggested_goal"] = exact_goal
    outbound = AsyncMock(side_effect=[draft(), repaired])
    monkeypatch.setattr(router, "generate_json", outbound)
    snapshot = SimpleNamespace(schema_document=document(), content_hash="hash")
    result, returned_configuration = await router._generate_need_advice(
        snapshot, {"goal": exact_goal}, "analyze", consent_target(configuration), AsyncMock()
    )
    assert result is repaired
    assert returned_configuration is configuration
    assert outbound.await_count == 2
    sent = outbound.await_args.args[2]
    assert sent["validation_feedback"][0]["exact_goal"] == exact_goal
    assert sent["business_request"]["goal"] == exact_goal


@pytest.mark.asyncio
async def test_proposal_generation_rejects_changed_provider_before_sending(monkeypatch) -> None:
    from app.modules.copilot import router
    from app.modules.copilot.schemas import ProposalCreate

    configuration = SimpleNamespace(
        id=1, provider_kind="test", base_url="https://example.invalid", model_id="test"
    )
    snapshot = SimpleNamespace(id=1, data_connection_id=1)
    connection = SimpleNamespace(id=1)
    session = AsyncMock()
    session.get = AsyncMock(side_effect=[snapshot, connection])
    monkeypatch.setattr(router, "_readiness", AsyncMock(return_value=SimpleNamespace(ready=True)))
    monkeypatch.setattr(router, "_latest_snapshot", AsyncMock(return_value=snapshot))
    monkeypatch.setattr(router, "_active_configuration", AsyncMock(return_value=configuration))
    outbound = AsyncMock()
    monkeypatch.setattr(router, "generate_json", outbound)
    payload = ProposalCreate(
        metadata_snapshot_id=1,
        business_goal="Analizar el importe mensual de ventas",
        business_questions=["sales_over_time"],
        viability_hash="a" * 64,
        metadata_consent_target="old-destination",
    )
    with pytest.raises(HTTPException) as error:
        await router.create_proposal(payload, SimpleNamespace(id=1), session)
    assert error.value.status_code == 422
    outbound.assert_not_called()
    session.add.assert_not_called()


def test_review_dimensions_accept_ai_capabilities_and_keep_order_without_duplicates() -> None:
    requirements = [
        {"code": "goal:date", "status": "direct"},
        {"code": "ai:0", "coverage_code": "goal:date", "status": "derivable"},
        {"code": "ai:1", "coverage_code": "goal:customer", "status": "derivable"},
        {"code": "ai:2", "coverage_code": "goal:territory", "status": "unavailable"},
    ]
    original = deepcopy(requirements)
    assert reviewed_dimensions({"requirements": requirements}) == ["date", "customer"]
    assert requirements == original


def _mock_advice_provider(monkeypatch, outbound):
    from app.modules.copilot import router

    configuration = SimpleNamespace(
        id=1, provider_kind="test", base_url="https://example.invalid", model_id="same-model"
    )
    monkeypatch.setattr(router, "_active_configuration", AsyncMock(return_value=configuration))
    monkeypatch.setattr(router, "_credential", AsyncMock(return_value=None))
    monkeypatch.setattr(router, "_parameter", AsyncMock(return_value=30))
    monkeypatch.setattr(router, "generate_json", outbound)
    return configuration


@pytest.mark.asyncio
@pytest.mark.parametrize("first_is_empty", [False, True])
async def test_suggestions_retry_once_with_validation_feedback(monkeypatch, first_is_empty) -> None:
    from app.modules.copilot import router
    from app.modules.copilot.schemas import NeedSuggestionInput

    snapshot = SimpleNamespace(id=1, schema_document=document(), content_hash="hash")
    invalid = draft()
    invalid["requirements"][0]["references"] = ["Comercial.Detalle.Inventado"]
    first = [] if first_is_empty else [invalid]
    outbound = AsyncMock(
        side_effect=[
            {"suggestions": first},
            {"suggestions": [draft()]},
        ]
    )
    configuration = _mock_advice_provider(monkeypatch, outbound)
    monkeypatch.setattr(
        router, "_validated_need_request", AsyncMock(return_value=(snapshot, {"goal": ""}, {}))
    )
    audit = AsyncMock()
    monkeypatch.setattr(router, "add_audit_event", audit)
    payload = NeedSuggestionInput(
        metadata_snapshot_id=1, metadata_consent_target=consent_target(configuration)
    )
    result = await router.suggest_business_needs(payload, SimpleNamespace(id=1), AsyncMock())
    assert result["suggestions"][0]["usable"] is True
    assert outbound.await_count == 2
    assert outbound.await_args_list[1].args[0] is configuration
    feedback = outbound.await_args_list[1].args[2]["validation_feedback"]
    expected = "ninguna sugerencia" if first_is_empty else "referencia real"
    assert expected in str(feedback)
    assert audit.await_args.args[-1]["attempts"] == 2
    assert audit.await_args.args[-1]["usable_count"] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("valid", [False, True])
async def test_suggestion_repair_is_bounded_and_never_relaxes_validation(
    monkeypatch, valid
) -> None:
    from app.modules.copilot import router
    from app.modules.copilot.schemas import NeedSuggestionInput

    snapshot = SimpleNamespace(id=1, schema_document=document(), content_hash="hash")
    response = draft()
    if not valid:
        response["anchor_table"] = "Comercial.Cabecera"
    outbound = AsyncMock(return_value={"suggestions": [response]})
    configuration = _mock_advice_provider(monkeypatch, outbound)
    monkeypatch.setattr(
        router, "_validated_need_request", AsyncMock(return_value=(snapshot, {"goal": ""}, {}))
    )
    monkeypatch.setattr(router, "add_audit_event", AsyncMock())
    result = await router.suggest_business_needs(
        NeedSuggestionInput(
            metadata_snapshot_id=1, metadata_consent_target=consent_target(configuration)
        ),
        SimpleNamespace(id=1),
        AsyncMock(),
    )
    assert result["suggestions"][0]["usable"] is valid
    assert outbound.await_count == (1 if valid else 2)
    if not valid:
        assert "ruta declarada" in str(result["suggestions"][0]["limitations"])


@pytest.mark.asyncio
@pytest.mark.parametrize("repair_valid", [False, True])
async def test_formulation_repairs_anchor_once_and_preserves_input_scope(monkeypatch, repair_valid):
    from app.modules.copilot import router
    from app.modules.copilot.schemas import BusinessNeedInput

    snapshot = SimpleNamespace(id=1, schema_document=document(), content_hash="hash")
    invalid = draft()
    invalid["anchor_table"] = "Comercial.Cabecera"
    outbound = AsyncMock(
        side_effect=[
            invalid,
            draft() if repair_valid else invalid,
        ]
    )
    configuration = _mock_advice_provider(monkeypatch, outbound)
    original_goal = "Comparar el importe registrado mensual de las facturas."
    request = {"goal": original_goal}
    monkeypatch.setattr(
        router, "_validated_need_request", AsyncMock(return_value=(snapshot, request, {}))
    )
    audit = AsyncMock()
    monkeypatch.setattr(router, "add_audit_event", audit)
    result = await router.formulate_business_need(
        BusinessNeedInput(
            metadata_snapshot_id=1,
            business_goal=original_goal,
            business_questions=["sales_over_time"],
            metadata_consent_target=consent_target(configuration),
        ),
        SimpleNamespace(id=1),
        AsyncMock(),
    )
    assert outbound.await_count == 2
    assert outbound.await_args.args[2]["business_request"] == request
    assert outbound.await_args.args[0] is configuration
    assert "ruta declarada" in str(outbound.await_args.args[2]["validation_feedback"])
    assert result["original_goal"] == original_goal
    assert result["usable"] is repair_valid
    assert audit.await_args.args[-1]["attempts"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("repair_valid", [False, True])
async def test_analysis_repairs_structural_errors_without_relaxing_validation(
    monkeypatch, repair_valid
):
    from app.modules.copilot import router

    invalid = draft()
    invalid["anchor_table"] = "Comercial.Cabecera"
    outbound = AsyncMock(side_effect=[invalid, draft() if repair_valid else invalid])
    configuration = _mock_advice_provider(monkeypatch, outbound)
    snapshot = SimpleNamespace(schema_document=document(), content_hash="hash")
    result, _ = await router._generate_need_advice(
        snapshot,
        {"goal": invalid["suggested_goal"]},
        "analyze",
        consent_target(configuration),
        AsyncMock(),
    )
    assert outbound.await_count == 2
    assert result["suggested_goal"] == invalid["suggested_goal"]
    checked = validate_draft(document(), result)
    assert checked["usable"] is repair_valid
    if not repair_valid:
        assert checked["requirements"][0]["status"] == "unavailable"
    assert "Comercial.Cabecera" in str(outbound.await_args.args[2]["validation_feedback"])


@pytest.mark.asyncio
async def test_analysis_does_not_retry_genuine_semantic_limits(monkeypatch):
    from app.modules.copilot import router

    response = draft()
    response["limitations"] = ["El esquema no demuestra el tratamiento de impuestos."]
    response["requirements"][0]["status"] = "ambiguous"
    response["requirements"][0]["reason"] = "Tratamiento tributario no demostrado."
    outbound = AsyncMock(return_value=response)
    configuration = _mock_advice_provider(monkeypatch, outbound)
    snapshot = SimpleNamespace(schema_document=document(), content_hash="hash")
    result, _ = await router._generate_need_advice(
        snapshot,
        {"goal": response["suggested_goal"]},
        "analyze",
        consent_target(configuration),
        AsyncMock(),
    )
    assert outbound.await_count == 1
    assert result["requirements"][0]["status"] == "ambiguous"


@pytest.mark.parametrize(
    ("column_name", "capability"),
    [
        ("UnitPrice", "unit_cost"),
        ("PrecioVenta", "unit_cost"),
        ("Precio_de_venta", "unit_cost"),
        ("UnitPriceDiscount", "discount_amount"),
        ("Tasa_de_descuento", "discount_amount"),
        ("Id", "sales_amount"),
        ("IdFactura", "unit_cost"),
    ],
)
def test_known_semantic_role_mismatches_are_blocked_for_english_and_spanish(
    column_name, capability
):
    metadata = document()
    table = metadata["schemas"][0]["tables"][0]
    if column_name not in {col["name"] for col in table["columns"]}:
        table["columns"].append({"name": column_name, "data_type": "decimal"})
    response = draft()
    response["requirements"][0].update(
        capability=capability, references=[f"Comercial.Detalle.{column_name}"]
    )
    checked = validate_draft(metadata, response)
    assert checked["usable"] is False
    assert checked["requirements"][0]["status"] == "unavailable"
    assert checked["requirements"][0]["validation_errors"]


@pytest.mark.parametrize("column_name", ["UnitCost", "CostoUnitario", "StandardCost"])
def test_compatible_unit_cost_remains_structurally_usable(column_name):
    metadata = document()
    metadata["schemas"][0]["tables"][0]["columns"].append(
        {"name": column_name, "data_type": "decimal"}
    )
    response = draft()
    response["requirements"][0].update(
        capability="unit_cost", references=[f"Comercial.Detalle.{column_name}"]
    )
    checked = validate_draft(metadata, response)
    assert checked["usable"] is True
    assert checked["requirements"][0]["status"] == "direct"


def test_unrecognized_financial_role_requires_interpretation_not_invented_certainty():
    metadata = document()
    metadata["schemas"][0]["tables"][0]["columns"].append(
        {"name": "MetricaX", "data_type": "decimal"}
    )
    response = draft()
    response["requirements"][0].update(
        capability="unit_cost", references=["Comercial.Detalle.MetricaX"]
    )
    checked = validate_draft(metadata, response)
    assert checked["requirements"][0]["status"] == "ambiguous"
    assert not checked["requirements"][0]["validation_errors"]


def test_discount_amount_needs_compatible_operands_and_explanatory_multiplication():
    metadata = document()
    metadata["schemas"][0]["tables"][0]["columns"].extend(
        {"name": name, "data_type": "decimal"}
        for name in ("UnitPrice", "UnitPriceDiscount", "Quantity")
    )
    response = draft()
    response["requirements"][0].update(
        kind="derived_measure",
        capability="discount_amount",
        status="derivable",
        references=[
            f"Comercial.Detalle.{name}" for name in ("UnitPrice", "UnitPriceDiscount", "Quantity")
        ],
        formula="precio × tasa × cantidad",
    )
    assert validate_draft(metadata, response)["usable"] is True
    response["requirements"][0]["formula"] = "precio + tasa + cantidad"
    checked = validate_draft(metadata, response)
    assert checked["requirements"][0]["status"] == "unavailable"


@pytest.mark.parametrize("kind", ["attribute", "identifier", "date"])
def test_financial_role_cannot_bypass_validation_by_using_another_requirement_kind(kind):
    metadata = document()
    metadata["schemas"][0]["tables"][0]["columns"].append(
        {"name": "UnitPrice", "data_type": "decimal"}
    )
    response = draft()
    response["requirements"][0].update(
        kind=kind, capability="unit_cost", references=["Comercial.Detalle.UnitPrice"]
    )
    checked = validate_draft(metadata, response)
    assert checked["requirements"][0]["status"] == "unavailable"
    assert checked["requirements"][0]["validation_errors"]


@pytest.mark.asyncio
async def test_temporal_grouping_is_not_an_arithmetic_measure_and_repair_gets_guidance(monkeypatch):
    from app.modules.copilot import router

    invalid = draft()
    invalid["requirements"].append(
        {
            **invalid["requirements"][0],
            "label": "Evolución temporal",
            "kind": "derived_measure",
            "status": "derivable",
            "references": ["Comercial.Detalle.Importe", "Comercial.Cabecera.Emitida"],
            "formula": "sumar importe por mes",
        }
    )
    checked = validate_draft(document(), invalid)
    assert checked["requirements"][-1]["status"] == "unavailable"
    assert "Agrupar un importe por fecha" in checked["requirements"][-1]["resolution"]
    outbound = AsyncMock(side_effect=[invalid, draft()])
    configuration = _mock_advice_provider(monkeypatch, outbound)
    snapshot = SimpleNamespace(schema_document=document(), content_hash="hash")
    result, _ = await router._generate_need_advice(
        snapshot,
        {"goal": invalid["suggested_goal"]},
        "analyze",
        consent_target(configuration),
        AsyncMock(),
    )
    assert outbound.await_count == 2
    feedback = str(outbound.await_args.args[2]["validation_feedback"])
    assert "kind=measure" in feedback
    assert "kind=date" in feedback
    assert validate_draft(document(), result)["usable"] is True
    assert len(result["requirements"]) == 2
