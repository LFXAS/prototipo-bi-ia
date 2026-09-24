from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BiProposal(Base):
    __tablename__ = "bi_proposals"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_proposal_id: Mapped[int | None] = mapped_column(
        ForeignKey("app.bi_proposals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    metadata_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("app.metadata_snapshots.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    business_goal: Mapped[str] = mapped_column(Text, nullable=False)
    business_questions: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    requested_dimensions: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    periodicity: Mapped[str] = mapped_column(String(20), nullable=False, default="month")
    domain_code: Mapped[str] = mapped_column(String(40), nullable=False, default="ventas")
    scope_document: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    semantic_map_document: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    prompt_version: Mapped[str] = mapped_column(String(30), nullable=False)
    contract_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    provider_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    model_id: Mapped[str] = mapped_column(String(160), nullable=False)
    proposal_document: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    validation_document: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings_confirmed: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("app.users.id", ondelete="SET NULL"), nullable=True
    )
    created_by_label: Mapped[str] = mapped_column(String(320), nullable=False)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("app.users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_by_label: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SemanticAdvice(Base):
    __tablename__ = "semantic_advice"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_id: Mapped[int] = mapped_column(
        ForeignKey("app.bi_proposals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    response_document: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    provider_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    model_id: Mapped[str] = mapped_column(String(160), nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("app.users.id", ondelete="SET NULL"), nullable=True
    )
    created_by_label: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
