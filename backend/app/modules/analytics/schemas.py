from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AnalyticsMetricRead(BaseModel):
    code: str
    name: str
    value: float | None
    unit: str
    status: Literal["reconciled", "not_calculable"]


class AnalyticsOptionRead(BaseModel):
    value: str
    label: str


class AnalyticsPointRead(BaseModel):
    key: str
    label: str
    value: float
    share: float | None = None


class AnalyticsVisualRead(BaseModel):
    code: str
    title: str
    subtitle: str
    kind: Literal["line", "bar", "donut"]
    dimension: str
    points: list[AnalyticsPointRead]


class AnalyticsInsightRead(BaseModel):
    code: str
    title: str
    statement: str
    evidence: str
    tone: Literal["positive", "neutral", "attention"] = "neutral"


class AnalyticsQualityRead(BaseModel):
    source_rows: int
    datamart_rows: int
    difference_rows: int
    reconciliation_passed: bool
    tables_loaded: int


class AnalyticsFiltersRead(BaseModel):
    years: list[AnalyticsOptionRead]
    territories: list[AnalyticsOptionRead]
    selected_year: int | None = None
    selected_territory: str | None = None


class AnalyticsDashboardRead(BaseModel):
    execution_id: int
    proposal_id: int
    title: str
    description: str
    grain: str
    refreshed_at: datetime
    currency_code: str
    currency_status: str
    reconciliation_passed: bool
    period_label: str
    metric_code: str
    available_metrics: list[AnalyticsOptionRead]
    filters: AnalyticsFiltersRead
    kpis: list[AnalyticsMetricRead]
    visuals: list[AnalyticsVisualRead]
    insights: list[AnalyticsInsightRead]
    quality: AnalyticsQualityRead
    guidance: list[str] = Field(default_factory=list)


class AnalyticsChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1200)


class AnalyticsCopilotRequest(BaseModel):
    question: str = Field(min_length=5, max_length=500)
    history: list[AnalyticsChatTurn] = Field(default_factory=list, max_length=8)
    view: Literal["executive", "analyst"] = "executive"
    execution_id: int | None = Field(default=None, gt=0)
    metric_code: str | None = Field(default=None, min_length=1, max_length=80)
    year: int | None = Field(default=None, ge=1900, le=2200)
    territory: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        return " ".join(value.split())


class AnalyticsQueryPointRead(BaseModel):
    label: str
    value: float
    share: float | None = None


class AnalyticsQueryEvidenceRead(BaseModel):
    metric_code: str
    metric_name: str
    unit: str
    dimension: Literal["product", "customer", "territory"]
    dimension_label: str
    top_n: int = Field(ge=1, le=20)
    order: Literal["desc", "asc"]
    year: int | None = None
    territory: str | None = None
    denominator_value: float
    denominator_definition: str
    provenance: list[str]
    points: list[AnalyticsQueryPointRead]


class AnalyticsCopilotRead(BaseModel):
    answer: str
    evidence: list[str]
    suggested_questions: list[str]
    caveat: str
    provider_kind: str
    model_id: str
    interpreted_query: AnalyticsQueryEvidenceRead | None = None
