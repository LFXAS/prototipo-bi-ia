from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.analytics.router import (
    _ANALYTICS_COPILOT_INSTRUCTION,
    _ANALYTICS_INTENT_INSTRUCTION,
    _analytics_intent_schema,
    _require_snapshot_connection,
)
from app.modules.analytics.schemas import (
    AnalyticsCopilotRequest,
    AnalyticsDashboardRead,
    AnalyticsFiltersRead,
    AnalyticsOptionRead,
    AnalyticsQualityRead,
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
