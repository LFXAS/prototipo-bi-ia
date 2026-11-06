from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.modules.analytics import router as analytics_router
from app.modules.copilot.models import BiProposal
from app.modules.copilot.service import canonical_hash
from app.modules.etl import router
from app.modules.etl.materializer import build_materialization_plan
from app.modules.etl.models import EtlExecution
from app.modules.etl.schemas import EtlExecutionCreate
from app.modules.etl.service import compile_kpi_recipes
from app.modules.metadata.models import MetadataSnapshot
from app.modules.parameters.models import DataConnection, Secret

pytestmark = pytest.mark.asyncio


def _fixture(rules: int | None = 5):
    now = datetime(2026, 11, 6, tzinfo=UTC)
    path = {
        "left_table": "Commerce.Lines",
        "right_table": "Commerce.Accounts",
        "left_columns": ["AccountRef"],
        "right_columns": ["ID"],
    }
    document = {
        "compilation_rules_version": rules,
        "summary": "Importe registrado por cliente",
        "grain": {"description": "Una fila por línea del documento."},
        "fact": {
            "name": "fact_ventas",
            "source_tables": ["Commerce.Lines"],
            "business_keys": ["ID"],
            "measures": [
                {
                    "name": "importe",
                    "source_columns": ["Amount"],
                    "aggregation": "sum",
                    "semantic_role": "sales_amount",
                }
            ],
        },
        "dimensions": [
            {
                "name": "dim_cliente",
                "source_tables": ["Commerce.Accounts"],
                "business_key": "ID",
                "attributes": ["Label"],
                "source_resolution": {
                    "selected_source": "Commerce.Accounts",
                    "business_key_reference": "Commerce.Accounts.ID",
                    "path": [path],
                },
            }
        ],
        "kpis": [
            {
                "code": "total_sales",
                "name": "Importe total",
                "formula": {"operation": "sum", "measure": "importe"},
                "unit": "moneda de origen",
            }
        ],
        "warnings": [],
    }
    if rules is None:
        del document["compilation_rules_version"]
    metadata = {
        "schemas": [
            {
                "name": "Commerce",
                "tables": [
                    {
                        "name": "Lines",
                        "columns": [
                            {"name": "ID", "data_type": "int", "primary_key": True},
                            {"name": "AccountRef", "data_type": "int"},
                            {"name": "Amount", "data_type": "numeric"},
                        ],
                        "foreign_keys": [
                            {
                                "columns": ["AccountRef"],
                                "referenced_schema": "Commerce",
                                "referenced_table": "Accounts",
                                "referenced_columns": ["ID"],
                            }
                        ],
                    },
                    {
                        "name": "Accounts",
                        "columns": [
                            {"name": "ID", "data_type": "int", "primary_key": True},
                            {"name": "Label", "data_type": "nvarchar"},
                        ],
                        "foreign_keys": [],
                    },
                ],
            }
        ]
    }
    proposal = SimpleNamespace(
        id=200,
        status="approved",
        metadata_snapshot_id=2,
        domain_code="ventas",
        business_goal="Comparar el importe registrado por cliente.",
        periodicity="month",
        provider_kind="test",
        model_id="test",
        created_at=now,
        reviewed_at=now,
        reviewed_by_label="Analista de prueba",
        review_comment="Contrato revisado.",
        proposal_document=document,
        validation_document={"valid": True},
        scope_document={},
        semantic_map_document={},
        prompt_version="sales-bi-v8",
    )
    snapshot = SimpleNamespace(
        id=2, data_connection_id=3, schema_document=metadata, content_hash=canonical_hash(metadata)
    )
    connection = SimpleNamespace(
        id=3,
        name="Fuente de prueba",
        database_name="CommerceDemo",
        is_active=True,
        last_test_status="ok",
        secret_id=4,
    )
    recipes, issues = compile_kpi_recipes(document)
    assert not issues
    execution = SimpleNamespace(
        id=21,
        proposal_id=200,
        metadata_snapshot_id=2,
        status="succeeded",
        domain_code="ventas",
        builder_version="sales-etl-v1",
        proposal_hash=canonical_hash(document),
        snapshot_hash=snapshot.content_hash,
        selection_document={"selected_kpi_codes": ["total_sales"]},
        plan_document={"kpi_recipes": recipes},
        validation_document={"materialization_passed": True},
        metrics_document={"reconciliation": {"passed": True}},
        created_by_label="Analista de prueba",
        created_at=now,
        started_at=now,
        finished_at=now,
    )
    return proposal, snapshot, connection, execution


def _result(value=None, items=()):
    result = Mock()
    result.scalar_one_or_none.return_value = value
    result.scalars.return_value = list(items)
    return result


def _session(proposal, snapshot, connection, execution):
    session = AsyncMock()
    session.add = Mock()
    objects = {
        BiProposal: proposal,
        MetadataSnapshot: snapshot,
        DataConnection: connection,
        EtlExecution: execution,
        Secret: SimpleNamespace(ciphertext=b"test-only-ciphertext"),
    }

    async def get(model, identity):
        return objects[model]

    session.get.side_effect = get
    session.execute.return_value = _result()
    return session


def _trust_other_preflight_checks(monkeypatch):
    # Keep the version gate independent of all other preflight outcomes. Physical
    # path validation itself is exercised with the real rules-5 fixture below.
    monkeypatch.setattr(router, "validate_proposal", Mock(return_value={"valid": True}))
    monkeypatch.setattr(
        router, "verify_proposal_evidence", Mock(return_value={"approval_safe": True})
    )
    monkeypatch.setattr(router, "assess_dimensional_readiness", Mock(return_value=([], [])))
    monkeypatch.setattr(router, "add_audit_event", AsyncMock())


@pytest.mark.parametrize("rules", [None, 1, 2, 3, 4])
async def test_legacy_candidate_is_read_only_without_withdrawing_approval(monkeypatch, rules):
    proposal, snapshot, connection, execution = _fixture(rules)
    before = deepcopy(vars(proposal))
    session = _session(proposal, snapshot, connection, execution)
    session.execute.return_value = _result(execution)
    _trust_other_preflight_checks(monkeypatch)

    candidate = await router._candidate(proposal, session)

    assert not candidate.eligible
    assert "versión derivada" in " ".join(candidate.blocking_reasons)
    assert candidate.latest_execution_id == execution.id
    assert vars(proposal) == before
    assert canonical_hash(proposal.proposal_document) == execution.proposal_hash
    session.commit.assert_not_awaited()
    session.add.assert_not_called()


@pytest.mark.parametrize("rules", [None, 1, 2, 3, 4])
async def test_legacy_preparation_is_rejected_before_creating_an_execution(monkeypatch, rules):
    proposal, snapshot, connection, execution = _fixture(rules)
    before = deepcopy(vars(proposal))
    session = _session(proposal, snapshot, connection, execution)
    session.execute.side_effect = [_result(proposal), _result()]
    _trust_other_preflight_checks(monkeypatch)
    payload = EtlExecutionCreate(
        proposal_id=proposal.id,
        selected_kpi_codes=["total_sales"],
        confirmation=True,
        analyst_comment="Revisé el contrato de esta prueba.",
    )

    with pytest.raises(HTTPException) as caught:
        await router.prepare_execution(payload, SimpleNamespace(id=1), session)

    assert caught.value.status_code == 422
    assert "versión derivada" in caught.value.detail
    assert vars(proposal) == before
    session.add.assert_not_called()
    session.flush.assert_not_awaited()
    session.commit.assert_not_awaited()
    router.add_audit_event.assert_not_awaited()


@pytest.mark.parametrize("rules", [None, 1, 2, 3, 4])
async def test_pending_legacy_execution_cannot_start_or_change_its_receipt(monkeypatch, rules):
    proposal, snapshot, connection, execution = _fixture(rules)
    execution.status = "prepared"
    execution.started_at = execution.finished_at = None
    before_proposal, before_execution = deepcopy(vars(proposal)), deepcopy(vars(execution))
    session = _session(proposal, snapshot, connection, execution)
    session.execute.side_effect = [_result(execution), _result(execution)]
    _trust_other_preflight_checks(monkeypatch)
    materialize = Mock(side_effect=AssertionError("Legacy ETL must never reach the materializer"))
    monkeypatch.setattr(router, "materialize_sales", materialize)

    with pytest.raises(HTTPException) as caught:
        await router.run_execution(execution.id, SimpleNamespace(id=1), session)

    assert caught.value.status_code == 422
    assert "versión derivada" in caught.value.detail
    assert vars(proposal) == before_proposal
    assert vars(execution) == before_execution
    materialize.assert_not_called()
    session.commit.assert_not_awaited()
    router.add_audit_event.assert_not_awaited()


async def test_current_approved_candidate_with_a_real_persisted_path_remains_eligible(monkeypatch):
    proposal, snapshot, connection, execution = _fixture()
    plan = build_materialization_plan(proposal.proposal_document, snapshot.schema_document)
    assert "t0.[AccountRef] = t1.[ID]" in plan.fact.query
    session = _session(proposal, snapshot, connection, execution)
    _trust_other_preflight_checks(monkeypatch)

    candidate = await router._candidate(proposal, session)

    assert candidate.eligible
    assert not candidate.blocking_reasons


async def test_current_approved_derivative_can_prepare_a_new_execution(monkeypatch):
    proposal, snapshot, connection, prior_execution = _fixture()
    before = deepcopy(vars(proposal))
    session = _session(proposal, snapshot, connection, prior_execution)
    session.execute.side_effect = [_result(proposal), _result(), _result(items=[])]
    _trust_other_preflight_checks(monkeypatch)
    payload = EtlExecutionCreate(
        proposal_id=proposal.id,
        selected_kpi_codes=["total_sales"],
        confirmation=True,
        analyst_comment="Derivada actual revisada con sus rutas exactas.",
    )
    actor = SimpleNamespace(id=1, full_name="Analista de prueba", email="analyst@example.test")

    result = await router.prepare_execution(payload, actor, session)

    assert result.status == "prepared"
    assert result.proposal_hash == canonical_hash(proposal.proposal_document)
    assert vars(proposal) == before
    session.add.assert_called_once_with(result)
    session.commit.assert_awaited_once()


async def test_current_prepared_derivative_can_reach_materialization(monkeypatch):
    proposal, snapshot, connection, execution = _fixture()
    execution.status = "prepared"
    execution.started_at = execution.finished_at = None
    session = _session(proposal, snapshot, connection, execution)
    session.execute.side_effect = [_result(execution), _result(execution)]
    _trust_other_preflight_checks(monkeypatch)
    monkeypatch.setattr(
        router, "_secret_cipher", SimpleNamespace(decrypt=Mock(return_value="test-only-password"))
    )
    materialize = Mock(return_value={"reconciliation": {"passed": True}, "kpis": []})
    monkeypatch.setattr(router, "materialize_sales", materialize)

    result = await router.run_execution(execution.id, SimpleNamespace(id=1), session)

    assert result.status == "succeeded"
    materialize.assert_called_once()
    assert materialize.call_args.args[1] is proposal.proposal_document
    assert result.started_at is not None and result.finished_at is not None
    assert session.commit.await_count == 2


@pytest.mark.parametrize("rules", [None, 1, 2, 3, 4])
async def test_legacy_execution_reads_keep_states_and_hashes_intact(monkeypatch, rules):
    proposal, snapshot, connection, execution = _fixture(rules)
    before_proposal, before_execution = deepcopy(vars(proposal)), deepcopy(vars(execution))
    session = _session(proposal, snapshot, connection, execution)
    session.scalar.return_value = 1
    session.execute.return_value = _result(items=[execution])
    monkeypatch.setattr(
        router, "_candidate", AsyncMock(side_effect=AssertionError("History must stay readable"))
    )

    single = await router.get_execution(execution.id, SimpleNamespace(id=1), session)
    history = await router.list_executions(SimpleNamespace(id=1), session, 10, 0, None)

    assert single is execution
    assert history.items[0].id == execution.id
    assert vars(proposal) == before_proposal
    assert vars(execution) == before_execution
    session.commit.assert_not_awaited()


@pytest.mark.parametrize("rules", [1, 4])
@pytest.mark.parametrize("report_format", ["pdf", "xlsx"])
async def test_published_legacy_dashboard_and_exports_remain_available(
    monkeypatch, rules, report_format
):
    proposal, snapshot, connection, execution = _fixture(rules)
    before_proposal, before_execution = deepcopy(vars(proposal)), deepcopy(vars(execution))
    session = _session(proposal, snapshot, connection, execution)
    session.execute.return_value = _result(execution)
    dashboard = SimpleNamespace(execution_id=execution.id, metric_code="total_sales")
    build = AsyncMock(return_value=dashboard)
    monkeypatch.setattr(analytics_router, "build_dashboard", build)
    monkeypatch.setattr(
        analytics_router, "user_permission_codes", lambda actor: {"analytics.dashboard.read"}
    )
    monkeypatch.setattr(analytics_router, "add_audit_event", AsyncMock())
    monkeypatch.setattr(analytics_router, "build_analytics_pdf", Mock(return_value=b"%PDF-test"))
    monkeypatch.setattr(analytics_router, "build_analytics_xlsx", Mock(return_value=b"xlsx-test"))

    loaded = await analytics_router._load_dashboard(
        session,
        connection_id=connection.id,
        execution_id=execution.id,
        metric_code="total_sales",
        year=None,
        territory=None,
    )
    exported = await analytics_router.export_analytics_report(
        report_format,
        "executive",
        connection.id,
        execution.id,
        "total_sales",
        None,
        None,
        SimpleNamespace(id=1),
        session,
    )

    assert loaded is dashboard
    assert exported.status_code == 200
    assert f".{report_format}" in exported.headers["Content-Disposition"]
    assert vars(proposal) == before_proposal
    assert vars(execution) == before_execution
    session.add.assert_not_called()
    # Exporting records an audit event, without changing the historical contract.
    session.commit.assert_awaited_once()
