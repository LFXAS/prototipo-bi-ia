from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EtlProposalCandidateRead(BaseModel):
    proposal_id: int
    metadata_snapshot_id: int
    business_goal: str
    periodicity: str
    provider_kind: str
    model_id: str
    created_at: datetime
    reviewed_at: datetime | None
    reviewed_by_label: str | None
    review_comment: str | None
    proposal_hash: str
    snapshot_hash: str
    summary: str
    grain: str
    fact_name: str
    dimensions: list[str]
    measures: list[str]
    kpi_count: int
    kpi_recipes: list[dict[str, Any]]
    transformation_plan: list[dict[str, Any]]
    warnings: list[str]
    eligible: bool
    blocking_reasons: list[str]
    recommended: bool = False
    latest_execution_id: int | None = None
    latest_execution_status: str | None = None
    latest_execution_at: datetime | None = None
    latest_execution_kpi_codes: list[str] = Field(default_factory=list)


class EtlProposalCatalogRead(BaseModel):
    items: list[EtlProposalCandidateRead]
    blocked_items: list[EtlProposalCandidateRead]
    recommended_proposal_id: int | None
    guidance: list[str]


class EtlExecutionCreate(BaseModel):
    proposal_id: int = Field(gt=0)
    selected_kpi_codes: list[str] = Field(min_length=1, max_length=12)
    confirmation: bool
    analyst_comment: str = Field(min_length=10, max_length=500)

    @field_validator("selected_kpi_codes")
    @classmethod
    def unique_kpis(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))

    @field_validator("analyst_comment")
    @classmethod
    def normalize_comment(cls, value: str) -> str:
        return " ".join(value.split())


class EtlExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    proposal_id: int
    metadata_snapshot_id: int
    status: str
    domain_code: str
    builder_version: str
    proposal_hash: str
    snapshot_hash: str
    selection_document: dict[str, Any]
    plan_document: dict[str, Any]
    validation_document: dict[str, Any]
    metrics_document: dict[str, Any]
    created_by_label: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class SpanishLabelMappingDecision(BaseModel):
    original: str = Field(min_length=1, max_length=80)
    label_es: str = Field(min_length=1, max_length=100)


class SpanishLabelGroupDecision(BaseModel):
    dimension: str = Field(min_length=1, max_length=60)
    target_column: str = Field(min_length=1, max_length=60)
    mappings: list[SpanishLabelMappingDecision] = Field(max_length=50)


class SpanishInterpretationDecision(BaseModel):
    confirmation: bool
    analyst_comment: str = Field(min_length=10, max_length=500)
    groups: list[SpanishLabelGroupDecision] = Field(max_length=8)

    @field_validator("analyst_comment")
    @classmethod
    def normalize_interpretation_comment(cls, value: str) -> str:
        return " ".join(value.split())
