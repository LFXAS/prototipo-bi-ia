from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.analytics.router import (
    _ANALYTICS_COPILOT_INSTRUCTION,
    _ANALYTICS_COPILOT_SCHEMA,
    _ANALYTICS_INTENT_INSTRUCTION,
    _analytics_intent_schema,
    _available_query_dimensions,
    _business_scope_caveat,
    _leading_territory_requested,
    _leading_territory_value,
    _platform_caveat,
    _require_snapshot_connection,
    _suggested_questions,
)
from app.modules.analytics.schemas import (
    AnalyticsCopilotRequest,
    AnalyticsDashboardRead,
    AnalyticsFiltersRead,
    AnalyticsOptionRead,
    AnalyticsPointRead,
    AnalyticsQualityRead,
    AnalyticsQueryEvidenceRead,
    AnalyticsVisualRead,
)


def test_analytics_copilot_normalizes_question_and_limits_history() -> None:
    payload = AnalyticsCopilotRequest(
        question="  ¿Qué   resultado   debería revisar primero?  ",
        history=[],
        data_connection_id=1,
        execution_id=7,
    )

    assert payload.question == "¿Qué resultado debería revisar primero?"
    assert payload.data_connection_id == 1
    assert payload.execution_id == 7


def test_analytics_copilot_requires_explicit_source_context() -> None:
    with pytest.raises(ValidationError):
        AnalyticsCopilotRequest(
            question="¿Qué resultado debería revisar primero?",
            history=[],
            execution_id=7,
        )


def test_dashboard_rejects_execution_from_another_source() -> None:
    snapshot = SimpleNamespace(data_connection_id=2)

    with pytest.raises(HTTPException) as caught:
        _require_snapshot_connection(snapshot, 1)  # type: ignore[arg-type]

    assert caught.value.status_code == 409
    assert "no pertenece a la fuente" in str(caught.value.detail)


def test_analytics_copilot_instruction_separates_observation_from_causes() -> None:
    instruction = _ANALYTICS_COPILOT_INSTRUCTION.casefold()

    assert "no inventes cifras, causas" in instruction
    assert "nunca enumeres causas hipotéticas" in instruction
    assert "no generes sql" in instruction


def test_order_scope_survives_provider_omission() -> None:
    scope = _business_scope_caveat(
        "Alcance: líneas de pedido registradas; estos importes no equivalen "
        "necesariamente a facturas emitidas. Resumen del datamart."
    )
    assert "facturas emitidas" in scope
    caveat = _platform_caveat(scope)
    assert caveat.startswith(scope)
    assert "SCD2" not in caveat
    assert "fueran vigentes en la fecha del hecho" in caveat
    assert "fecha del hecho no demuestra" in caveat
    assert caveat.endswith("demanda de mercado.")
    assert _business_scope_caveat("Ventas conciliadas.") == ""


def test_intent_schema_closes_metrics_years_and_territories_to_real_options() -> None:
    dashboard = AnalyticsDashboardRead(
        execution_id=7,
        proposal_id=52,
        data_connection_id=1,
        source_name="AdventureWorks local",
        database_name="AdventureWorks2022",
        title="Ventas",
        description="Ventas conciliadas",
        grain="Una fila por detalle",
        refreshed_at=datetime.now(UTC),
        currency_code="USD",
        currency_status="verified",
        reconciliation_passed=True,
        period_label="Todos los períodos",
        metric_code="total_units",
        available_metrics=[
            AnalyticsOptionRead(value="total_units", label="Unidades vendidas"),
            AnalyticsOptionRead(value="total_sales", label="Ventas netas"),
        ],
        filters=AnalyticsFiltersRead(
            years=[AnalyticsOptionRead(value="2014", label="2014")],
            territories=[AnalyticsOptionRead(value="Europe", label="Europa")],
        ),
        kpis=[],
        visuals=[],
        insights=[],
        quality=AnalyticsQualityRead(
            source_rows=1,
            datamart_rows=1,
            difference_rows=0,
            reconciliation_passed=True,
            tables_loaded=1,
        ),
    )

    properties = _analytics_intent_schema(dashboard)["properties"]
    assert isinstance(properties, dict)
    assert properties["metric_code"]["enum"] == ["total_units", "total_sales"]
    assert properties["year"]["enum"] == ["__dashboard__", "__all__", "2014"]
    assert properties["territory"]["enum"] == ["__dashboard__", "__all__", "Europe"]
    assert "no generes sql" in _ANALYTICS_INTENT_INSTRUCTION.casefold()


def test_leading_territory_is_resolved_from_visible_verified_options() -> None:
    dashboard = AnalyticsDashboardRead(
        execution_id=7,
        proposal_id=52,
        data_connection_id=1,
        source_name="Fuente comercial",
        database_name="BaseComercial",
        title="Ventas",
        description="Ventas conciliadas",
        grain="Una fila por detalle",
        refreshed_at=datetime.now(UTC),
        currency_code="USD",
        currency_status="verified",
        reconciliation_passed=True,
        period_label="Todos los períodos",
        metric_code="total_sales",
        available_metrics=[AnalyticsOptionRead(value="total_sales", label="Ventas")],
        filters=AnalyticsFiltersRead(
            years=[],
            territories=[
                AnalyticsOptionRead(value="Southwest", label="Suroeste"),
                AnalyticsOptionRead(value="Northwest", label="Noroeste"),
            ],
        ),
        kpis=[],
        visuals=[
            AnalyticsVisualRead(
                code="territories",
                title="Territorios",
                subtitle="Ventas por territorio",
                kind="donut",
                dimension="territorio",
                points=[AnalyticsPointRead(key="Southwest", label="Suroeste", value=100, share=60)],
            )
        ],
        insights=[],
        quality=AnalyticsQualityRead(
            source_rows=1,
            datamart_rows=1,
            difference_rows=0,
            reconciliation_passed=True,
            tables_loaded=1,
        ),
    )

    assert _leading_territory_requested("¿Cuáles son los 5 productos del territorio líder?")
    assert _leading_territory_requested("Top products in the leading territory")
    assert _leading_territory_value(dashboard) == "Southwest"


def _catalog_dashboard(
    metrics: list[tuple[str, str]], visual_codes: list[str]
) -> AnalyticsDashboardRead:
    return AnalyticsDashboardRead(
        execution_id=18,
        proposal_id=122,
        data_connection_id=1,
        source_name="Fuente de prueba",
        database_name="Datos de prueba",
        title="Análisis",
        description="Resultados del alcance publicado",
        grain="Una fila por evento",
        refreshed_at=datetime.now(UTC),
        currency_code="USD",
        currency_status="verified",
        reconciliation_passed=True,
        period_label="2014",
        metric_code=metrics[0][0] if metrics else "none",
        available_metrics=[AnalyticsOptionRead(value=code, label=label) for code, label in metrics],
        filters=AnalyticsFiltersRead(years=[], territories=[], selected_year=2014),
        kpis=[],
        visuals=[
            AnalyticsVisualRead(
                code=code,
                title=code,
                subtitle="Resultados disponibles",
                kind="line" if code == "trend" else "bar",
                dimension=code,
                points=[],
            )
            for code in visual_codes
        ],
        insights=[],
        quality=AnalyticsQualityRead(
            source_rows=1,
            datamart_rows=1,
            difference_rows=0,
            reconciliation_passed=True,
            tables_loaded=1,
        ),
    )


def test_suggested_questions_use_only_partial_published_catalog() -> None:
    dashboard = _catalog_dashboard(
        [("amount", "Importe registrado"), ("quantity", "Unidades"), ("documents", "Pedidos")],
        ["trend", "products"],
    )

    questions = _suggested_questions(dashboard)

    assert len(questions) == 3
    assert all("por producto" in question for question in questions)
    assert all("filtros actuales" in question for question in questions)
    assert all(
        label in " ".join(questions)
        for _, label in [("a", "Importe registrado"), ("q", "Unidades"), ("d", "Pedidos")]
    )
    assert not any(
        word in " ".join(questions).casefold()
        for word in ("margen", "rentabilidad", "cliente", "territorio")
    )
    properties = _analytics_intent_schema(dashboard)["properties"]
    assert properties["dimension"]["enum"] == ["none", "product"]


@pytest.mark.parametrize("label", ["Índice Zeta", "Metric Ω-42", "x'); DROP TABLE mart; --"])
def test_suggested_questions_do_not_infer_capabilities_from_metric_names(label: str) -> None:
    dashboard = _catalog_dashboard([("arbitrary_code", label)], ["products", "customers"])

    questions = _suggested_questions(dashboard)

    assert all(label in question for question in questions)
    assert _available_query_dimensions(dashboard) == ["product", "customer"]
    assert all(len(question) <= 500 for question in questions)


def test_followups_without_spatial_dimensions_stay_with_visible_values_and_trend() -> None:
    dashboard = _catalog_dashboard([("metric", "Importe registrado")], ["trend"])

    questions = _suggested_questions(dashboard)

    assert len(questions) == 2
    assert "valor" in questions[0]
    assert "períodos mostrados" in questions[1]
    assert _analytics_intent_schema(dashboard)["properties"]["dimension"]["enum"] == ["none"]
    assert _suggested_questions(_catalog_dashboard([], [])) == []


def test_provider_response_contract_does_not_ask_for_free_followup_questions() -> None:
    assert set(_ANALYTICS_COPILOT_SCHEMA["properties"]) == {"answer", "evidence"}
    assert set(_ANALYTICS_COPILOT_SCHEMA["required"]) == {"answer", "evidence"}


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_metric_code", ["metric_7", "metric_7'; DROP TABLE mart; --"])
@pytest.mark.parametrize(
    "provider", ["ollama-local", "gemini", "groq-cloud", "anthropic-cloud", "qwen-cloud"]
)
async def test_copilot_replaces_provider_questions_and_passes_only_closed_query_arguments(
    monkeypatch, provider_metric_code: str, provider: str
) -> None:
    from app.modules.analytics import router as analytics_router

    label = "Índice x'); DROP TABLE mart; --"
    dashboard = _catalog_dashboard([("metric_7", label)], ["products"])
    monkeypatch.setattr(analytics_router, "_load_dashboard", AsyncMock(return_value=dashboard))
    configuration = SimpleNamespace(provider_kind=provider, last_test_status="ok", model_id="test")
    monkeypatch.setattr(analytics_router, "_active_llm", AsyncMock(return_value=configuration))
    monkeypatch.setattr(analytics_router, "_llm_credential", AsyncMock(return_value="test-only"))
    llm = AsyncMock(
        side_effect=[
            {
                "analysis_mode": "aggregate",
                "metric_code": provider_metric_code,
                "dimension": "product",
                "top_n": 5,
                "order": "desc",
                "year": "__dashboard__",
                "territory": "__dashboard__",
                "interpretation": "Comparar los productos del alcance actual",
            },
            {
                "answer": "El resultado se limita a la métrica disponible en esta selección.",
                "evidence": ["Datos agregados del alcance publicado."],
                "caveat": "La ficha de transacción demuestra la ubicación histórica de la entrega.",
                "suggested_questions": ["¿Cuál es la rentabilidad y margen sin costo disponible?"],
            },
        ]
    )
    monkeypatch.setattr(analytics_router, "generate_json", llm)
    query = AsyncMock(
        return_value=AnalyticsQueryEvidenceRead(
            metric_code="metric_7",
            metric_name=label,
            unit="USD",
            dimension="product",
            dimension_label="Producto",
            top_n=5,
            order="desc",
            year=2014,
            denominator_value=100,
            denominator_definition="Total del alcance actual",
            provenance=[],
            points=[],
        )
    )
    monkeypatch.setattr(analytics_router, "run_safe_aggregate_query", query)
    monkeypatch.setattr(analytics_router, "add_audit_event", AsyncMock())
    session = AsyncMock()
    session.scalar.return_value = 30
    execution = SimpleNamespace(id=18, metadata_snapshot_id=30, started_at=None, finished_at=None)
    proposal = SimpleNamespace(
        id=122,
        proposal_document={
            "fact": {"source_tables": ["Registro.Hechos"]},
            "dimensions": [{"name": "dim_zeta", "source_tables": ["Registro.Zeta"]}],
        },
        business_goal="Comparar importes registrados, sin asumir hechos de entrega.",
        business_questions=["¿Qué categorías presentan mayor importe?"],
    )
    snapshot = SimpleNamespace(data_connection_id=1, schema_document={"schemas": []})
    session.get.side_effect = [execution, proposal, snapshot]
    payload = AnalyticsCopilotRequest(
        question=_suggested_questions(dashboard)[0], data_connection_id=1, execution_id=18
    )

    result = await analytics_router.analytics_copilot(payload, SimpleNamespace(id=1), session)

    assert result.suggested_questions == _suggested_questions(dashboard)
    assert "rentabilidad" not in " ".join(result.suggested_questions)
    assert result.caveat == _platform_caveat("")
    assert "ficha de transacción" not in result.caveat
    for call in llm.await_args_list:
        provenance = call.args[2]["data_provenance"]
        assert provenance["source"] == {
            "data_connection_id": 1,
            "source_name": dashboard.source_name,
            "database_name": dashboard.database_name,
        }
        assert provenance["dimension_value_semantics"] == "source_state_read_during_etl"
        assert provenance["dimensions"][0]["source_tables"] == ["Registro.Zeta"]
        assert provenance["scd2_implemented"] is False
        assert provenance["dimension_values_at_fact_time_verified"] is False
        assert provenance["delivery_events_verified"] is False
        assert provenance["fact_date_establishes_dimension_validity"] is False
    explanation_context = llm.await_args_list[1].args[2]
    assert explanation_context["selection"]["source_name"] == dashboard.source_name
    assert explanation_context["selection"]["database_name"] == dashboard.database_name
    assert explanation_context["business_need"]["goal"] == proposal.business_goal
    assert query.await_args.kwargs == {
        "metric_code": "metric_7",
        "dimension": "product",
        "top_n": 5,
        "order": "desc",
        "year": 2014,
        "territory": None,
    }
    assert set(llm.await_args_list[1].kwargs["response_schema"]["properties"]) == {
        "answer",
        "evidence",
    }
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_dashboard_only_explanation_receives_provenance_without_running_a_query(
    monkeypatch,
) -> None:
    from app.modules.analytics import router as analytics_router

    dashboard = _catalog_dashboard([("metric", "Índice disponible")], ["trend"])
    monkeypatch.setattr(analytics_router, "_load_dashboard", AsyncMock(return_value=dashboard))
    monkeypatch.setattr(
        analytics_router,
        "_active_llm",
        AsyncMock(
            return_value=SimpleNamespace(
                provider_kind="ollama-local", last_test_status="ok", model_id="test"
            )
        ),
    )
    monkeypatch.setattr(analytics_router, "_llm_credential", AsyncMock(return_value=None))
    llm = AsyncMock(
        side_effect=[
            {"analysis_mode": "dashboard", "dimension": "none"},
            {
                "answer": "El panel muestra únicamente los agregados publicados.",
                "evidence": ["Resultados de la ejecución seleccionada."],
            },
        ]
    )
    query = AsyncMock()
    monkeypatch.setattr(analytics_router, "generate_json", llm)
    monkeypatch.setattr(analytics_router, "run_safe_aggregate_query", query)
    monkeypatch.setattr(analytics_router, "add_audit_event", AsyncMock())
    session = AsyncMock()
    session.scalar.return_value = 30
    session.get.side_effect = [
        SimpleNamespace(id=18, metadata_snapshot_id=7, started_at=None, finished_at=None),
        SimpleNamespace(
            id=122, proposal_document={}, business_goal="Resumen", business_questions=[]
        ),
        SimpleNamespace(data_connection_id=1, schema_document={}),
    ]

    result = await analytics_router.analytics_copilot(
        AnalyticsCopilotRequest(question="Resume lo publicado", data_connection_id=1),
        SimpleNamespace(id=1),
        session,
    )

    query.assert_not_awaited()
    assert result.interpreted_query is None
    assert result.caveat == _platform_caveat("")
    assert llm.await_args_list[1].args[2]["data_provenance"]["execution_id"] == 18
    assert llm.await_args_list[1].args[2]["safe_aggregate_result"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("snapshot", [None, SimpleNamespace(data_connection_id=2)])
async def test_copilot_does_not_send_missing_or_cross_source_provenance(
    monkeypatch, snapshot
) -> None:
    from app.modules.analytics import router as analytics_router

    dashboard = _catalog_dashboard([("metric", "Índice disponible")], ["trend"])
    monkeypatch.setattr(analytics_router, "_load_dashboard", AsyncMock(return_value=dashboard))
    monkeypatch.setattr(
        analytics_router,
        "_active_llm",
        AsyncMock(
            return_value=SimpleNamespace(
                provider_kind="ollama-local", last_test_status="ok", model_id="test"
            )
        ),
    )
    monkeypatch.setattr(analytics_router, "_llm_credential", AsyncMock(return_value=None))
    llm = AsyncMock()
    monkeypatch.setattr(analytics_router, "generate_json", llm)
    session = AsyncMock()
    session.scalar.return_value = 30
    session.get.side_effect = [
        SimpleNamespace(id=18, metadata_snapshot_id=7),
        SimpleNamespace(id=122),
        snapshot,
    ]

    with pytest.raises(HTTPException) as caught:
        await analytics_router.analytics_copilot(
            AnalyticsCopilotRequest(question="Resume lo publicado", data_connection_id=1),
            SimpleNamespace(id=1),
            session,
        )

    assert caught.value.status_code == 409
    llm.assert_not_awaited()
    session.commit.assert_not_awaited()
