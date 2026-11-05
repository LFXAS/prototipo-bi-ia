from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.modules.copilot import router
from app.modules.copilot.schemas import ProposalDecision, ProposalRevision
from app.modules.copilot.service import COMPILATION_RULES_VERSION, PROMPT_VERSION

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    ("prompt_version", "rules_version", "draft_status"),
    [
        ("sales-bi-v6", None, "ready_for_review"),
        ("sales-bi-v5", None, "ready_for_review"),
        (PROMPT_VERSION, None, "ready_for_review"),
        ("sales-bi-v6", 2, "ready_for_review"),
        ("sales-bi-v6", None, "validation_failed"),
    ],
)
async def test_legacy_draft_requires_a_current_revision_before_approval(
    monkeypatch, prompt_version, rules_version, draft_status
) -> None:
    document = {} if rules_version is None else {"compilation_rules_version": rules_version}
    proposal = SimpleNamespace(
        id=119,
        status=draft_status,
        prompt_version=prompt_version,
        proposal_document=document,
        validation_document={"valid": True},
    )
    before = deepcopy(vars(proposal))
    monkeypatch.setattr(router, "_proposal_or_404", AsyncMock(return_value=proposal))
    audit = AsyncMock()
    monkeypatch.setattr(router, "add_audit_event", audit)
    session = AsyncMock()

    with pytest.raises(HTTPException) as caught:
        await router.approve_proposal(119, ProposalDecision(), SimpleNamespace(id=1), session)

    assert caught.value.status_code == 409
    assert "Personalícela" in caught.value.detail
    assert "no la corrige automáticamente" in caught.value.detail
    assert vars(proposal) == before
    session.get.assert_not_awaited()
    session.commit.assert_not_awaited()
    audit.assert_not_awaited()


async def test_already_approved_legacy_contract_is_returned_without_mutation(monkeypatch) -> None:
    proposal = SimpleNamespace(
        id=117, status="approved", prompt_version="sales-bi-v6", proposal_document={}
    )
    before = deepcopy(vars(proposal))
    monkeypatch.setattr(router, "_proposal_or_404", AsyncMock(return_value=proposal))
    session = AsyncMock()

    result = await router.approve_proposal(117, ProposalDecision(), SimpleNamespace(id=1), session)

    assert result is proposal
    assert vars(proposal) == before
    session.get.assert_not_awaited()
    session.commit.assert_not_awaited()


async def test_current_contract_can_be_approved_after_current_validation(monkeypatch) -> None:
    proposal = SimpleNamespace(
        id=121,
        status="ready_for_review",
        prompt_version=PROMPT_VERSION,
        proposal_document={"compilation_rules_version": COMPILATION_RULES_VERSION},
        metadata_snapshot_id=2,
        scope_document={},
        input_hash="a" * 64,
    )
    monkeypatch.setattr(router, "_proposal_or_404", AsyncMock(return_value=proposal))
    monkeypatch.setattr(
        router, "validate_proposal", Mock(return_value={"valid": True, "warnings": 0})
    )
    audit = AsyncMock()
    monkeypatch.setattr(router, "add_audit_event", audit)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(schema_document={})
    actor = SimpleNamespace(id=1, full_name="Persona revisora", email="reviewer@example.test")

    result = await router.approve_proposal(121, ProposalDecision(), actor, session)

    assert result.status == "approved"
    session.commit.assert_awaited_once()
    assert audit.await_args.args[2] == "copilot.proposal.approve"


@pytest.mark.parametrize("source_status", ["ready_for_review", "approved"])
async def test_personalizing_a_legacy_contract_creates_a_current_child(
    monkeypatch, source_status
) -> None:
    source = SimpleNamespace(
        id=119,
        status=source_status,
        metadata_snapshot_id=2,
        proposal_document={"ai_decisions": {"summary": "Diseño anterior"}},
        semantic_map_document={},
        scope_document={},
        input_hash="a" * 64,
        business_goal="Analizar ventas registradas",
        business_questions=[],
        requested_dimensions=[],
        periodicity="month",
        domain_code="ventas",
        prompt_version="sales-bi-v6",
        contract_version=1,
        provider_kind="test",
        model_id="test",
    )
    before = deepcopy(vars(source))
    monkeypatch.setattr(router, "_proposal_or_404", AsyncMock(return_value=source))
    monkeypatch.setattr(router, "apply_analyst_adjustments", Mock(return_value={}))
    monkeypatch.setattr(
        router,
        "expand_proposal_blueprint",
        Mock(return_value={"compilation_rules_version": COMPILATION_RULES_VERSION}),
    )
    monkeypatch.setattr(
        router, "validate_proposal", Mock(return_value={"valid": True, "warnings": 0})
    )
    monkeypatch.setattr(router, "add_audit_event", AsyncMock())
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(schema_document={})
    session.add = Mock()
    payload = ProposalRevision(
        summary="Ventas por producto",
        grain_description="Una fila por línea de venta",
        dimension_names=["dim_producto"],
        measure_names=["importe_venta"],
        kpi_codes=["ventas_totales"],
        comment="Revisión con reglas vigentes",
    )
    actor = SimpleNamespace(id=1, full_name="Persona analista", email="analyst@example.test")

    child = await router.revise_proposal(119, payload, actor, session)

    assert child.source_proposal_id == 119
    assert child.prompt_version == PROMPT_VERSION
    assert child.proposal_document["compilation_rules_version"] == COMPILATION_RULES_VERSION
    assert vars(source) == before
