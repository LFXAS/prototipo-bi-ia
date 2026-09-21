from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MetadataSnapshot(Base):
    __tablename__ = "metadata_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "data_connection_id",
            "contract_version",
            "content_hash",
            name="uq_metadata_snapshots_source_contract_hash",
        ),
        {"schema": "app"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data_connection_id: Mapped[int] = mapped_column(
        ForeignKey("app.data_connections.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    connector_code: Mapped[str] = mapped_column(String(40), nullable=False)
    database_name: Mapped[str] = mapped_column(String(128), nullable=False)
    contract_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    schema_document: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    schema_count: Mapped[int] = mapped_column(Integer, nullable=False)
    table_count: Mapped[int] = mapped_column(Integer, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False)
    relationship_count: Mapped[int] = mapped_column(Integer, nullable=False)
    captured_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("app.users.id", ondelete="SET NULL"), nullable=True
    )
    captured_by_label: Mapped[str] = mapped_column(String(320), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
