from __future__ import annotations

from dataclasses import dataclass

import pyodbc  # type: ignore[import-not-found]

from app.core.config import settings
from app.modules.parameters.models import DataConnection


@dataclass(frozen=True)
class SqlServerTestResult:
    ok: bool
    message: str


def _odbc_value(value: str) -> str:
    """Quotes an ODBC value so delimiters cannot become connection options."""
    return "{" + value.replace("}", "}}") + "}"


def build_connection_string(configuration: DataConnection, password: str) -> str:
    """Builds the driver-owned connection string from separately validated fields."""
    encrypt = "yes" if configuration.encrypt else "no"
    trust = "yes" if configuration.trust_server_certificate else "no"
    return (
        f"DRIVER={{{settings.sqlserver_driver}}};"
        f"SERVER={configuration.host},{configuration.port};"
        f"DATABASE={configuration.database_name};"
        f"UID={configuration.username};PWD={_odbc_value(password)};"
        f"Encrypt={encrypt};TrustServerCertificate={trust};"
        "ApplicationIntent=ReadOnly;"
    )


def test_sqlserver_read_only(
    configuration: DataConnection, password: str, timeout_seconds: int
) -> SqlServerTestResult:
    connection = pyodbc.connect(
        build_connection_string(configuration, password),
        timeout=timeout_seconds,
    )
    try:
        connection.timeout = timeout_seconds
        cursor = connection.cursor()
        cursor.execute("SELECT TOP (1) name FROM sys.tables ORDER BY name")
        cursor.fetchone()
        cursor.execute(
            """
            SELECT
                IS_MEMBER('db_owner'),
                IS_MEMBER('db_datawriter'),
                HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'INSERT'),
                HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'UPDATE'),
                HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'DELETE'),
                HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'CREATE TABLE'),
                HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'CONTROL')
            """
        )
        permissions = cursor.fetchone()
        if permissions is None or any(value == 1 for value in permissions):
            return SqlServerTestResult(
                ok=False,
                message=(
                    "La conexión funciona, pero la cuenta posee permisos de escritura "
                    "incompatibles."
                ),
            )
        return SqlServerTestResult(
            ok=True,
            message="Conexión SQL Server y cuenta de solo lectura validadas.",
        )
    finally:
        connection.close()
