from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Parameter(Base):
    __tablename__ = "parameters"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    module_code: Mapped[str] = mapped_column(String(80), default="general", nullable=False)
    value_type: Mapped[str] = mapped_column(String(30), default="integer", nullable=False)
    value: Mapped[str] = mapped_column(Text)
    default_value: Mapped[str] = mapped_column(Text, default="", nullable=False)
    min_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Secret(Base):
    __tablename__ = "secrets"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    ciphertext: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LlmConfiguration(Base):
    __tablename__ = "llm_configurations"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    provider_kind: Mapped[str] = mapped_column(String(40), index=True)
    base_url: Mapped[str] = mapped_column(String(300))
    model_id: Mapped[str] = mapped_column(String(160))
    credential_reference: Mapped[str] = mapped_column(String(80))
    secret_id: Mapped[int | None] = mapped_column(
        ForeignKey("app.secrets.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_test_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_test_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    secret: Mapped[Secret | None] = relationship(lazy="raise")

    @property
    def credential_configured(self) -> bool:
        return self.provider_kind == "ollama-local" or self.secret_id is not None


class DataConnection(Base):
    __tablename__ = "data_connections"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    connector_kind: Mapped[str] = mapped_column(String(40), default="sqlserver", index=True)
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer, default=1433)
    database_name: Mapped[str] = mapped_column(String(128))
    username: Mapped[str] = mapped_column(String(128))
    encrypt: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trust_server_certificate: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    secret_id: Mapped[int] = mapped_column(
        ForeignKey("app.secrets.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_test_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_test_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    secret: Mapped[Secret] = relationship(lazy="raise")
