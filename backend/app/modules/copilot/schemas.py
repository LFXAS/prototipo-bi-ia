from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DimensionCode = Literal["date", "product", "customer", "territory"]
ProposalStatus = Literal[
    "generating",
    "provider_failed",
    "validation_failed",
    "ready_for_review",
    "approved",
    "rejected",
    "invalidated",
    "discarded",
]
AggregationCode = Literal["sum", "count", "count_distinct", "average", "min", "max"]


class CapabilityOptionRead(BaseModel):
    code: str
    label: str
    description: str
    available: bool
    reason: str
    evidence: list[str]


class DomainCapabilityRead(BaseModel):
    code: str
    label: str
    description: str
    available: bool
    reason: str
    questions: list[CapabilityOptionRead]
    periodicities: list[CapabilityOptionRead]


class CopilotCatalogRead(BaseModel):
    metadata_snapshot_id: int
    domains: list[DomainCapabilityRead]


class ProposalCreate(BaseModel):
    metadata_snapshot_id: int = Field(gt=0)
    business_goal: str = Field(min_length=20, max_length=500)
    business_questions: list[str] = Field(min_length=1, max_length=12)
    requested_dimensions: list[DimensionCode] = Field(default_factory=list, max_length=0)
    excluded_concepts: list[str] = Field(default_factory=list, max_length=20)
    source_proposal_id: int | None = Field(default=None, gt=0)
    periodicity: str = Field(default="month", min_length=3, max_length=20)
    domain_code: Literal["ventas"] = "ventas"

    @field_validator("business_goal")
    @classmethod
    def normalized_goal(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("business_questions", "requested_dimensions", "excluded_concepts")
    @classmethod
    def unique_values(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))


class AnalysisCatalogQuestion(BaseModel):
    code: str = Field(min_length=3, max_length=80, pattern=r"^[a-z][a-z0-9_-]+$")
    label: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=300)
    prompt_instruction: str = Field(min_length=10, max_length=500)
    enabled: bool = True


class AnalysisCatalogPeriodicity(BaseModel):
    code: Literal["day", "week", "month", "quarter", "year"]
    label: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=10, max_length=240)
    enabled: bool = True


class AnalysisCatalogConfiguration(BaseModel):
    version: Literal[2] = 2
    domain_code: Literal["ventas"] = "ventas"
    questions: list[AnalysisCatalogQuestion] = Field(min_length=1, max_length=12)
    periodicities: list[AnalysisCatalogPeriodicity] = Field(min_length=1, max_length=5)


class AnalysisCatalogDomainRead(BaseModel):
    code: str
    label: str
    description: str
    enabled: bool
    implementation_status: Literal["implemented"] = "implemented"


class ProposalDecision(BaseModel):
    comment: str | None = Field(default=None, max_length=500)
    warnings_confirmed: bool = False


class ProposalReject(BaseModel):
    comment: str = Field(min_length=10, max_length=500)


class ProposalRevision(BaseModel):
    summary: str = Field(min_length=10, max_length=160)
    grain_description: str = Field(min_length=10, max_length=240)
    dimension_names: list[str] = Field(min_length=1, max_length=4)
    measure_names: list[str] = Field(min_length=1, max_length=2)
    kpi_codes: list[str] = Field(min_length=1, max_length=3)
    kpi_measure_names: dict[str, str] = Field(default_factory=dict)
    measure_aggregations: dict[str, AggregationCode] = Field(default_factory=dict)
    comment: str = Field(min_length=10, max_length=500)

    @field_validator("summary", "grain_description", "comment")
    @classmethod
    def normalized_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("dimension_names", "measure_names", "kpi_codes")
    @classmethod
    def unique_selections(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))


class ProposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_proposal_id: int | None = None
    metadata_snapshot_id: int
    business_goal: str
    business_questions: list[str]
    requested_dimensions: list[str]
    periodicity: str
    domain_code: str
    scope_document: dict[str, Any]
    semantic_map_document: dict[str, Any]
    status: str
    input_hash: str
    prompt_version: str
    contract_version: int
    provider_kind: str
    model_id: str
    proposal_document: dict[str, Any]
    validation_document: dict[str, Any]
    review_comment: str | None = None
    warnings_confirmed: bool
    created_by_label: str
    reviewed_by_label: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None


class ProposalVerificationCheck(BaseModel):
    code: str
    label: str
    passed: bool
    detail: str


class ProposalVerificationRead(BaseModel):
    proposal_id: int
    verified: bool
    approval_safe: bool
    compatibility_warning: bool
    approval_invalidated: bool = False
    checks: list[ProposalVerificationCheck]
    snapshot_hash: str
    proposal_hash: str
    replay_hash: str
    validated_reference_count: int
    rejected_reference_count: int
    validation_errors: int
    validation_warnings: int
    pending_validations: list[str]


class ReadinessComponent(BaseModel):
    ready: bool
    label: str
    detail: str
    path: str | None = None


class CopilotReadiness(BaseModel):
    ready: bool
    source: ReadinessComponent
    metadata: ReadinessComponent
    llm: ReadinessComponent
