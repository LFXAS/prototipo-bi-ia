from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EtlExecution(Base):
    __tablename__ = "etl_executions"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_id: Mapped[int] = mapped_column(
        ForeignKey("app.bi_proposals.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    metadata_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("app.metadata_snapshots.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="prepared", index=True)
    domain_code: Mapped[str] = mapped_column(String(40), nullable=False, default="ventas")
    builder_version: Mapped[str] = mapped_column(String(40), nullable=False)
    proposal_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    selection_document: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    plan_document: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    validation_document: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    metrics_document: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("app.users.id", ondelete="SET NULL"), nullable=True
    )
    created_by_label: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
