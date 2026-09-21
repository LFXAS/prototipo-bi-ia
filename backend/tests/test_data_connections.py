from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from pytest import MonkeyPatch

from app.modules.parameters import connections, router
from app.modules.parameters.models import DataConnection
from app.modules.parameters.schemas import DataConnectionCreate


class FakeCursor:
    timeout = 0

    def __init__(self, permissions: tuple[int, ...]) -> None:
        self.permissions = permissions
        self.query_count = 0

    def execute(self, _: str) -> FakeCursor:
        self.query_count += 1
        return self

    def fetchone(self) -> tuple[Any, ...]:
        if self.query_count == 1:
            return ("SalesOrderHeader",)
        return self.permissions


class FakeConnection:
    def __init__(self, permissions: tuple[int, ...]) -> None:
        self.fake_cursor = FakeCursor(permissions)
        self.closed = False

    def cursor(self) -> FakeCursor:
        return self.fake_cursor

    def close(self) -> None:
        self.closed = True


def configuration() -> DataConnection:
    return DataConnection(
        name="AdventureWorks",
        connector_kind="sqlserver",
        host="sqlserver",
        port=1433,
        database_name="AdventureWorks2022",
        username="bi_reader",
        secret_id=1,
        encrypt=True,
        trust_server_certificate=True,
    )


def test_read_only_connection_is_accepted(monkeypatch: MonkeyPatch) -> None:
    fake = FakeConnection((0, 0, 0, 0, 0, 0, 0))
    monkeypatch.setattr(connections.pyodbc, "connect", lambda *_args, **_kwargs: fake)

    result = connections.test_sqlserver_read_only(configuration(), "temporary", 8)

    assert result.ok
    assert fake.closed


def test_writer_connection_is_rejected(monkeypatch: MonkeyPatch) -> None:
    fake = FakeConnection((0, 1, 0, 0, 0, 0, 0))
    monkeypatch.setattr(connections.pyodbc, "connect", lambda *_args, **_kwargs: fake)

    result = connections.test_sqlserver_read_only(configuration(), "temporary", 8)

    assert not result.ok
    assert "permisos de escritura" in result.message


def test_connection_fields_reject_connection_string_injection() -> None:
    with pytest.raises(ValidationError):
        DataConnectionCreate(
            name="Fuente inválida",
            host="sqlserver;PWD=expuesta",
            database_name="AdventureWorks2022",
            username="bi_reader",
            password="temporary-secret",
        )


def test_password_is_quoted_as_single_odbc_value() -> None:
    connection_string = connections.build_connection_string(
        configuration(), "secret;Encrypt=no}suffix"
    )

    assert "PWD={secret;Encrypt=no}}suffix};" in connection_string
    assert "PWD=secret;Encrypt=no" not in connection_string


def test_parameter_range_is_enforced() -> None:
    assert router._validated_parameter_value("UI_PAGE_SIZE", "25") == "25"
    with pytest.raises(HTTPException) as captured:
        router._validated_parameter_value("UI_PAGE_SIZE", "500")
    assert captured.value.status_code == 422
