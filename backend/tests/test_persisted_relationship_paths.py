from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.modules.analytics.service import AnalyticsUnavailableError, dimension_provenance
from app.modules.etl.materializer import build_materialization_plan, persisted_relationship_paths


def relationship_fixture(spanish=False):
    schema = "Comercio" if spanish else "Commerce"
    names = (
        ["Lineas", "Documentos", "Cuentas", "Lugares", "Regiones"]
        if spanish
        else ["Lines", "Documents", "Accounts", "Places", "Areas"]
    )
    line, document, account, place, area = [f"{schema}.{name}" for name in names]

    def column(name, primary=False, data_type="int"):
        return {"name": name, "data_type": data_type, "primary_key": primary}

    def relation(left, target, right="ID"):
        return {
            "columns": [left],
            "referenced_schema": schema,
            "referenced_table": target.split(".", 1)[1],
            "referenced_columns": [right],
        }

    tables = [
        {
            "name": names[0],
            "columns": [column("ID", True), column("DocumentRef"), column("Amount")],
            "foreign_keys": [relation("DocumentRef", document)],
        },
        {
            "name": names[1],
            "columns": [column("ID", True), column("BuyerRef"), column("BillingRef")],
            # The first metadata FK deliberately represents the other business role.
            "foreign_keys": [relation("BillingRef", account), relation("BuyerRef", account)],
        },
        {
            "name": names[2],
            "columns": [
                column("ID", True),
                column("Label", data_type="nvarchar"),
                column("DeliveryRef"),
                column("PostalRef"),
                column("Rate", data_type="numeric"),
            ],
            "foreign_keys": [relation("PostalRef", place), relation("DeliveryRef", place)],
        },
        {
            "name": names[3],
            "columns": [column("ID", True), column("AreaRef")],
            "foreign_keys": [relation("AreaRef", area)],
        },
        {
            "name": names[4],
            "columns": [column("ID", True), column("Label", data_type="nvarchar")],
            "foreign_keys": [],
        },
    ]

    def step(left, right, column):
        return {
            "left_table": left,
            "right_table": right,
            "left_columns": [column],
            "right_columns": ["ID"],
        }

    buyer_path = [step(line, document, "DocumentRef"), step(document, account, "BuyerRef")]
    territory_path = [
        *deepcopy(buyer_path),
        step(account, place, "DeliveryRef"),
        step(place, area, "AreaRef"),
    ]

    def dimension(name, source, path):
        return {
            "name": name,
            "source_tables": [source],
            "business_key": "ID",
            "attributes": ["Label"],
            "source_resolution": {
                "status": "preserved",
                "selected_source": source,
                "proposed_source": source,
                "business_key_reference": f"{source}.ID",
                "path": path,
            },
        }

    proposal = {
        "compilation_rules_version": 5,
        "fact": {
            "name": "fact_ventas",
            "source_tables": [line],
            "business_keys": ["ID"],
            "measures": [{"name": "importe", "source_columns": ["Amount"], "aggregation": "sum"}],
        },
        "dimensions": [
            dimension("dim_cliente", account, buyer_path),
            dimension("dim_territorio", area, territory_path),
        ],
    }
    metadata = {"schemas": [{"name": schema, "tables": tables}]}
    return proposal, metadata


@pytest.mark.parametrize("spanish", [False, True])
def test_rules5_materializer_uses_exact_reviewed_roles_not_the_first_metadata_fk(spanish):
    proposal, metadata = relationship_fixture(spanish)

    plan = build_materialization_plan(proposal, metadata)

    assert "t1.[BuyerRef] = t2.[ID]" in plan.fact.query
    assert "t2.[DeliveryRef] = t3.[ID]" in plan.fact.query
    assert "[BillingRef]" not in plan.fact.query
    assert "[PostalRef]" not in plan.fact.query


@pytest.mark.parametrize("rules", [1, 2, 3, 4])
def test_legacy_materializer_keeps_the_original_first_fk_resolver(rules):
    proposal, metadata = relationship_fixture()
    proposal["compilation_rules_version"] = rules

    plan = build_materialization_plan(proposal, metadata)

    assert "t1.[BillingRef] = t2.[ID]" in plan.fact.query
    assert "t2.[PostalRef] = t3.[ID]" in plan.fact.query
    assert "[BuyerRef]" not in plan.fact.query
    assert "[DeliveryRef]" not in plan.fact.query


def test_rules5_missing_persisted_path_does_not_reopen_bfs(monkeypatch):
    from app.modules.etl import materializer

    proposal, metadata = relationship_fixture()
    del proposal["dimensions"][0]["source_resolution"]
    monkeypatch.setattr(
        materializer,
        "_shortest_path",
        lambda *args: pytest.fail("Rules 5 must not call the legacy BFS resolver"),
    )

    with pytest.raises(ValueError, match="persistida"):
        build_materialization_plan(proposal, metadata)


@pytest.mark.parametrize(
    "field,value", [("left_columns", ["Amount"]), ("right_columns", ["Label"])]
)
def test_rules5_tampered_persisted_fk_is_rejected(field, value):
    proposal, metadata = relationship_fixture()
    proposal["dimensions"][0]["source_resolution"]["path"][1][field] = value

    with pytest.raises(ValueError, match="FK dirigida"):
        build_materialization_plan(proposal, metadata)


def test_rules5_parallel_prefixes_for_one_table_are_rejected_without_role_aliases():
    proposal, metadata = relationship_fixture()
    proposal["dimensions"][1]["source_resolution"]["path"][1]["left_columns"] = ["BillingRef"]

    with pytest.raises(ValueError, match="rutas incompatibles"):
        build_materialization_plan(proposal, metadata)


def test_rules5_incomplete_target_identity_is_not_grain_preserving():
    proposal, metadata = relationship_fixture()
    metadata["schemas"][0]["tables"][1]["columns"].append(
        {"name": "TenantID", "data_type": "int", "primary_key": True}
    )

    with pytest.raises(ValueError, match="clave primaria completa"):
        build_materialization_plan(proposal, metadata)


def test_rules5_dimension_cannot_replace_its_verified_identity_with_an_attribute():
    proposal, metadata = relationship_fixture()
    dimension = proposal["dimensions"][0]
    dimension["business_key"] = "Label"
    dimension["source_resolution"]["business_key_reference"] = "Commerce.Accounts.Label"

    with pytest.raises(ValueError, match="clave primaria simple"):
        build_materialization_plan(proposal, metadata)


def test_rules5_reverse_relation_cannot_multiply_a_header_fact():
    proposal, metadata = relationship_fixture()
    proposal["fact"]["source_tables"] = ["Commerce.Documents"]
    proposal["fact"]["measures"] = []
    proposal["dimensions"] = [
        {
            "name": "dim_producto",
            "source_tables": ["Commerce.Lines"],
            "business_key": "ID",
            "attributes": [],
            "source_resolution": {
                "selected_source": "Commerce.Lines",
                "business_key_reference": "Commerce.Lines.ID",
                "path": [
                    {
                        "left_table": "Commerce.Documents",
                        "right_table": "Commerce.Lines",
                        "left_columns": ["ID"],
                        "right_columns": ["DocumentRef"],
                    }
                ],
            },
        }
    ]

    with pytest.raises(ValueError, match="FK dirigida"):
        build_materialization_plan(proposal, metadata)


def test_rules5_external_measure_requires_a_unique_safe_path():
    proposal, metadata = relationship_fixture()
    proposal["dimensions"] = []
    proposal["fact"]["measures"] = [
        {
            "name": "costo",
            "source_columns": ["Amount", "Commerce.Accounts.Rate"],
            "aggregation": "sum",
            "calculation": {
                "operation": "multiply",
                "inputs": ["Amount", "Commerce.Accounts.Rate"],
            },
        }
    ]

    with pytest.raises(ValueError, match="única ruta"):
        build_materialization_plan(proposal, metadata)


def test_rules5_external_measure_can_reuse_a_verified_dimensional_prefix():
    proposal, metadata = relationship_fixture()
    proposal["fact"]["measures"] = [
        {
            "name": "costo",
            "source_columns": ["Amount", "Commerce.Accounts.Rate"],
            "aggregation": "sum",
            "calculation": {
                "operation": "multiply",
                "inputs": ["Amount", "Commerce.Accounts.Rate"],
            },
        }
    ]

    plan = build_materialization_plan(proposal, metadata)

    assert "CAST(t2.[Rate] AS decimal(38, 10))" in plan.fact.query
    assert "[BillingRef]" not in plan.fact.query


def test_rules5_controlled_relation_resolves_an_external_measure_without_free_bfs():
    proposal, metadata = relationship_fixture()
    chosen = deepcopy(proposal["dimensions"][0]["source_resolution"]["path"])
    proposal["ai_decisions"] = {"controlled_relations": chosen}
    proposal["dimensions"] = []
    proposal["fact"]["measures"] = [
        {"name": "tasa", "source_columns": ["Commerce.Accounts.Rate"], "aggregation": "sum"}
    ]

    plan = build_materialization_plan(proposal, metadata)

    assert "t1.[BuyerRef] = t2.[ID]" in plan.fact.query
    assert "t2.[Rate]" in plan.fact.query
    assert "[BillingRef]" not in plan.fact.query


def test_rules5_provenance_uses_the_same_exact_path_as_the_materializer():
    proposal, metadata = relationship_fixture()
    execution = SimpleNamespace(id=20, started_at=None, finished_at=None)
    version = SimpleNamespace(id=126, proposal_document=proposal)
    snapshot = SimpleNamespace(schema_document=metadata)

    provenance = dimension_provenance(execution, version, snapshot)
    paths = persisted_relationship_paths(proposal, metadata)
    plan = build_materialization_plan(proposal, metadata)

    territory = provenance["dimensions"][1]
    assert territory["relationship_path"] == proposal["dimensions"][1]["source_resolution"]["path"]
    assert territory["relationship_path"][1]["left_columns"] == ["BuyerRef"]
    assert territory["relationship_path"][2]["left_columns"] == ["DeliveryRef"]
    assert paths["Commerce.Areas"][-1][0:2] == ("Commerce.Places", "Commerce.Areas")
    assert "[DeliveryRef]" in plan.fact.query


def test_rules5_invalid_provenance_does_not_report_a_different_bfs_path():
    proposal, metadata = relationship_fixture()
    del proposal["dimensions"][0]["source_resolution"]

    with pytest.raises(AnalyticsUnavailableError, match="evidencia dimensional"):
        dimension_provenance(
            SimpleNamespace(id=20, started_at=None, finished_at=None),
            SimpleNamespace(id=126, proposal_document=proposal),
            SimpleNamespace(schema_document=metadata),
        )
