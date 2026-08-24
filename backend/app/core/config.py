from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Prototipo BI asistido por IA"
    app_env: Literal["development", "test", "production"] = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "bi_prototype"
    postgres_user: str = "bi_app"
    postgres_password: SecretStr = SecretStr("change_me")

    sqlserver_host: str = "sqlserver"
    sqlserver_port: int = 1433
    sqlserver_database: str = "AdventureWorks2022"
    sqlserver_user: str = "bi_reader"
    sqlserver_password: SecretStr = SecretStr("change_me")
    sqlserver_driver: str = "ODBC Driver 18 for SQL Server"
    sqlserver_encrypt: bool = True
    sqlserver_trust_server_certificate: bool = True
    sqlserver_application_intent: Literal["ReadOnly"] = "ReadOnly"

    @property
    def postgres_async_url(self) -> str:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)

    @property
    def postgres_sync_url(self) -> str:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)

    @property
    def adventureworks_url(self) -> str:
        options = (
            f"DRIVER={{{self.sqlserver_driver}}};"
            f"SERVER={self.sqlserver_host},{self.sqlserver_port};"
            f"DATABASE={self.sqlserver_database};"
            f"UID={self.sqlserver_user};"
            f"PWD={self.sqlserver_password.get_secret_value()};"
            f"Encrypt={'yes' if self.sqlserver_encrypt else 'no'};"
            f"TrustServerCertificate={'yes' if self.sqlserver_trust_server_certificate else 'no'};"
            f"ApplicationIntent={self.sqlserver_application_intent};"
        )
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(options)}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
