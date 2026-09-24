from __future__ import annotations

from app.modules.metadata.introspection import _COLUMN_QUERY, normalize_metadata
from app.modules.metadata.router import _matching_tables
from app.modules.parameters.models import DataConnection


def configuration() -> DataConnection:
    return DataConnection(
        id=9,
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


COLUMNS = [
    ("Sales", "Customer", "CustomerID", 1, "int", 4, 10, 0, 0, 1),
    ("Sales", "SalesOrderHeader", "SalesOrderID", 1, "int", 4, 10, 0, 0, 1),
    ("Sales", "SalesOrderHeader", "CustomerID", 2, "int", 4, 10, 0, 1, 0),
]

FOREIGN_KEYS = [
    (
        "FK_SalesOrderHeader_Customer_CustomerID",
        "Sales",
        "SalesOrderHeader",
        1,
        "CustomerID",
        "Sales",
        "Customer",
        "CustomerID",
    )
]


def test_metadata_document_is_canonical_and_reproducible() -> None:
    first = normalize_metadata(configuration(), COLUMNS, FOREIGN_KEYS)
    second = normalize_metadata(configuration(), list(reversed(COLUMNS)), FOREIGN_KEYS)

    assert first.content_hash == second.content_hash
    assert first.schema_count == 1
    assert first.table_count == 2
    assert first.column_count == 3
    assert first.relationship_count == 1
    assert set(first.document) == {"contract_version", "source", "schemas"}
    assert "password" not in str(first.document).lower()
    assert "sqlserver" not in str(first.document["source"]["database"]).lower()


def test_introspection_uses_base_type_so_alias_typed_columns_are_not_lost() -> None:
    """AdventureWorks uses aliases such as dbo.Name that a reader cannot describe directly."""
    assert "columns.system_type_id" in _COLUMN_QUERY
    assert "types.user_type_id = types.system_type_id" in _COLUMN_QUERY


def test_foreign_key_keeps_valid_source_and_target_columns() -> None:
    result = normalize_metadata(configuration(), COLUMNS, FOREIGN_KEYS)
    tables = result.document["schemas"][0]["tables"]
    order = next(table for table in tables if table["name"] == "SalesOrderHeader")
    relation = order["foreign_keys"][0]

    assert relation["columns"] == ["CustomerID"]
    assert relation["referenced_schema"] == "Sales"
    assert relation["referenced_table"] == "Customer"
    assert relation["referenced_columns"] == ["CustomerID"]


def test_table_search_uses_snapshot_names_without_sql() -> None:
    result = normalize_metadata(configuration(), COLUMNS, FOREIGN_KEYS)

    by_table = _matching_tables(result.document, "order", None)
    by_column = _matching_tables(result.document, "customerid", "Sales")
    missing = _matching_tables(result.document, "drop table", None)

    assert [item["name"] for item in by_table] == ["SalesOrderHeader"]
    assert [item["name"] for item in by_column] == ["Customer", "SalesOrderHeader"]
    assert missing == []
