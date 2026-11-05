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
    exact_goal = (
        "Analizar el importe registrado por mes y el promedio por documento.\n"
        "No asumir cobros, moneda, impuestos ni costo histórico; conservar ese límite."
    )
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
async def test_analysis_cannot_reduce_scope_even_after_repairing_structural_evidence(
    monkeypatch,
) -> None:
    from app.modules.copilot import router

    exact_goal = (
        "Analizar el importe facturado por mes y explicar su relación con el clima externo, "
        "sin asumir cobros ni una moneda comprobada."
    )
    invalid = draft()
    invalid["suggested_goal"] = exact_goal
    invalid["anchor_table"] = "Comercial.Cabecera"
    reduced = draft()
    assert validate_draft(document(), reduced)["usable"] is True
    outbound = AsyncMock(side_effect=[invalid, reduced])
    configuration = _mock_advice_provider(monkeypatch, outbound)
    snapshot = SimpleNamespace(schema_document=document(), content_hash="hash")
    request = {"goal": exact_goal, "questions": [], "periodicity": {"code": "month"}}
    original_request = deepcopy(request)

    with pytest.raises(HTTPException) as error:
        await router._generate_need_advice(
            snapshot, request, "analyze", consent_target(configuration), AsyncMock()
        )

    assert error.value.status_code == 502
    assert outbound.await_count == 2
    assert request == original_request
    for call in outbound.await_args_list:
        assert call.args[0] is configuration
        assert call.args[2]["business_request"] == original_request
        assert call.args[2]["metadata"] == metadata_context(document())
    assert "ruta declarada" in str(outbound.await_args.args[2]["validation_feedback"])


@pytest.mark.asyncio
async def test_analysis_repair_keeps_unavailable_request_instead_of_replacing_goal(
    monkeypatch,
) -> None:
    from app.modules.copilot import router

    exact_goal = "Analizar el importe facturado mensual y su relación con el clima externo."
    preserved = draft()
    preserved["suggested_goal"] = exact_goal
    preserved["scope_supported"] = False
    preserved["requirements"].append(
        {
            "label": "Clima externo",
            "request_text": "relación con el clima externo",
            "kind": "unsupported",
            "capability": "other",
            "status": "unavailable",
            "references": [],
            "formula": "",
            "reason": "No existen datos meteorológicos externos en la instantánea.",
        }
    )
    preserved["limitations"] = ["La fuente no permite explicar una relación causal con el clima."]
    outbound = AsyncMock(side_effect=[draft(), preserved])
    configuration = _mock_advice_provider(monkeypatch, outbound)
    snapshot = SimpleNamespace(schema_document=document(), content_hash="hash")

    result, returned_configuration = await router._generate_need_advice(
        snapshot, {"goal": exact_goal}, "analyze", consent_target(configuration), AsyncMock()
    )

    assert result is preserved
    assert result["suggested_goal"] == exact_goal
    assert returned_configuration is configuration
    assert outbound.await_count == 2
    checked = validate_draft(document(), result)
    assert checked["usable"] is False
    assert any(
        item["label"] == "Clima externo" and item["status"] == "unavailable"
        for item in checked["requirements"]
    )
    assert checked["limitations"] == preserved["limitations"]
    assert outbound.await_args.args[2]["validation_feedback"][0]["exact_goal"] == exact_goal


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
    operation = router._generate_need_advice(
        snapshot,
        {"goal": invalid["suggested_goal"]},
        "analyze",
        consent_target(configuration),
        AsyncMock(),
    )
    if not repair_valid:
        with pytest.raises(HTTPException) as error:
            await operation
        assert error.value.status_code == 422
        assert outbound.await_count == 2
        assert "Comercial.Cabecera" in str(outbound.await_args.args[2]["validation_feedback"])
        return
    result, _ = await operation
    assert outbound.await_count == 2
    assert result["suggested_goal"] == invalid["suggested_goal"]
    checked = validate_draft(document(), result)
    assert checked["usable"] is repair_valid
    if not repair_valid:
        assert checked["requirements"][0]["status"] == "unavailable"
    assert "Comercial.Cabecera" in str(outbound.await_args.args[2]["validation_feedback"])


def event_advice(language: str, event: str) -> tuple[dict, dict, list[str]]:
    schema = "Operaciones" if language == "es" else "Commerce"
    event_name = {
        ("es", "order"): "Pedido",
        ("es", "invoice"): "Factura",
        ("en", "order"): "Order",
        ("en", "invoice"): "Invoice",
    }[(language, event)]
    line = f"Lineas{event_name}" if language == "es" else f"{event_name}Lines"
    header = f"{event_name}s"
    line_key = "IdLinea" if language == "es" else "LineID"
    document_key = f"Id{event_name}" if language == "es" else f"{event_name}ID"
    amount = "Importe" if language == "es" else "Amount"
    date = "Fecha" if language == "es" else "Date"
    metadata = {
        "schemas": [
            {
                "name": schema,
                "tables": [
                    {
                        "name": line,
                        "columns": [
                            {"name": line_key, "data_type": "int", "primary_key": True},
                            {"name": document_key, "data_type": "int"},
                            {"name": amount, "data_type": "decimal"},
                        ],
                        "foreign_keys": [
                            {
                                "columns": [document_key],
                                "referenced_schema": schema,
                                "referenced_table": header,
                                "referenced_columns": [document_key],
                            }
                        ],
                    },
                    {
                        "name": header,
                        "columns": [
                            {"name": document_key, "data_type": "int", "primary_key": True},
                            {"name": date, "data_type": "date"},
                        ],
                        "foreign_keys": [],
                    },
                ],
            }
        ]
    }
    response = draft()
    response["suggested_goal"] = (
        f"Analizar el importe de {event_name.lower()}s por mes y conservar "
        "la trazabilidad de línea al documento."
        if language == "es"
        else f"Analyze {event_name.lower()}s by month and preserve line to document traceability."
    )
    response["anchor_table"] = f"{schema}.{line}"
    response["requirements"][0]["references"] = [f"{schema}.{line}.{amount}"]
    response["requirements"][1]["references"] = [f"{schema}.{header}.{date}"]
    identity_refs = [f"{schema}.{line}.{line_key}", f"{schema}.{line}.{document_key}"]
    response["requirements"].append(
        {
            "label": "Trazabilidad de línea a documento",
            "request_text": "Conservar trazabilidad de cada línea a su documento",
            "kind": "identifier",
            "capability": "invoice_event",
            "status": "direct",
            "references": identity_refs,
            "formula": "",
            "reason": "Claves declaradas.",
        }
    )
    return metadata, response, identity_refs


@pytest.mark.parametrize("language", ["es", "en"])
def test_order_identity_is_not_invoice_event_and_preserves_requested_keys(language):
    metadata, response, refs = event_advice(language, "order")
    checked = validate_draft(
        metadata, response, business_request={"goal": response["suggested_goal"]}
    )
    assert checked["requirements"][-1]["status"] == "unavailable"
    assert checked["requirements"][-1]["validation_errors"]
    response["requirements"][-1]["capability"] = "transactions"
    corrected = validate_draft(
        metadata, response, business_request={"goal": response["suggested_goal"]}
    )
    identity = corrected["requirements"][-1]
    assert identity["status"] == "direct"
    assert identity["components"] == ["transactions"]
    assert identity["identity_references"] == refs
    assert identity["request_text"] == response["requirements"][-1]["request_text"]
    assert corrected["usable"] is True


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("evidence", ["document_fk", "line_only", "no_fk", "invoice_id_only"])
def test_true_invoice_event_requires_declared_document_relationship(language, evidence):
    metadata, response, _ = event_advice(language, "invoice")
    if evidence == "line_only":
        response["requirements"][-1]["references"] = response["requirements"][-1]["references"][:1]
    elif evidence == "no_fk":
        metadata["schemas"][0]["tables"][0]["foreign_keys"] = []
    elif evidence == "invoice_id_only":
        tables = metadata["schemas"][0]["tables"]
        old_header = tables[1]["name"]
        tables[1]["name"] = "UnclassifiedEntity"
        tables[0]["foreign_keys"][0]["referenced_table"] = "UnclassifiedEntity"
        response["requirements"][1]["references"] = [
            ref.replace(f".{old_header}.", ".UnclassifiedEntity.")
            for ref in response["requirements"][1]["references"]
        ]
    checked = validate_draft(
        metadata, response, business_request={"goal": response["suggested_goal"]}
    )
    identity = checked["requirements"][-1]
    assert identity["components"] == ["invoice_event"]
    assert (identity["status"] == "direct") is (evidence == "document_fk")
    assert bool(identity["validation_errors"]) is (evidence != "document_fk")


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("evidence", ["complete_pk", "partial_pk", "no_pk", "detail", "other"])
def test_invoice_header_fact_requires_positive_event_and_complete_declared_identity(
    language, evidence
):
    metadata, response, _ = event_advice(language, "invoice")
    schema = metadata["schemas"][0]
    header = schema["tables"][1]
    date = header["columns"][1]["name"]
    key = header["columns"][0]["name"]
    header["columns"].extend(
        [
            {"name": "PartitionKey", "data_type": "int", "primary_key": True},
            {"name": "RecordedAmount", "data_type": "decimal"},
        ]
    )
    if evidence == "detail":
        header["name"] += "Lines"
    elif evidence == "other":
        # A billing namespace does not make an arbitrary entity an invoice header.
        schema["name"] = "Billing"
        header["name"] = "Customers"
    if evidence == "no_pk":
        for column in header["columns"]:
            column["primary_key"] = False
    schema["tables"] = [header]
    anchor = f"{schema['name']}.{header['name']}"
    response["anchor_table"] = anchor
    response["requirements"][0]["references"] = [f"{anchor}.RecordedAmount"]
    response["requirements"][1]["references"] = [f"{anchor}.{date}"]
    response["requirements"][-1]["references"] = [f"{anchor}.{key}"]
    if evidence != "partial_pk":
        response["requirements"][-1]["references"].append(f"{anchor}.PartitionKey")
    checked = validate_draft(
        metadata, response, business_request={"goal": response["suggested_goal"]}
    )
    identity = checked["requirements"][-1]
    assert (identity["status"] == "direct") is (evidence == "complete_pk")
    assert bool(identity["validation_errors"]) is (evidence != "complete_pk")
    if evidence == "complete_pk":
        response["suggested_goal"] = "Analizar pedidos sin facturas."
        excluded = validate_draft(
            metadata, response, business_request={"goal": response["suggested_goal"]}
        )
        assert excluded["requirements"][-1]["status"] == "unavailable"


@pytest.mark.parametrize("language", ["es", "en"])
def test_invoice_namespace_header_with_declared_pk_is_not_forced_to_invent_a_self_fk(language):
    metadata, response, _ = event_advice(language, "invoice")
    schema = metadata["schemas"][0]
    header = schema["tables"][1]
    schema["name"] = "Facturacion" if language == "es" else "Billing"
    header["name"] = "Cabeceras" if language == "es" else "Headers"
    key = header["columns"][0]["name"]
    date = header["columns"][1]["name"]
    header["columns"].append({"name": "Amount", "data_type": "decimal"})
    schema["tables"] = [header]
    anchor = f"{schema['name']}.{header['name']}"
    response["anchor_table"] = anchor
    response["requirements"][0]["references"] = [f"{anchor}.Amount"]
    response["requirements"][1]["references"] = [f"{anchor}.{date}"]
    response["requirements"][-1]["references"] = [f"{anchor}.{key}"]
    checked = validate_draft(
        metadata, response, business_request={"goal": response["suggested_goal"]}
    )
    assert checked["requirements"][-1]["status"] == "direct"
    assert checked["usable"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("language", ["es", "en"])
async def test_misclassified_order_event_repairs_once_without_dropping_identity(
    monkeypatch, language
):
    from app.modules.copilot import router

    metadata, invalid, refs = event_advice(language, "order")
    repaired = deepcopy(invalid)
    repaired["requirements"][-1]["capability"] = "transactions"
    outbound = AsyncMock(side_effect=[invalid, repaired])
    configuration = _mock_advice_provider(monkeypatch, outbound)
    snapshot = SimpleNamespace(schema_document=metadata, content_hash="hash")
    request = {"goal": invalid["suggested_goal"], "questions": []}
    result, _ = await router._generate_need_advice(
        snapshot, request, "analyze", consent_target(configuration), AsyncMock()
    )
    assert outbound.await_count == 2
    assert result["suggested_goal"] == request["goal"]
    checked = validate_draft(metadata, result, business_request=request)
    assert checked["requirements"][-1]["identity_references"] == refs
    assert checked["requirements"][-1]["label"] == invalid["requirements"][-1]["label"]
    assert "capability=transactions" in str(outbound.await_args.args[2]["validation_feedback"])


@pytest.mark.asyncio
async def test_invalid_event_after_repair_cannot_be_saved_as_acknowledgeable_review(monkeypatch):
    from app.modules.copilot import router
    from app.modules.copilot.schemas import BusinessNeedInput

    metadata, invalid, _ = event_advice("es", "order")
    outbound = AsyncMock(return_value=invalid)
    configuration = _mock_advice_provider(monkeypatch, outbound)
    snapshot = SimpleNamespace(id=1, schema_document=metadata, content_hash="hash")
    request = {"goal": invalid["suggested_goal"], "questions": [], "periodicity": {"code": "month"}}
    monkeypatch.setattr(
        router, "_validated_need_request", AsyncMock(return_value=(snapshot, request, {}))
    )
    session = AsyncMock()
    with pytest.raises(HTTPException) as error:
        await router.validate_business_need_viability(
            BusinessNeedInput(
                metadata_snapshot_id=1,
                business_goal=invalid["suggested_goal"],
                business_questions=["sales_over_time"],
                metadata_consent_target=consent_target(configuration),
            ),
            SimpleNamespace(id=1),
            session,
        )
    assert error.value.status_code == 422
    assert outbound.await_count == 2
    session.add.assert_not_called()
    session.commit.assert_not_awaited()


def test_review_rule_version_invalidates_only_new_review_authorization(monkeypatch):
    from app.modules.copilot import need_advisor

    request = {
        "goal": "Analizar pedidos y conservar su trazabilidad",
        "questions": [],
        "periodicity": {"code": "month"},
    }
    current = review_input_hash(1, "snapshot", request)
    assert need_advisor.REVIEW_VERSION == "need-review-6"
    monkeypatch.setattr(need_advisor, "REVIEW_VERSION", "need-review-5")
    assert review_input_hash(1, "snapshot", request) != current


def ranking_advice(language: str) -> tuple[dict, dict]:
    metadata, response, _ = event_advice(language, "order")
    schema = metadata["schemas"][0]
    table = schema["tables"][0]
    group_table = "Productos" if language == "es" else "Products"
    group_key = "IdProducto" if language == "es" else "ProductID"
    group_label = "Nombre" if language == "es" else "Label"
    group_ref = f"{schema['name']}.{group_table}"
    table["columns"].append({"name": group_key, "data_type": "int"})
    table["foreign_keys"].append(
        {
            "columns": [group_key],
            "referenced_schema": schema["name"],
            "referenced_table": group_table,
            "referenced_columns": [group_key],
        }
    )
    schema["tables"].append(
        {
            "name": group_table,
            "columns": [
                {"name": group_key, "data_type": "int", "primary_key": True},
                {"name": group_label, "data_type": "nvarchar"},
            ],
            "foreign_keys": [],
        }
    )
    response["requirements"] = response["requirements"][:2]
    dimension_refs = [f"{response['anchor_table']}.{group_key}", f"{group_ref}.{group_label}"]
    response["requirements"].append(
        {
            "label": "Producto",
            "request_text": "Comparar por producto",
            "kind": "attribute",
            "capability": "product",
            "status": "direct",
            "references": dimension_refs,
            "formula": "",
            "reason": "Identidad de producto por FK declarada.",
        }
    )
    operation = {
        "label": "Ranking por sumas de producto",
        "request_text": "Los rankings comparan sumas por producto"
        if language == "es"
        else "Rank products by sums",
        "kind": "ranking",
        "capability": "product",
        "status": "derivable",
        "references": [*response["requirements"][0]["references"], *dimension_refs],
        "formula": "Agrupar y ordenar los agregados solicitados",
        "reason": "Operación del catálogo sobre medida y producto.",
    }
    response["suggested_goal"] = (
        "Analizar el importe registrado y productos por mes. "
        "Los rankings comparan sumas por producto."
        if language == "es"
        else "Analyze recorded amounts and products by month. Rank products by sums."
    )
    response["requirements"].insert(0, operation)
    return metadata, response


@pytest.mark.parametrize("language", ["es", "en"])
def test_ranking_is_supported_operation_with_verified_measure_dimension_and_safe_path(language):
    metadata, response = ranking_advice(language)
    checked = validate_draft(metadata, response)
    operation = checked["requirements"][0]
    assert checked["usable"] is True
    assert operation["status"] == "derivable"
    assert operation["components"] == ["sales_amount", "product"]
    assert operation["analytical_operation"]["operation"] == "group_aggregate_order"
    assert operation["analytical_operation"]["measure_requirement"] == "ai:1"
    assert operation["analytical_operation"]["dimension_requirement"] == "ai:3"
    assert not any(
        "rank" in column["name"].lower()
        for table in metadata["schemas"][0]["tables"]
        for column in table["columns"]
    )


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("gap", ["measure", "dimension", "relationship", "numeric_type"])
def test_ranking_never_becomes_available_without_all_verified_dependencies(language, gap):
    metadata, response = ranking_advice(language)
    if gap == "measure":
        response["requirements"].pop(1)
    elif gap == "dimension":
        response["requirements"].pop(3)
    elif gap == "relationship":
        metadata["schemas"][0]["tables"][0]["foreign_keys"] = metadata["schemas"][0]["tables"][0][
            "foreign_keys"
        ][:1]
    else:
        metadata["schemas"][0]["tables"][0]["columns"][2]["data_type"] = "nvarchar"
    checked = validate_draft(metadata, response)
    operation = checked["requirements"][0]
    assert operation["status"] == "unavailable"
    assert operation["validation_errors"]
    assert "analytical_operation" not in operation


@pytest.mark.asyncio
@pytest.mark.parametrize("language", ["es", "en"])
async def test_false_missing_rank_column_repairs_to_operation_without_rewriting_goal(
    monkeypatch, language
):
    from app.modules.copilot import router

    metadata, repaired = ranking_advice(language)
    invalid = deepcopy(repaired)
    invalid["requirements"][0].update(
        kind="unsupported",
        capability="other",
        status="unavailable",
        references=[],
        reason="No existe columna ranking en el origen.",
    )
    outbound = AsyncMock(side_effect=[invalid, repaired])
    configuration = _mock_advice_provider(monkeypatch, outbound)
    snapshot = SimpleNamespace(schema_document=metadata, content_hash="hash")
    request = {"goal": repaired["suggested_goal"], "questions": []}
    result, _ = await router._generate_need_advice(
        snapshot, request, "analyze", consent_target(configuration), AsyncMock()
    )
    assert outbound.await_count == 2
    assert result["suggested_goal"] == request["goal"]
    checked = validate_draft(metadata, result, business_request=request)
    assert (
        checked["requirements"][0]["analytical_operation"]["operation"] == "group_aggregate_order"
    )
    assert (
        outbound.await_args.args[2]["analytical_operations"]["ranking"]["source_column_required"]
        is False
    )
    assert "kind=ranking" in str(outbound.await_args.args[2]["validation_feedback"])


def test_ranking_does_not_claim_unimplemented_percentiles_or_hide_real_input_ambiguity():
    metadata, response = ranking_advice("es")
    response["requirements"][0]["request_text"] = "Clasificar productos por percentiles de importes"
    checked = validate_draft(metadata, response)
    assert checked["requirements"][0]["status"] == "unavailable"
    assert "analytical_operation" not in checked["requirements"][0]
    metadata, response = ranking_advice("es")
    response["requirements"][0]["status"] = "ambiguous"
    response["requirements"][3]["status"] = "ambiguous"
    response["limitations"] = [
        "La identidad descriptiva requiere revisión; la moneda es condicional."
    ]
    checked = validate_draft(metadata, response)
    assert checked["requirements"][3]["status"] == "ambiguous"
    assert checked["requirements"][0]["status"] == "ambiguous"
    assert not checked["requirements"][0]["validation_errors"]
    assert checked["limitations"] == response["limitations"]


@pytest.mark.parametrize(
    ("request_text", "supported"),
    [
        ("Clasificar productos por puntuación ponderada.", False),
        ("Clasificar productos por puntuacion ponderada.", False),
        ("Rank products by a weighted score.", False),
        ("Clasificar productos por importe sin percentiles ni puntuación nueva.", True),
        ("Rank products by amount without percentiles or new scoring.", True),
        ("No calcular puntuación; ordenar productos por importe.", True),
        ("Do not calculate scores; rank products by amount.", True),
        ("Clasificar productos por importe; no excluir percentiles.", False),
        ("Rank products by amount; do not exclude percentiles.", False),
    ],
)
def test_ranking_exclusions_and_accents_do_not_change_the_supported_operation(
    request_text, supported
):
    metadata, response = ranking_advice("es")
    response["requirements"][0]["request_text"] = request_text
    checked = validate_draft(metadata, response)
    ranking = checked["requirements"][0]
    assert (ranking["status"] == "derivable") is supported
    assert ("analytical_operation" in ranking) is supported
    assert bool(ranking["validation_errors"]) is not supported


@pytest.mark.asyncio
async def test_supported_rank_with_inputs_cannot_stay_false_unavailable_after_repair(monkeypatch):
    from app.modules.copilot import router

    metadata, response = ranking_advice("en")
    response["requirements"][0]["status"] = "unavailable"
    outbound = AsyncMock(return_value=response)
    configuration = _mock_advice_provider(monkeypatch, outbound)
    snapshot = SimpleNamespace(schema_document=metadata, content_hash="hash")
    with pytest.raises(HTTPException) as error:
        await router._generate_need_advice(
            snapshot,
            {"goal": response["suggested_goal"]},
            "analyze",
            consent_target(configuration),
            AsyncMock(),
        )
    assert error.value.status_code == 422
    assert outbound.await_count == 2


@pytest.mark.parametrize("missing", [None, "measure", "dimension"])
def test_validated_ranking_propagates_to_proposal_payload_and_requires_both_contract_outputs(
    missing,
):
    from app.modules.copilot.service import build_requirement_coverage, proposal_payload

    metadata, response = ranking_advice("es")
    checked = validate_draft(metadata, response)
    assessment = {"requirements": checked["requirements"]}
    business_request = {
        "goal": response["suggested_goal"],
        "questions": [],
        "periodicity": {"code": "month"},
        "viability_assessment": assessment,
    }
    payload = proposal_payload(
        "snapshot", "sqlserver", business_request, {"tables": []}, {"candidates": []}
    )
    proposal = {
        "fact": {
            "measures": [
                {
                    "name": "importe",
                    "semantic_role": "sales_amount",
                    "aggregation": "sum",
                    "source_columns": ["Importe"],
                }
            ]
        },
        "dimensions": [{"name": "dim_producto"}],
    }
    if missing == "measure":
        proposal["fact"]["measures"] = []
    elif missing == "dimension":
        proposal["dimensions"] = []
    coverage = build_requirement_coverage(proposal, assessment)
    operation = checked["requirements"][0]["analytical_operation"]
    assert payload["business_request"]["requirements"][0]["analytical_operation"] == operation
    assert coverage[0]["analytical_operation"] == operation
    assert coverage[0]["coverage_status"] == ("covered" if missing is None else "not_covered")


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
