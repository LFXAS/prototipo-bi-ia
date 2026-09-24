from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.pagination import PageRead
from app.db.session import get_session
from app.modules.copilot.domains import (
    catalog_for_snapshot,
    default_needs_catalog_configuration,
    domain_profile,
    normalize_needs_catalog_configuration,
)
from app.modules.copilot.models import BiProposal, SemanticAdvice
from app.modules.copilot.schemas import (
    AnalysisCatalogConfiguration,
    AnalysisCatalogDomainRead,
    CopilotCatalogRead,
    CopilotReadiness,
    ProposalCreate,
    ProposalDecision,
    ProposalRead,
    ProposalReject,
    ProposalRevision,
    ProposalStatus,
    ProposalVerificationRead,
    ReadinessComponent,
    SemanticAdviceCreate,
    SemanticAdviceRead,
)
from app.modules.copilot.service import (
    CONTRACT_VERSION,
    PROMPT_VERSION,
    PROPOSAL_BLUEPRINT_SYSTEM_INSTRUCTION,
    SEMANTIC_ADVICE_SYSTEM_INSTRUCTION,
    SEMANTIC_RESPONSE_SCHEMA,
    SEMANTIC_SYSTEM_INSTRUCTION,
    apply_analyst_adjustments,
    canonical_hash,
    compact_metadata_blocks,
    derived_scope,
    expand_proposal_blueprint,
    proposal_blueprint_schema,
    proposal_payload,
    selected_semantic_candidates,
    semantic_advice_response_schema,
    validate_proposal,
    validated_semantic_candidates,
    verify_proposal_evidence,
)
from app.modules.metadata.models import MetadataSnapshot
from app.modules.parameters.models import DataConnection, LlmConfiguration, Parameter, Secret
from app.modules.parameters.providers import ProviderGenerationError, generate_json
from app.modules.parameters.secrets import SecretCipher, SecretDecryptionError
from app.modules.parameters.service import APPROVED_PARAMETERS
from app.modules.security.models import User
from app.modules.security.service import add_audit_event, require_permission

router = APIRouter(tags=["copilot"])
_secret_cipher = SecretCipher(settings.secrets_key_path)


async def _active_configuration(session: AsyncSession) -> LlmConfiguration | None:
    return (
        await session.execute(
            select(LlmConfiguration).where(LlmConfiguration.is_active.is_(True)).limit(1)
        )
    ).scalar_one_or_none()


async def _latest_snapshot(
    session: AsyncSession, connection_id: int | None = None
) -> MetadataSnapshot | None:
    statement = select(MetadataSnapshot)
    if connection_id is not None:
        statement = statement.where(MetadataSnapshot.data_connection_id == connection_id)
    return (
        await session.execute(statement.order_by(MetadataSnapshot.captured_at.desc()).limit(1))
    ).scalar_one_or_none()


async def _parameter(session: AsyncSession, key: str) -> int:
    value = await session.scalar(select(Parameter.value).where(Parameter.key == key))
    return int(value or APPROVED_PARAMETERS[key]["default_value"])


_ANALYSIS_CATALOG_KEYS = {"ventas": "COPILOT_SALES_NEEDS_CATALOG"}


async def _needs_catalog(session: AsyncSession, domain_code: str = "ventas") -> dict[str, object]:
    try:
        parameter_key = _ANALYSIS_CATALOG_KEYS[domain_code]
    except KeyError as exc:
        raise ValueError("El dominio solicitado no está habilitado.") from exc
    value = await session.scalar(select(Parameter.value).where(Parameter.key == parameter_key))
    if not value:
        return default_needs_catalog_configuration()
    try:
        return normalize_needs_catalog_configuration(json.loads(value))
    except (json.JSONDecodeError, ValueError):
        return default_needs_catalog_configuration()


async def _store_needs_catalog(
    session: AsyncSession, domain_code: str, configuration: dict[str, object]
) -> Parameter:
    try:
        parameter_key = _ANALYSIS_CATALOG_KEYS[domain_code]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dominio analítico no encontrado.") from exc
    parameter = (
        await session.execute(select(Parameter).where(Parameter.key == parameter_key))
    ).scalar_one_or_none()
    definition = APPROVED_PARAMETERS[parameter_key]
    serialized = json.dumps(configuration, ensure_ascii=False, separators=(",", ":"))
    if parameter is None:
        parameter = Parameter(
            key=parameter_key,
            value=serialized,
            is_active=True,
            **definition,
        )
        session.add(parameter)
    else:
        parameter.value = serialized
    await session.flush()
    return parameter


async def _readiness(session: AsyncSession) -> CopilotReadiness:
    connection = (
        await session.execute(select(DataConnection).where(DataConnection.is_active.is_(True)))
    ).scalar_one_or_none()
    snapshot = await _latest_snapshot(session, connection.id if connection else None)
    configuration = await _active_configuration(session)
    source_ok = connection is not None and connection.last_test_status == "ok"
    metadata_ok = (
        snapshot is not None
        and connection is not None
        and snapshot.data_connection_id == connection.id
    )
    llm_ok = configuration is not None and configuration.last_test_status == "ok"
    return CopilotReadiness(
        ready=source_ok and metadata_ok and llm_ok,
        source=ReadinessComponent(
            ready=source_ok,
            label="Fuente de ventas",
            detail=(
                f"{connection.name} está activa y probada."
                if connection is not None and connection.last_test_status == "ok"
                else "Falta activar y probar una fuente SQL Server."
            ),
            path="/conexiones",
        ),
        metadata=ReadinessComponent(
            ready=metadata_ok,
            label="Metadatos",
            detail=(
                f"Instantánea {snapshot.content_hash[:12]} disponible."
                if metadata_ok and snapshot
                else "Falta crear una instantánea de la fuente activa."
            ),
            path="/esquema",
        ),
        llm=ReadinessComponent(
            ready=llm_ok,
            label="Asistente de IA",
            detail=(
                f"{configuration.name} · {configuration.model_id}."
                if llm_ok and configuration
                else "Falta activar y probar una configuración LLM."
            ),
            path="/llm",
        ),
    )


@router.get("/copilot/readiness", response_model=CopilotReadiness)
async def get_readiness(
    _: User = Depends(require_permission("copilot.proposals.read")),
    session: AsyncSession = Depends(get_session),
) -> CopilotReadiness:
    return await _readiness(session)


@router.get("/copilot/catalog", response_model=CopilotCatalogRead)
async def get_catalog(
    metadata_snapshot_id: int = Query(gt=0),
    _: User = Depends(require_permission("copilot.proposals.read")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    connection = (
        await session.execute(select(DataConnection).where(DataConnection.is_active.is_(True)))
    ).scalar_one_or_none()
    snapshot = await session.get(MetadataSnapshot, metadata_snapshot_id)
    latest = await _latest_snapshot(session, connection.id if connection else None)
    if (
        connection is None
        or snapshot is None
        or latest is None
        or snapshot.id != latest.id
        or snapshot.data_connection_id != connection.id
    ):
        raise HTTPException(
            status_code=422,
            detail="El catálogo sólo puede calcularse con la instantánea vigente.",
        )
    return {
        "metadata_snapshot_id": snapshot.id,
        "domains": catalog_for_snapshot(snapshot.schema_document, await _needs_catalog(session)),
    }


@router.get(
    "/analysis-catalog/domains",
    response_model=list[AnalysisCatalogDomainRead],
)
async def list_analysis_catalog_domains(
    _: User = Depends(require_permission("copilot.catalog.read")),
) -> list[dict[str, object]]:
    return [
        {
            "code": profile.code,
            "label": profile.label,
            "description": profile.description,
            "enabled": profile.code in _ANALYSIS_CATALOG_KEYS,
            "implementation_status": "implemented",
        }
        for profile in (domain_profile(code) for code in _ANALYSIS_CATALOG_KEYS)
    ]


@router.get(
    "/analysis-catalog/domains/{domain_code}",
    response_model=AnalysisCatalogConfiguration,
)
async def get_analysis_catalog_domain(
    domain_code: str,
    _: User = Depends(require_permission("copilot.catalog.read")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    try:
        domain_profile(domain_code)
        return await _needs_catalog(session, domain_code)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put(
    "/analysis-catalog/domains/{domain_code}",
    response_model=AnalysisCatalogConfiguration,
)
async def update_analysis_catalog_domain(
    domain_code: str,
    payload: AnalysisCatalogConfiguration,
    actor: User = Depends(require_permission("copilot.catalog.write")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    if payload.domain_code != domain_code:
        raise HTTPException(
            status_code=422,
            detail="El dominio del catálogo no coincide con la ruta seleccionada.",
        )
    try:
        domain_profile(domain_code)
        normalized = normalize_needs_catalog_configuration(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    parameter = await _store_needs_catalog(session, domain_code, normalized)
    await add_audit_event(
        session,
        actor.id,
        "copilot.catalog.update",
        "analysis_catalog",
        domain_code,
        {
            "parameter_id": parameter.id,
            "question_count": len(cast(list[object], normalized["questions"])),
            "periodicity_count": len(cast(list[object], normalized["periodicities"])),
        },
    )
    await session.commit()
    return normalized


@router.post(
    "/analysis-catalog/domains/{domain_code}/reset",
    response_model=AnalysisCatalogConfiguration,
)
async def reset_analysis_catalog_domain(
    domain_code: str,
    actor: User = Depends(require_permission("copilot.catalog.write")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    try:
        domain_profile(domain_code)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    configuration = default_needs_catalog_configuration()
    parameter = await _store_needs_catalog(session, domain_code, configuration)
    await add_audit_event(
        session,
        actor.id,
        "copilot.catalog.reset",
        "analysis_catalog",
        domain_code,
        {"parameter_id": parameter.id},
    )
    await session.commit()
    return configuration


def _safe_business_request(
    payload: ProposalCreate, configuration: dict[str, object]
) -> dict[str, object]:
    profile = domain_profile(payload.domain_code)
    lowered = payload.business_goal.casefold()
    if re.search(
        r"\b(select|insert|update|delete|drop|alter|create table|exec(?:ute)?)\b", lowered
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Describa la necesidad en lenguaje de negocio, sin SQL ni instrucciones técnicas."
            ),
        )
    excluded = ("inventario", "compras", "nómina", "nomina", "contabilidad")
    if any(term in lowered for term in excluded) and "venta" not in lowered:
        raise HTTPException(
            status_code=422,
            detail="En este prototipo el asistente se limita al análisis de ventas.",
        )
    configured_questions = {
        str(item["code"]): item
        for item in cast(list[dict[str, object]], configuration["questions"])
    }
    configured_periodicities = {
        str(item["code"]): item
        for item in cast(list[dict[str, object]], configuration["periodicities"])
    }
    selected_questions = [configured_questions[code] for code in payload.business_questions]
    selected_periodicity = configured_periodicities[payload.periodicity]
    return {
        "domain": profile.code,
        "goal": payload.business_goal,
        "questions": [
            {
                "code": item["code"],
                "label": item["label"],
                "description": item["description"],
                "instruction": item["prompt_instruction"],
            }
            for item in selected_questions
        ],
        "requested_dimensions": [],
        "periodicity": {
            "code": selected_periodicity["code"],
            "label": selected_periodicity["label"],
            "description": selected_periodicity["description"],
        },
        "excluded_concepts": payload.excluded_concepts,
    }


async def _credential(configuration: LlmConfiguration, session: AsyncSession) -> str | None:
    if configuration.provider_kind == "ollama-local":
        return None
    secret = await session.get(Secret, configuration.secret_id) if configuration.secret_id else None
    if secret is None:
        return None
    try:
        return _secret_cipher.decrypt(secret.ciphertext)
    except (SecretDecryptionError, OSError):
        return None


@router.post("/copilot/proposals", response_model=ProposalRead, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    payload: ProposalCreate,
    actor: User = Depends(require_permission("copilot.proposals.generate")),
    session: AsyncSession = Depends(get_session),
) -> BiProposal:
    readiness = await _readiness(session)
    if not readiness.ready:
        raise HTTPException(
            status_code=422,
            detail=(
                "Complete la fuente, los metadatos y el proveedor LLM antes de iniciar el análisis."
            ),
        )
    snapshot = await session.get(MetadataSnapshot, payload.metadata_snapshot_id)
    connection = (
        await session.execute(select(DataConnection).where(DataConnection.is_active.is_(True)))
    ).scalar_one()
    latest = await _latest_snapshot(session, connection.id)
    if (
        snapshot is None
        or latest is None
        or snapshot.id != latest.id
        or snapshot.data_connection_id != connection.id
    ):
        raise HTTPException(
            status_code=422, detail="Seleccione la instantánea vigente de la fuente activa."
        )
    configuration = await _active_configuration(session)
    if configuration is None:
        raise HTTPException(status_code=422, detail="No existe una configuración LLM activa.")
    catalog_configuration = await _needs_catalog(session, payload.domain_code)
    available_catalog = catalog_for_snapshot(snapshot.schema_document, catalog_configuration)
    selected_domain = next(
        (item for item in available_catalog if item["code"] == payload.domain_code), None
    )
    domain_questions = cast(list[dict[str, object]], (selected_domain or {}).get("questions", []))
    domain_periodicities = cast(
        list[dict[str, object]], (selected_domain or {}).get("periodicities", [])
    )
    available_questions = {
        str(item["code"]) for item in domain_questions if bool(item["available"])
    }
    available_periodicities = {
        str(item["code"]) for item in domain_periodicities if bool(item["available"])
    }
    unavailable_questions = set(map(str, payload.business_questions)) - available_questions
    unavailable_periodicities = {payload.periodicity} - available_periodicities
    if unavailable_questions or unavailable_periodicities:
        unavailable = sorted(unavailable_questions | unavailable_periodicities)
        raise HTTPException(
            status_code=422,
            detail=(
                "La necesidad contiene opciones deshabilitadas o no respaldadas por los "
                f"metadatos actuales: {', '.join(unavailable)}. Actualice la selección."
            ),
        )
    request_document = _safe_business_request(payload, catalog_configuration)
    source_proposal = (
        await session.get(BiProposal, payload.source_proposal_id)
        if payload.source_proposal_id is not None
        else None
    )
    if payload.source_proposal_id is not None and (
        source_proposal is None
        or source_proposal.metadata_snapshot_id != snapshot.id
        or source_proposal.domain_code != payload.domain_code
    ):
        raise HTTPException(
            status_code=422,
            detail="La versión de origen no corresponde a la instantánea y dominio vigentes.",
        )
    input_hash = canonical_hash(
        {"snapshot_hash": snapshot.content_hash, "request": request_document}
    )
    record = BiProposal(
        source_proposal_id=payload.source_proposal_id,
        metadata_snapshot_id=snapshot.id,
        business_goal=payload.business_goal,
        business_questions=list(payload.business_questions),
        requested_dimensions=list(payload.requested_dimensions),
        periodicity=payload.periodicity,
        domain_code=payload.domain_code,
        scope_document={},
        semantic_map_document={},
        status="generating",
        input_hash=input_hash,
        prompt_version=PROMPT_VERSION,
        contract_version=CONTRACT_VERSION,
        provider_kind=configuration.provider_kind,
        model_id=configuration.model_id,
        proposal_document={},
        validation_document={"valid": False, "errors": 0, "warnings": 0, "issues": []},
        created_by_user_id=actor.id,
        created_by_label=f"{actor.full_name} <{actor.email}>",
    )
    session.add(record)
    await session.flush()
    credential = await _credential(configuration, session)
    timeout = await _parameter(session, "LLM_TIMEOUT_SECONDS")
    block_size = await _parameter(session, "METADATA_BLOCK_MAX_ITEMS")
    try:
        if source_proposal is not None and source_proposal.semantic_map_document.get("candidates"):
            semantic_map = deepcopy(source_proposal.semantic_map_document)
            raw_rejected = semantic_map.get("rejected_references", [])
            rejected = (
                [item for item in raw_rejected if isinstance(item, dict)]
                if isinstance(raw_rejected, list)
                else []
            )
            semantic_map["reused_from_proposal_id"] = source_proposal.id
        else:
            semantic_responses = [
                await generate_json(
                    configuration,
                    SEMANTIC_SYSTEM_INSTRUCTION,
                    block,
                    credential=credential,
                    timeout_seconds=timeout,
                    max_output_tokens=(
                        700
                        if configuration.provider_kind == "gemini"
                        else 1200
                        if configuration.provider_kind == "groq-cloud"
                        else 600
                    ),
                    response_schema=SEMANTIC_RESPONSE_SCHEMA,
                )
                for block in compact_metadata_blocks(
                    snapshot.schema_document, request_document, block_size
                )
            ]
            semantic_map, rejected = validated_semantic_candidates(
                semantic_responses, snapshot.schema_document
            )
        excluded = {item.casefold() for item in payload.excluded_concepts}
        raw_candidates = semantic_map.get("candidates", [])
        candidates = (
            [item for item in raw_candidates if isinstance(item, dict)]
            if isinstance(raw_candidates, list)
            else []
        )
        if source_proposal is not None or excluded:
            for candidate in candidates:
                concept = str(candidate.get("business_concept", "")).casefold()
                name = str(candidate.get("business_name_es", "")).casefold()
                candidate["selected"] = concept not in excluded and name not in excluded
                candidate["selection_source"] = "analyst"
        semantic_map["candidates"] = candidates
        semantic_map["excluded_by_analyst"] = payload.excluded_concepts
        semantic_map["excluded_by_system"] = [
            str(candidate.get("business_concept", ""))
            for candidate in candidates
            if not bool(candidate.get("selected", True))
            and candidate.get("selection_source") == "automatic"
        ]
        record.semantic_map_document = semantic_map
        scope = derived_scope(snapshot.schema_document, semantic_map)
        record.scope_document = scope
        if not selected_semantic_candidates(semantic_map) or not scope["tables"]:
            issues = [
                *rejected,
                {
                    "code": "semantic.empty",
                    "level": "error",
                    "path": "semantic_map",
                    "message": (
                        "No se identificó un alcance de ventas verificable. "
                        "Precise el objetivo y genere un nuevo intento."
                    ),
                },
            ]
            record.validation_document = {
                "valid": False,
                "errors": 1,
                "warnings": len(rejected),
                "issues": issues,
            }
            record.status = "validation_failed"
        else:
            blueprint = await generate_json(
                configuration,
                PROPOSAL_BLUEPRINT_SYSTEM_INSTRUCTION,
                proposal_payload(
                    snapshot.content_hash,
                    snapshot.connector_code,
                    request_document,
                    scope,
                    semantic_map,
                ),
                credential=credential,
                timeout_seconds=timeout,
                max_output_tokens=(
                    800
                    if configuration.provider_kind == "gemini"
                    else 2400
                    if configuration.provider_kind == "groq-cloud"
                    else 700
                ),
                response_schema=proposal_blueprint_schema(scope, semantic_map),
            )
            # The LLM proposes dimensions from verified metadata; the catalog never forces them.
            blueprint["requested_dimensions"] = []
            proposal = expand_proposal_blueprint(blueprint, scope, semantic_map)
            validation = validate_proposal(proposal, scope, snapshot.schema_document)
            record.proposal_document = proposal
            record.validation_document = validation
            record.status = "ready_for_review" if validation["valid"] else "validation_failed"
    except ProviderGenerationError as exc:
        record.status = "provider_failed"
        record.validation_document = {
            "valid": False,
            "errors": 1,
            "warnings": 0,
            "issues": [
                {"code": "provider.failed", "level": "error", "path": "$", "message": str(exc)}
            ],
        }
    action = f"copilot.proposal.{record.status}"
    await add_audit_event(
        session,
        actor.id,
        action,
        "bi_proposal",
        str(record.id),
        {
            "input_hash": input_hash[:12],
            "provider": configuration.provider_kind,
            "model": configuration.model_id,
            "source_proposal_id": payload.source_proposal_id,
        },
    )
    await session.commit()
    await session.refresh(record)
    return record


@router.get("/copilot/proposals", response_model=PageRead[ProposalRead])
async def list_proposals(
    _: User = Depends(require_permission("copilot.proposals.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    statuses: list[ProposalStatus] = Query(default_factory=list, alias="status"),
    domain_code: str | None = Query(default=None, min_length=1, max_length=40),
) -> PageRead[ProposalRead]:
    total_statement = select(func.count()).select_from(BiProposal)
    items_statement = select(BiProposal)
    if statuses:
        total_statement = total_statement.where(BiProposal.status.in_(statuses))
        items_statement = items_statement.where(BiProposal.status.in_(statuses))
    if domain_code:
        try:
            domain_profile(domain_code)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        total_statement = total_statement.where(BiProposal.domain_code == domain_code)
        items_statement = items_statement.where(BiProposal.domain_code == domain_code)
    total = (await session.scalar(total_statement)) or 0
    items = (
        await session.execute(
            items_statement.order_by(BiProposal.created_at.desc(), BiProposal.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars()
    return PageRead(items=list(items), total=total, limit=limit, offset=offset)


async def _proposal_or_404(proposal_id: int, session: AsyncSession) -> BiProposal:
    proposal = await session.get(BiProposal, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Propuesta BI no encontrada.")
    return proposal


@router.get("/copilot/proposals/{proposal_id}", response_model=ProposalRead)
async def get_proposal(
    proposal_id: int,
    _: User = Depends(require_permission("copilot.proposals.read")),
    session: AsyncSession = Depends(get_session),
) -> BiProposal:
    return await _proposal_or_404(proposal_id, session)


def _semantic_candidate_or_404(proposal: BiProposal, concept_code: str) -> dict[str, object]:
    candidates = proposal.semantic_map_document.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = []
    candidate = next(
        (
            item
            for item in candidates
            if isinstance(item, dict)
            and str(item.get("business_concept", "")).casefold() == concept_code.casefold()
        ),
        None,
    )
    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="El concepto no pertenece al expediente semántico de esta propuesta.",
        )
    return cast(dict[str, object], candidate)


@router.get(
    "/copilot/proposals/{proposal_id}/semantic-advice",
    response_model=list[SemanticAdviceRead],
)
async def list_semantic_advice(
    proposal_id: int,
    concept_code: str = Query(min_length=1, max_length=80),
    _: User = Depends(require_permission("copilot.proposals.read")),
    session: AsyncSession = Depends(get_session),
) -> list[SemanticAdvice]:
    proposal = await _proposal_or_404(proposal_id, session)
    _semantic_candidate_or_404(proposal, concept_code)
    records = (
        await session.execute(
            select(SemanticAdvice)
            .where(
                SemanticAdvice.proposal_id == proposal.id,
                SemanticAdvice.concept_code == concept_code,
            )
            .order_by(SemanticAdvice.created_at, SemanticAdvice.id)
            .limit(30)
        )
    ).scalars()
    return list(records)


@router.post(
    "/copilot/proposals/{proposal_id}/semantic-advice",
    response_model=SemanticAdviceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_semantic_advice(
    proposal_id: int,
    payload: SemanticAdviceCreate,
    actor: User = Depends(require_permission("copilot.proposals.generate")),
    session: AsyncSession = Depends(get_session),
) -> SemanticAdvice:
    proposal = await _proposal_or_404(proposal_id, session)
    candidate = _semantic_candidate_or_404(proposal, payload.concept_code)
    if re.search(
        r"\b(select|insert|update|delete|drop|alter|create table|exec(?:ute)?)\b",
        payload.question.casefold(),
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "El copiloto explica decisiones mediante evidencia verificada; no genera "
                "ni ejecuta SQL libre. Formule la pregunta en términos de negocio."
            ),
        )
    configuration = await _active_configuration(session)
    if configuration is None:
        raise HTTPException(status_code=422, detail="No existe una configuración LLM activa.")
    credential = await _credential(configuration, session)
    timeout = await _parameter(session, "LLM_TIMEOUT_SECONDS")
    previous = list(
        (
            await session.execute(
                select(SemanticAdvice)
                .where(
                    SemanticAdvice.proposal_id == proposal.id,
                    SemanticAdvice.concept_code == payload.concept_code,
                )
                .order_by(SemanticAdvice.created_at.desc(), SemanticAdvice.id.desc())
                .limit(6)
            )
        ).scalars()
    )
    raw_technical_refs = candidate.get("technical_refs", [])
    technical_refs = (
        [str(item) for item in raw_technical_refs if isinstance(item, str)]
        if isinstance(raw_technical_refs, list)
        else []
    )
    request_document = {
        "task": "explain_semantic_decision",
        "language": "es",
        "business_goal": proposal.business_goal,
        "business_questions": proposal.business_questions,
        "concept": candidate,
        "analyst_question": payload.question,
        "previous_turns": [
            {
                "question": item.question,
                "conclusion": str(item.response_document.get("conclusion", "")),
                "answer_es": str(item.response_document.get("answer_es", ""))[:500],
            }
            for item in reversed(previous)
        ],
        "constraints": {
            "no_sql": True,
            "no_rows": True,
            "no_credentials": True,
            "technical_references_must_match": technical_refs,
            "advice_does_not_change_selection": True,
        },
    }
    try:
        raw_response = await generate_json(
            configuration,
            SEMANTIC_ADVICE_SYSTEM_INSTRUCTION,
            request_document,
            credential=credential,
            timeout_seconds=timeout,
            max_output_tokens=(
                900
                if configuration.provider_kind == "gemini"
                else 1800
                if configuration.provider_kind == "groq-cloud"
                else 900
            ),
            response_schema=semantic_advice_response_schema(technical_refs),
        )
    except ProviderGenerationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    allowed_refs = set(technical_refs)
    raw_evidence = raw_response.get("evidence", [])
    evidence = [
        {
            "technical_ref": str(item.get("technical_ref", "")),
            "detail_es": str(item.get("detail_es", ""))[:240],
        }
        for item in raw_evidence
        if isinstance(item, dict)
        and str(item.get("technical_ref", "")) in allowed_refs
        and str(item.get("detail_es", "")).strip()
    ]
    if not evidence and technical_refs:
        evidence = [
            {
                "technical_ref": technical_refs[0],
                "detail_es": "Referencia técnica comprobada en la instantánea vigente.",
            }
        ]
    conclusion = str(raw_response.get("conclusion", "define_business"))
    if conclusion not in {"include", "exclude", "define_business"}:
        conclusion = "define_business"
    confidence = str(raw_response.get("confidence", "low"))
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"
    response_document: dict[str, object] = {
        "conclusion": conclusion,
        "answer_es": str(raw_response.get("answer_es", ""))[:800],
        "evidence": evidence,
        "risk_es": str(raw_response.get("risk_es", ""))[:400],
        "include_consequence_es": str(raw_response.get("include_consequence_es", ""))[:400],
        "exclude_consequence_es": str(raw_response.get("exclude_consequence_es", ""))[:400],
        "recommended_action_es": str(raw_response.get("recommended_action_es", ""))[:400],
        "confidence": confidence,
        "selection_changed": False,
    }
    record = SemanticAdvice(
        proposal_id=proposal.id,
        concept_code=payload.concept_code,
        question=payload.question,
        response_document=response_document,
        provider_kind=configuration.provider_kind,
        model_id=configuration.model_id,
        created_by_user_id=actor.id,
        created_by_label=f"{actor.full_name} <{actor.email}>",
    )
    session.add(record)
    await session.flush()
    await add_audit_event(
        session,
        actor.id,
        "copilot.semantic_advice.create",
        "semantic_advice",
        str(record.id),
        {
            "proposal_id": proposal.id,
            "concept_code": payload.concept_code,
            "conclusion": conclusion,
            "provider": configuration.provider_kind,
            "model": configuration.model_id,
        },
    )
    await session.commit()
    await session.refresh(record)
    return record


@router.post(
    "/copilot/proposals/{proposal_id}/revisions",
    response_model=ProposalRead,
    status_code=status.HTTP_201_CREATED,
)
async def revise_proposal(
    proposal_id: int,
    payload: ProposalRevision,
    actor: User = Depends(require_permission("copilot.proposals.generate")),
    session: AsyncSession = Depends(get_session),
) -> BiProposal:
    source = await _proposal_or_404(proposal_id, session)
    if source.status not in {
        "ready_for_review",
        "approved",
        "invalidated",
        "validation_failed",
    }:
        raise HTTPException(
            status_code=409,
            detail="Esta versión no contiene una propuesta que pueda personalizarse.",
        )
    snapshot = await session.get(MetadataSnapshot, source.metadata_snapshot_id)
    if snapshot is None:
        raise HTTPException(
            status_code=409,
            detail="La instantánea asociada ya no está disponible.",
        )
    source_blueprint = source.proposal_document.get("ai_decisions")
    if not isinstance(source_blueprint, dict):
        raise HTTPException(
            status_code=409,
            detail="La propuesta no conserva decisiones que puedan personalizarse.",
        )
    adjustments = payload.model_dump()
    try:
        revised_blueprint = apply_analyst_adjustments(source_blueprint, adjustments)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    semantic_map = deepcopy(source.semantic_map_document)
    semantic_map["analyst_revision"] = {
        "source_proposal_id": source.id,
        "comment": payload.comment,
        "dimension_names": payload.dimension_names,
        "measure_names": payload.measure_names,
        "kpi_codes": payload.kpi_codes,
    }
    proposal_document = expand_proposal_blueprint(
        revised_blueprint,
        source.scope_document,
        semantic_map,
    )
    validation = validate_proposal(
        proposal_document,
        source.scope_document,
        snapshot.schema_document,
    )
    revision_hash = canonical_hash(
        {
            "source_proposal_id": source.id,
            "source_input_hash": source.input_hash,
            "adjustments": adjustments,
        }
    )
    record = BiProposal(
        source_proposal_id=source.id,
        metadata_snapshot_id=source.metadata_snapshot_id,
        business_goal=source.business_goal,
        business_questions=list(source.business_questions),
        requested_dimensions=list(source.requested_dimensions),
        periodicity=source.periodicity,
        domain_code=source.domain_code,
        scope_document=deepcopy(source.scope_document),
        semantic_map_document=semantic_map,
        status="ready_for_review" if validation["valid"] else "validation_failed",
        input_hash=revision_hash,
        prompt_version=source.prompt_version,
        contract_version=source.contract_version,
        provider_kind=source.provider_kind,
        model_id=source.model_id,
        proposal_document=proposal_document,
        validation_document=validation,
        created_by_user_id=actor.id,
        created_by_label=f"{actor.full_name} <{actor.email}>",
    )
    session.add(record)
    await session.flush()
    await add_audit_event(
        session,
        actor.id,
        "copilot.proposal.revise",
        "bi_proposal",
        str(record.id),
        {
            "source_proposal_id": source.id,
            "input_hash": revision_hash[:12],
            "status": record.status,
        },
    )
    await session.commit()
    await session.refresh(record)
    return record


@router.post(
    "/copilot/proposals/{proposal_id}/verify",
    response_model=ProposalVerificationRead,
)
async def verify_proposal(
    proposal_id: int,
    actor: User = Depends(require_permission("copilot.proposals.read")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    proposal = await _proposal_or_404(proposal_id, session)
    if not proposal.proposal_document:
        raise HTTPException(
            status_code=409,
            detail="La versión seleccionada no contiene una propuesta verificable.",
        )
    snapshot = await session.get(MetadataSnapshot, proposal.metadata_snapshot_id)
    if snapshot is None:
        raise HTTPException(
            status_code=409, detail="La instantánea asociada ya no está disponible."
        )
    evidence = verify_proposal_evidence(
        proposal.proposal_document,
        proposal.validation_document,
        proposal.scope_document,
        proposal.semantic_map_document,
        snapshot.schema_document,
        snapshot.content_hash,
        proposal.prompt_version,
    )
    invalidated = proposal.status == "approved" and not bool(evidence["approval_safe"])
    if invalidated:
        proposal.status = "invalidated"
        proposal.review_comment = (
            "Aprobación retirada automáticamente: la versión no supera las reglas "
            "determinísticas vigentes."
        )
        proposal.reviewed_by_user_id = actor.id
        proposal.reviewed_by_label = f"{actor.full_name} <{actor.email}>"
        proposal.reviewed_at = datetime.now(UTC)
    await add_audit_event(
        session,
        actor.id,
        "copilot.proposal.verify",
        "bi_proposal",
        str(proposal.id),
        {
            "verified": evidence["verified"],
            "approval_invalidated": invalidated,
            "snapshot_hash": snapshot.content_hash[:12],
            "proposal_hash": str(evidence["proposal_hash"])[:12],
        },
    )
    await session.commit()
    return {"proposal_id": proposal.id, "approval_invalidated": invalidated, **evidence}


@router.post(
    "/copilot/proposals/{proposal_id}/restore-approval",
    response_model=ProposalRead,
)
async def restore_proposal_approval(
    proposal_id: int,
    payload: ProposalDecision,
    actor: User = Depends(require_permission("copilot.proposals.review")),
    session: AsyncSession = Depends(get_session),
) -> BiProposal:
    proposal = await _proposal_or_404(proposal_id, session)
    if proposal.status != "invalidated":
        raise HTTPException(
            status_code=409,
            detail="Sólo puede restaurar una propuesta cuya aprobación fue retirada.",
        )
    snapshot = await session.get(MetadataSnapshot, proposal.metadata_snapshot_id)
    if snapshot is None:
        raise HTTPException(
            status_code=409, detail="La instantánea asociada ya no está disponible."
        )
    evidence = verify_proposal_evidence(
        proposal.proposal_document,
        proposal.validation_document,
        proposal.scope_document,
        proposal.semantic_map_document,
        snapshot.schema_document,
        snapshot.content_hash,
        proposal.prompt_version,
    )
    if not bool(evidence["approval_safe"]):
        raise HTTPException(
            status_code=422,
            detail=(
                "La aprobación no puede restaurarse porque la propuesta presenta "
                "errores bloqueantes vigentes."
            ),
        )
    warning_count = int(evidence["validation_warnings"])
    if warning_count > 0 and not payload.warnings_confirmed:
        raise HTTPException(
            status_code=422,
            detail="Confirme que revisó las advertencias antes de restaurar la aprobación.",
        )
    proposal.status = "approved"
    proposal.review_comment = payload.comment or (
        "Aprobación restaurada después de comprobar que la diferencia corresponde "
        "únicamente a compatibilidad entre versiones del motor."
    )
    proposal.warnings_confirmed = payload.warnings_confirmed
    proposal.reviewed_by_user_id = actor.id
    proposal.reviewed_by_label = f"{actor.full_name} <{actor.email}>"
    proposal.reviewed_at = datetime.now(UTC)
    await add_audit_event(
        session,
        actor.id,
        "copilot.proposal.approval_restored",
        "bi_proposal",
        str(proposal.id),
        {
            "reason": proposal.review_comment,
            "compatibility_warning": evidence["compatibility_warning"],
            "proposal_prompt_version": proposal.prompt_version,
            "current_prompt_version": PROMPT_VERSION,
        },
    )
    await session.commit()
    await session.refresh(proposal)
    return proposal


@router.post("/copilot/proposals/{proposal_id}/invalidate", response_model=ProposalRead)
async def invalidate_proposal(
    proposal_id: int,
    payload: ProposalReject,
    actor: User = Depends(require_permission("copilot.proposals.review")),
    session: AsyncSession = Depends(get_session),
) -> BiProposal:
    proposal = await _proposal_or_404(proposal_id, session)
    if proposal.status == "invalidated":
        return proposal
    if proposal.status != "approved":
        raise HTTPException(
            status_code=409,
            detail="Sólo puede retirar la aprobación de una propuesta aprobada.",
        )
    proposal.status = "invalidated"
    proposal.review_comment = payload.comment
    proposal.warnings_confirmed = False
    proposal.reviewed_by_user_id = actor.id
    proposal.reviewed_by_label = f"{actor.full_name} <{actor.email}>"
    proposal.reviewed_at = datetime.now(UTC)
    await add_audit_event(
        session,
        actor.id,
        "copilot.proposal.invalidate",
        "bi_proposal",
        str(proposal.id),
        {"reason": payload.comment},
    )
    await session.commit()
    await session.refresh(proposal)
    return proposal


@router.post("/copilot/proposals/{proposal_id}/discard", response_model=ProposalRead)
async def discard_proposal(
    proposal_id: int,
    payload: ProposalReject,
    actor: User = Depends(require_permission("copilot.proposals.generate")),
    session: AsyncSession = Depends(get_session),
) -> BiProposal:
    proposal = await _proposal_or_404(proposal_id, session)
    if proposal.status == "discarded":
        return proposal
    if proposal.status == "approved":
        raise HTTPException(
            status_code=409,
            detail="Retire primero la aprobación antes de descartar esta versión.",
        )
    proposal.status = "discarded"
    proposal.review_comment = payload.comment
    proposal.reviewed_by_user_id = actor.id
    proposal.reviewed_by_label = f"{actor.full_name} <{actor.email}>"
    proposal.reviewed_at = datetime.now(UTC)
    await add_audit_event(
        session,
        actor.id,
        "copilot.proposal.discard",
        "bi_proposal",
        str(proposal.id),
        {"reason": payload.comment},
    )
    await session.commit()
    await session.refresh(proposal)
    return proposal


@router.post("/copilot/proposals/{proposal_id}/approve", response_model=ProposalRead)
async def approve_proposal(
    proposal_id: int,
    payload: ProposalDecision,
    actor: User = Depends(require_permission("copilot.proposals.review")),
    session: AsyncSession = Depends(get_session),
) -> BiProposal:
    proposal = await _proposal_or_404(proposal_id, session)
    if proposal.status == "approved":
        return proposal
    if proposal.status != "ready_for_review":
        raise HTTPException(
            status_code=409,
            detail="Sólo una propuesta válida y pendiente de revisión puede aprobarse.",
        )
    snapshot = await session.get(MetadataSnapshot, proposal.metadata_snapshot_id)
    if snapshot is None:
        raise HTTPException(
            status_code=409, detail="La instantánea asociada ya no está disponible."
        )
    current_validation = validate_proposal(
        proposal.proposal_document,
        proposal.scope_document,
        snapshot.schema_document,
    )
    proposal.validation_document = current_validation
    if not current_validation["valid"]:
        proposal.status = "validation_failed"
        await add_audit_event(
            session,
            actor.id,
            "copilot.proposal.approval_blocked",
            "bi_proposal",
            str(proposal.id),
            {"errors": current_validation["errors"]},
        )
        await session.commit()
        raise HTTPException(
            status_code=422,
            detail=(
                "La propuesta contiene inconsistencias semánticas. "
                "Personalícela o genere una nueva versión antes de aprobar."
            ),
        )
    warning_count = proposal.validation_document.get("warnings", 0)
    if isinstance(warning_count, int) and warning_count > 0 and not payload.warnings_confirmed:
        raise HTTPException(
            status_code=422, detail="Confirme que revisó las advertencias antes de aprobar."
        )
    proposal.status = "approved"
    proposal.review_comment = payload.comment
    proposal.warnings_confirmed = payload.warnings_confirmed
    proposal.reviewed_by_user_id = actor.id
    proposal.reviewed_by_label = f"{actor.full_name} <{actor.email}>"
    proposal.reviewed_at = datetime.now(UTC)
    await add_audit_event(
        session,
        actor.id,
        "copilot.proposal.approve",
        "bi_proposal",
        str(proposal.id),
        {"input_hash": proposal.input_hash[:12]},
    )
    await session.commit()
    await session.refresh(proposal)
    return proposal


@router.post("/copilot/proposals/{proposal_id}/reject", response_model=ProposalRead)
async def reject_proposal(
    proposal_id: int,
    payload: ProposalReject,
    actor: User = Depends(require_permission("copilot.proposals.review")),
    session: AsyncSession = Depends(get_session),
) -> BiProposal:
    proposal = await _proposal_or_404(proposal_id, session)
    if proposal.status == "rejected":
        return proposal
    if proposal.status != "ready_for_review":
        raise HTTPException(
            status_code=409, detail="Sólo una propuesta pendiente de revisión puede rechazarse."
        )
    proposal.status = "rejected"
    proposal.review_comment = payload.comment
    proposal.reviewed_by_user_id = actor.id
    proposal.reviewed_by_label = f"{actor.full_name} <{actor.email}>"
    proposal.reviewed_at = datetime.now(UTC)
    await add_audit_event(
        session,
        actor.id,
        "copilot.proposal.reject",
        "bi_proposal",
        str(proposal.id),
        {"input_hash": proposal.input_hash[:12]},
    )
    await session.commit()
    await session.refresh(proposal)
    return proposal
