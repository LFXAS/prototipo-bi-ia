from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.pagination import PageRead
from app.db.session import get_session
from app.modules.copilot.models import BiProposal
from app.modules.copilot.service import validate_proposal, verify_proposal_evidence
from app.modules.etl.materializer import (
    apply_spanish_labels,
    discover_spanish_label_candidates,
    enrich_currency_metrics,
    materialize_sales,
)
from app.modules.etl.models import EtlExecution
from app.modules.etl.schemas import (
    EtlExecutionCreate,
    EtlExecutionRead,
    EtlProposalCandidateRead,
    EtlProposalCatalogRead,
    SpanishInterpretationDecision,
)
from app.modules.etl.service import (
    BUILDER_VERSION,
    assess_dimensional_readiness,
    compile_kpi_recipes,
    compile_transformation_plan,
    proposal_overview,
)
from app.modules.metadata.models import MetadataSnapshot
from app.modules.parameters.models import DataConnection, LlmConfiguration, Secret
from app.modules.parameters.providers import ProviderGenerationError, generate_json
from app.modules.parameters.secrets import SecretCipher, SecretDecryptionError
from app.modules.security.models import User
from app.modules.security.service import add_audit_event, require_permission

router = APIRouter(tags=["etl"])
_secret_cipher = SecretCipher(settings.secrets_key_path)
_NON_REPEATABLE_EXECUTION_STATUSES = ("prepared", "running", "succeeded", "validation_warning")

_LOCALIZATION_SYSTEM_INSTRUCTION = (
    "Eres un intérprete semántico de BI. Recibirás únicamente categorías no sensibles de "
    "baja cardinalidad. Para cada valor detecta si ya está en español: si lo está, repítelo "
    "sin cambios; si está en inglés, produce una etiqueta breve y fiel en español. No "
    "inventes significado, no cambies códigos y devuelve sólo JSON con groups. Cada grupo "
    "debe repetir dimension y target_column; cada mapping debe incluir original, label_es, "
    "language (es, en o unknown) y changed."
)
_LOCALIZATION_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["groups"],
    "properties": {
        "groups": {
            "type": "array",
            "maxItems": 8,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["dimension", "target_column", "mappings"],
                "properties": {
                    "dimension": {"type": "string"},
                    "target_column": {"type": "string"},
                    "mappings": {
                        "type": "array",
                        "maxItems": 50,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["original", "label_es", "language", "changed"],
                            "properties": {
                                "original": {"type": "string"},
                                "label_es": {"type": "string"},
                                "language": {"type": "string", "enum": ["es", "en", "unknown"]},
                                "changed": {"type": "boolean"},
                            },
                        },
                    },
                },
            },
        }
    },
}


def _applied_semantic_document(
    stored: dict[str, object],
    applied: list[dict[str, object]],
    *,
    reviewed_by: str,
    reviewed_at: str,
    analyst_comment: str,
) -> dict[str, object]:
    """Return a new JSON value so the ORM can persist the nested state change."""
    return {
        **stored,
        "status": "applied",
        "mappings": applied,
        "reviewed_by": reviewed_by,
        "reviewed_at": reviewed_at,
        "analyst_comment": analyst_comment,
        "message": (
            "Las etiquetas españolas revisadas fueron publicadas sin reemplazar los "
            "valores originales."
        ),
    }


def _execution_kpi_codes(execution: EtlExecution) -> list[str]:
    raw = execution.selection_document.get("selected_kpi_codes", [])
    return sorted(str(code) for code in raw) if isinstance(raw, list) else []


def _same_execution_contract(execution: EtlExecution, selected_kpi_codes: list[str]) -> bool:
    return _execution_kpi_codes(execution) == sorted(selected_kpi_codes)


async def _localize_categories(
    candidates: list[dict[str, object]], session: AsyncSession
) -> tuple[list[dict[str, object]], str, str]:
    configuration = (
        await session.execute(select(LlmConfiguration).where(LlmConfiguration.is_active.is_(True)))
    ).scalar_one_or_none()
    if configuration is None:
        raise ProviderGenerationError("No existe un proveedor activo para interpretar categorías.")
    credential: str | None = None
    if configuration.provider_kind != "ollama-local":
        secret = (
            await session.get(Secret, configuration.secret_id)
            if configuration.secret_id is not None
            else None
        )
        if secret is None:
            raise ProviderGenerationError("La configuración activa no tiene credencial.")
        credential = _secret_cipher.decrypt(secret.ciphertext)
    response = await generate_json(
        configuration,
        _LOCALIZATION_SYSTEM_INSTRUCTION,
        {"groups": candidates, "rules": {"preserve_original": True, "language": "es"}},
        credential,
        timeout_seconds=60,
        max_output_tokens=2048,
        # Gemini 3 can reject this small schema before generation. JSON mode plus the
        # whitelist below remains bounded; Groq GPT-OSS supports strict schema decoding.
        response_schema=(
            _LOCALIZATION_SCHEMA if configuration.provider_kind == "groq-cloud" else None
        ),
    )
    allowed: dict[tuple[str, str], set[str]] = {}
    for item in candidates:
        raw_values = item.get("values", [])
        values = raw_values if isinstance(raw_values, list) else []
        allowed[(str(item.get("dimension")), str(item.get("target_column")))] = {
            str(value) for value in values
        }
    validated: list[dict[str, object]] = []
    for group in response.get("groups", []):
        if not isinstance(group, dict):
            continue
        key = (str(group.get("dimension")), str(group.get("target_column")))
        if key not in allowed:
            continue
        mappings: list[dict[str, object]] = []
        for raw_mapping in group.get("mappings", []):
            if not isinstance(raw_mapping, dict):
                continue
            original = str(raw_mapping.get("original", raw_mapping.get("source", "")))
            label_es = str(raw_mapping.get("label_es", raw_mapping.get("target", "")))
            if original not in allowed[key] or not 0 < len(label_es) <= 100:
                continue
            language = str(raw_mapping.get("language", "unknown"))
            if language not in {"es", "en", "unknown"}:
                language = "unknown"
            mappings.append(
                {
                    "original": original,
                    "label_es": label_es,
                    "language": language,
                    "changed": bool(
                        raw_mapping.get("changed", original.casefold() != label_es.casefold())
                    ),
                }
            )
        validated.append({"dimension": key[0], "target_column": key[1], "mappings": mappings})
    return validated, configuration.provider_kind, configuration.model_id


async def _candidate(proposal: BiProposal, session: AsyncSession) -> EtlProposalCandidateRead:
    blockers: list[str] = []
    snapshot = await session.get(MetadataSnapshot, proposal.metadata_snapshot_id)
    connection = (
        await session.get(DataConnection, snapshot.data_connection_id)
        if snapshot is not None
        else None
    )
    recipes, recipe_issues = compile_kpi_recipes(proposal.proposal_document)
    blockers.extend(recipe_issues)
    if proposal.status != "approved":
        blockers.append("La propuesta no conserva una aprobación humana vigente.")
    if proposal.domain_code != "ventas":
        blockers.append("El constructor disponible sólo implementa el perfil de ventas.")
    if snapshot is None:
        blockers.append("La instantánea de metadatos asociada ya no está disponible.")
    if connection is None or not connection.is_active or connection.last_test_status != "ok":
        blockers.append("La fuente asociada debe estar activa y validada en modo de sólo lectura.")
    if snapshot is not None:
        current = validate_proposal(
            proposal.proposal_document, proposal.scope_document, snapshot.schema_document
        )
        if not bool(current.get("valid")):
            blockers.append("La revalidación actual detectó inconsistencias en el contrato BI.")
        evidence = verify_proposal_evidence(
            proposal.proposal_document,
            proposal.validation_document,
            proposal.scope_document,
            proposal.semantic_map_document,
            snapshot.schema_document,
            snapshot.content_hash,
            proposal.prompt_version,
        )
        if not bool(evidence.get("approval_safe")):
            blockers.append("La evidencia estructural vigente no permite ejecutar esta propuesta.")
        readiness_blockers, readiness_warnings = assess_dimensional_readiness(
            proposal.proposal_document, snapshot.schema_document
        )
        blockers.extend(readiness_blockers)
    else:
        readiness_warnings = []
    overview = proposal_overview(proposal.proposal_document)
    proposal_hash = str(overview["proposal_hash"])
    latest_execution = (
        await session.execute(
            select(EtlExecution)
            .where(
                EtlExecution.proposal_id == proposal.id,
                EtlExecution.proposal_hash == proposal_hash,
                EtlExecution.status.in_(_NON_REPEATABLE_EXECUTION_STATUSES),
            )
            .order_by(EtlExecution.created_at.desc(), EtlExecution.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    dimensions = overview["dimensions"] if isinstance(overview["dimensions"], list) else []
    measures = overview["measures"] if isinstance(overview["measures"], list) else []
    warnings = overview["warnings"] if isinstance(overview["warnings"], list) else []
    warnings = [*warnings, *readiness_warnings]
    return EtlProposalCandidateRead(
        proposal_id=proposal.id,
        metadata_snapshot_id=proposal.metadata_snapshot_id,
        business_goal=proposal.business_goal,
        periodicity=proposal.periodicity,
        provider_kind=proposal.provider_kind,
        model_id=proposal.model_id,
        created_at=proposal.created_at,
        reviewed_at=proposal.reviewed_at,
        reviewed_by_label=proposal.reviewed_by_label,
        review_comment=proposal.review_comment,
        proposal_hash=proposal_hash,
        snapshot_hash=snapshot.content_hash if snapshot is not None else "",
        summary=str(overview["summary"]),
        grain=str(overview["grain"]),
        fact_name=str(overview["fact_name"]),
        dimensions=[str(item) for item in dimensions],
        measures=[str(item) for item in measures],
        kpi_count=len(recipes),
        kpi_recipes=recipes,
        transformation_plan=compile_transformation_plan(proposal.proposal_document),
        warnings=[str(item) for item in warnings],
        eligible=not blockers,
        blocking_reasons=list(dict.fromkeys(blockers)),
        latest_execution_id=latest_execution.id if latest_execution is not None else None,
        latest_execution_status=latest_execution.status if latest_execution is not None else None,
        latest_execution_at=latest_execution.created_at if latest_execution is not None else None,
        latest_execution_kpi_codes=(
            _execution_kpi_codes(latest_execution) if latest_execution is not None else []
        ),
    )


@router.get("/etl/proposals", response_model=EtlProposalCatalogRead)
async def list_eligible_proposals(
    _: User = Depends(require_permission("etl.executions.read")),
    session: AsyncSession = Depends(get_session),
) -> EtlProposalCatalogRead:
    proposals = list(
        (
            await session.execute(
                select(BiProposal)
                .where(BiProposal.status == "approved")
                .order_by(BiProposal.reviewed_at.desc(), BiProposal.id.desc())
            )
        ).scalars()
    )
    candidates = [await _candidate(proposal, session) for proposal in proposals]
    eligible = [item for item in candidates if item.eligible]
    blocked = [item for item in candidates if not item.eligible]
    recommended_id = (
        eligible[0].proposal_id if eligible and eligible[0].latest_execution_id is None else None
    )
    for item in eligible:
        item.recommended = item.proposal_id == recommended_id
    return EtlProposalCatalogRead(
        items=eligible,
        blocked_items=blocked,
        recommended_proposal_id=recommended_id,
        guidance=[
            "Revise la necesidad, granularidad, medidas y KPI antes de seleccionar.",
            "Compare propuestas cuando más de una represente la misma necesidad.",
            (
                "Una ejecución idéntica ya preparada o materializada se abre desde su "
                "expediente; no se repite silenciosamente."
            ),
        ],
    )


@router.post(
    "/etl/executions", response_model=EtlExecutionRead, status_code=status.HTTP_201_CREATED
)
async def prepare_execution(
    payload: EtlExecutionCreate,
    actor: User = Depends(require_permission("etl.executions.write")),
    session: AsyncSession = Depends(get_session),
) -> EtlExecution:
    if not payload.confirmation:
        raise HTTPException(
            status_code=422,
            detail="Confirme que revisó la propuesta, transformaciones y KPI antes de continuar.",
        )
    proposal = (
        await session.execute(
            select(BiProposal).where(BiProposal.id == payload.proposal_id).with_for_update()
        )
    ).scalar_one_or_none()
    if proposal is None:
        raise HTTPException(status_code=404, detail="Propuesta aprobada no encontrada.")
    candidate = await _candidate(proposal, session)
    if not candidate.eligible:
        raise HTTPException(
            status_code=422,
            detail="La propuesta perdió compatibilidad: " + " ".join(candidate.blocking_reasons),
        )
    available = {str(item["code"]): item for item in candidate.kpi_recipes}
    unknown = [code for code in payload.selected_kpi_codes if code not in available]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail="Los KPI seleccionados ya no están disponibles: " + ", ".join(unknown),
        )
    selected = [available[code] for code in payload.selected_kpi_codes]
    prior_executions = list(
        (
            await session.execute(
                select(EtlExecution)
                .where(
                    EtlExecution.proposal_id == proposal.id,
                    EtlExecution.proposal_hash == candidate.proposal_hash,
                    EtlExecution.status.in_(_NON_REPEATABLE_EXECUTION_STATUSES),
                )
                .order_by(EtlExecution.created_at.desc(), EtlExecution.id.desc())
            )
        ).scalars()
    )
    duplicate = next(
        (
            item
            for item in prior_executions
            if _same_execution_contract(item, payload.selected_kpi_codes)
        ),
        None,
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Este contrato ya corresponde a la ejecución #{duplicate.id} "
                f"({duplicate.status}). Abra ese expediente; no es necesario volver a "
                "ejecutar el ETL."
            ),
        )
    execution = EtlExecution(
        proposal_id=proposal.id,
        metadata_snapshot_id=proposal.metadata_snapshot_id,
        status="prepared",
        domain_code=proposal.domain_code,
        builder_version=BUILDER_VERSION,
        proposal_hash=candidate.proposal_hash,
        snapshot_hash=candidate.snapshot_hash,
        selection_document={
            "confirmed": True,
            "confirmed_at": datetime.now(UTC).isoformat(),
            "analyst_comment": payload.analyst_comment,
            "selected_kpi_codes": payload.selected_kpi_codes,
        },
        plan_document={
            "overview": {
                "summary": candidate.summary,
                "grain": candidate.grain,
                "fact": candidate.fact_name,
                "dimensions": candidate.dimensions,
                "measures": candidate.measures,
            },
            "transformations": candidate.transformation_plan,
            "kpi_recipes": selected,
        },
        validation_document={
            "preflight_passed": True,
            "blocking_reasons": [],
            "warnings": candidate.warnings,
            "message": "Contrato, fuente, transformaciones y KPI preparados para materialización.",
        },
        metrics_document={},
        created_by_user_id=actor.id,
        created_by_label=f"{actor.full_name} <{actor.email}>",
    )
    session.add(execution)
    await session.flush()
    await add_audit_event(
        session,
        actor.id,
        "etl.execution.prepare",
        "etl_execution",
        str(execution.id),
        {
            "proposal_id": proposal.id,
            "builder_version": BUILDER_VERSION,
            "selected_kpis": payload.selected_kpi_codes,
        },
    )
    await session.commit()
    await session.refresh(execution)
    return execution


@router.get("/etl/executions", response_model=PageRead[EtlExecutionRead])
async def list_executions(
    _: User = Depends(require_permission("etl.executions.read")),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageRead[EtlExecutionRead]:
    total = (await session.scalar(select(func.count()).select_from(EtlExecution))) or 0
    items = list(
        (
            await session.execute(
                select(EtlExecution)
                .order_by(EtlExecution.created_at.desc(), EtlExecution.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).scalars()
    )
    return PageRead(items=items, total=total, limit=limit, offset=offset)


@router.get("/etl/executions/{execution_id}", response_model=EtlExecutionRead)
async def get_execution(
    execution_id: int,
    _: User = Depends(require_permission("etl.executions.read")),
    session: AsyncSession = Depends(get_session),
) -> EtlExecution:
    execution = await session.get(EtlExecution, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Ejecución ETL no encontrada.")
    return execution


@router.post(
    "/etl/executions/{execution_id}/verify-currency",
    response_model=EtlExecutionRead,
)
async def verify_execution_currency(
    execution_id: int,
    actor: User = Depends(require_permission("etl.executions.write")),
    session: AsyncSession = Depends(get_session),
) -> EtlExecution:
    execution = (
        await session.execute(
            select(EtlExecution).where(EtlExecution.id == execution_id).with_for_update()
        )
    ).scalar_one_or_none()
    if execution is None:
        raise HTTPException(status_code=404, detail="Ejecución ETL no encontrada.")
    context = execution.metrics_document.get("currency_context", {})
    if isinstance(context, dict) and context.get("status") == "verified":
        return execution
    if execution.status not in {"succeeded", "validation_warning"}:
        raise HTTPException(
            status_code=409,
            detail=(
                "La divisa sólo puede comprobarse después de una carga conciliada. "
                "Resuelva primero la materialización."
            ),
        )
    proposal = await session.get(BiProposal, execution.proposal_id)
    snapshot = await session.get(MetadataSnapshot, execution.metadata_snapshot_id)
    if proposal is None or snapshot is None:
        raise HTTPException(status_code=422, detail="El contrato de origen ya no está disponible.")
    connection = await session.get(DataConnection, snapshot.data_connection_id)
    secret = await session.get(Secret, connection.secret_id) if connection is not None else None
    if connection is None or secret is None:
        raise HTTPException(
            status_code=422, detail="La credencial de la fuente no está disponible."
        )
    try:
        source_password = _secret_cipher.decrypt(secret.ciphertext)
    except (SecretDecryptionError, OSError) as exc:
        raise HTTPException(
            status_code=422, detail="La credencial de la fuente no pudo descifrarse."
        ) from exc
    execution.metrics_document = await asyncio.to_thread(
        enrich_currency_metrics,
        dict(execution.metrics_document),
        proposal.proposal_document,
        snapshot.schema_document,
        connection,
        source_password,
    )
    resolved = execution.metrics_document.get("currency_context", {})
    await add_audit_event(
        session,
        actor.id,
        "etl.execution.verify_currency",
        "etl_execution",
        str(execution.id),
        {
            "status": resolved.get("status") if isinstance(resolved, dict) else "unresolved",
            "currency_code": (
                resolved.get("currency_code") if isinstance(resolved, dict) else None
            ),
        },
    )
    await session.commit()
    await session.refresh(execution)
    return execution


@router.post("/etl/executions/{execution_id}/run", response_model=EtlExecutionRead)
async def run_execution(
    execution_id: int,
    actor: User = Depends(require_permission("etl.executions.write")),
    session: AsyncSession = Depends(get_session),
) -> EtlExecution:
    execution = (
        await session.execute(
            select(EtlExecution).where(EtlExecution.id == execution_id).with_for_update()
        )
    ).scalar_one_or_none()
    if execution is None:
        raise HTTPException(status_code=404, detail="Ejecución ETL no encontrada.")
    if execution.status != "prepared":
        raise HTTPException(
            status_code=409,
            detail=(
                "Esta ejecución ya fue iniciada. Abra su expediente para revisar el resultado "
                "o prepare una ejecución nueva."
            ),
        )
    proposal = await session.get(BiProposal, execution.proposal_id)
    snapshot = await session.get(MetadataSnapshot, execution.metadata_snapshot_id)
    if proposal is None or snapshot is None:
        raise HTTPException(status_code=422, detail="El contrato de origen ya no está disponible.")
    candidate = await _candidate(proposal, session)
    if not candidate.eligible:
        raise HTTPException(
            status_code=422,
            detail="La ejecución fue bloqueada: " + " ".join(candidate.blocking_reasons),
        )
    connection = await session.get(DataConnection, snapshot.data_connection_id)
    secret = await session.get(Secret, connection.secret_id) if connection is not None else None
    if connection is None or secret is None:
        raise HTTPException(
            status_code=422, detail="La credencial de la fuente no está disponible."
        )
    try:
        source_password = _secret_cipher.decrypt(secret.ciphertext)
    except (SecretDecryptionError, OSError) as exc:
        raise HTTPException(
            status_code=422, detail="La credencial de la fuente no pudo descifrarse."
        ) from exc
    selected_recipes = execution.plan_document.get("kpi_recipes", [])
    if not isinstance(selected_recipes, list):
        raise HTTPException(status_code=422, detail="El expediente de KPI no es válido.")
    execution.status = "running"
    execution.started_at = datetime.now(UTC)
    execution.validation_document = {
        **execution.validation_document,
        "message": "Extracción, transformación y carga en curso.",
    }
    await session.commit()
    try:
        metrics = await asyncio.to_thread(
            materialize_sales,
            execution.id,
            proposal.proposal_document,
            snapshot.schema_document,
            connection,
            source_password,
            selected_recipes,
        )
        localization_warning = False
        raw_candidates = metrics.pop("_localization_candidates", [])
        candidates = [item for item in raw_candidates if isinstance(item, dict)]
        if candidates:
            try:
                mappings, provider_kind, model_id = await _localize_categories(candidates, session)
                metrics["semantic_interpretation"] = {
                    "policy": "preserve-original-add-spanish-label",
                    "status": "review_required",
                    "provider_kind": provider_kind,
                    "model_id": model_id,
                    "mappings": mappings,
                    "message": (
                        "La IA preparó etiquetas españolas. Revise, corrija o excluya cada "
                        "mapeo antes de publicarlo; los originales permanecen intactos."
                    ),
                }
                localization_warning = True
            except Exception as exc:  # noqa: BLE001 - optional localization cannot undo valid ETL
                localization_warning = True
                metrics["semantic_interpretation"] = {
                    "policy": "preserve-original-add-spanish-label",
                    "status": "pending",
                    "mappings": [],
                    "failure_code": type(exc).__name__,
                    "failure_detail": (
                        str(exc)
                        if isinstance(exc, ProviderGenerationError)
                        else "La respuesta no cumplió el contrato de interpretación."
                    ),
                    "resolution": (
                        "Pruebe y active un proveedor disponible; después use Reintentar "
                        "interpretación. No es necesario repetir el ETL."
                    ),
                    "message": (
                        "Los datos numéricos se conciliaron, pero el proveedor no pudo "
                        "preparar las etiquetas españolas. Los valores originales se conservan."
                    ),
                }
        reconciliation = metrics.get("reconciliation", {})
        passed = bool(reconciliation.get("passed")) if isinstance(reconciliation, dict) else False
        execution.status = (
            "succeeded" if passed and not localization_warning else "validation_warning"
        )
        execution.metrics_document = metrics
        execution.validation_document = {
            "preflight_passed": True,
            "materialization_passed": True,
            "reconciliation_passed": passed,
            "message": (
                "El datamart fue materializado y conciliado correctamente."
                if passed and not localization_warning
                else (
                    "El datamart se concilió, pero la interpretación española quedó pendiente."
                    if passed
                    else "El datamart fue cargado, pero existen diferencias que deben revisarse."
                )
            ),
        }
    except Exception as exc:  # noqa: BLE001 - boundary converts driver failures safely
        execution.status = "failed"
        execution.metrics_document = {"error_code": type(exc).__name__}
        execution.validation_document = {
            "preflight_passed": True,
            "materialization_passed": False,
            "reconciliation_passed": False,
            "message": (
                "La materialización falló y la transacción fue revertida. Revise la fuente, "
                "el contrato y los registros del servidor antes de preparar un nuevo intento."
            ),
        }
    execution.finished_at = datetime.now(UTC)
    await add_audit_event(
        session,
        actor.id,
        "etl.execution.run",
        "etl_execution",
        str(execution.id),
        {"proposal_id": proposal.id, "status": execution.status},
    )
    await session.commit()
    await session.refresh(execution)
    return execution


@router.post(
    "/etl/executions/{execution_id}/interpret-spanish",
    response_model=EtlExecutionRead,
)
async def retry_spanish_interpretation(
    execution_id: int,
    actor: User = Depends(require_permission("etl.executions.write")),
    session: AsyncSession = Depends(get_session),
) -> EtlExecution:
    execution = (
        await session.execute(
            select(EtlExecution).where(EtlExecution.id == execution_id).with_for_update()
        )
    ).scalar_one_or_none()
    if execution is None:
        raise HTTPException(status_code=404, detail="Ejecución ETL no encontrada.")
    reconciliation = execution.metrics_document.get("reconciliation", {})
    if (
        execution.status not in {"succeeded", "validation_warning"}
        or not isinstance(reconciliation, dict)
        or not bool(reconciliation.get("passed"))
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "La interpretación sólo puede reintentarse después de una carga conciliada. "
                "Resuelva primero los errores de materialización."
            ),
        )
    candidates = await asyncio.to_thread(discover_spanish_label_candidates, execution.id)
    metrics = dict(execution.metrics_document)
    if not candidates:
        metrics["semantic_interpretation"] = {
            "policy": "preserve-original-add-spanish-label",
            "status": "not_required",
            "mappings": [],
            "message": (
                "No se detectaron categorías inglesas aptas para traducción. Los nombres "
                "técnicos siguen explicados en español y los datos originales se conservan."
            ),
        }
    else:
        try:
            mappings, provider_kind, model_id = await _localize_categories(candidates, session)
        except ProviderGenerationError as exc:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"El proveedor no pudo interpretar las categorías: {exc} "
                    "Pruebe otra configuración activa y vuelva a intentarlo."
                ),
            ) from exc
        metrics["semantic_interpretation"] = {
            "policy": "preserve-original-add-spanish-label",
            "status": "review_required",
            "provider_kind": provider_kind,
            "model_id": model_id,
            "mappings": mappings,
            "message": (
                "La IA preparó etiquetas españolas. Revise, corrija o excluya cada mapeo "
                "antes de publicarlo; los valores originales permanecen intactos."
            ),
        }
    execution.metrics_document = metrics
    semantic_result = metrics.get("semantic_interpretation", {})
    execution.status = (
        "succeeded"
        if isinstance(semantic_result, dict) and semantic_result.get("status") == "not_required"
        else "validation_warning"
    )
    execution.validation_document = {
        **execution.validation_document,
        "materialization_passed": True,
        "reconciliation_passed": True,
        "message": (
            "El datamart quedó conciliado; revise la interpretación española propuesta."
            if execution.status == "validation_warning"
            else "El datamart quedó conciliado y no requiere etiquetas adicionales."
        ),
    }
    await add_audit_event(
        session,
        actor.id,
        "etl.execution.interpret_spanish",
        "etl_execution",
        str(execution.id),
        {"status": execution.status, "candidate_groups": len(candidates)},
    )
    await session.commit()
    await session.refresh(execution)
    return execution


@router.post(
    "/etl/executions/{execution_id}/interpret-spanish/apply",
    response_model=EtlExecutionRead,
)
async def apply_spanish_interpretation(
    execution_id: int,
    payload: SpanishInterpretationDecision,
    actor: User = Depends(require_permission("etl.executions.write")),
    session: AsyncSession = Depends(get_session),
) -> EtlExecution:
    if not payload.confirmation:
        raise HTTPException(
            status_code=422,
            detail="Confirme que revisó las etiquetas antes de publicarlas.",
        )
    execution = (
        await session.execute(
            select(EtlExecution).where(EtlExecution.id == execution_id).with_for_update()
        )
    ).scalar_one_or_none()
    if execution is None:
        raise HTTPException(status_code=404, detail="Ejecución ETL no encontrada.")
    metrics = dict(execution.metrics_document)
    stored_semantic = metrics.get("semantic_interpretation", {})
    if not isinstance(stored_semantic, dict) or stored_semantic.get("status") != "review_required":
        raise HTTPException(
            status_code=409,
            detail="Esta ejecución no tiene una interpretación pendiente de revisión.",
        )
    proposed_groups = stored_semantic.get("mappings", [])
    proposed: dict[tuple[str, str], set[str]] = {}
    if isinstance(proposed_groups, list):
        for group in proposed_groups:
            if not isinstance(group, dict):
                continue
            raw_mappings = group.get("mappings", [])
            mappings = raw_mappings if isinstance(raw_mappings, list) else []
            proposed[(str(group.get("dimension")), str(group.get("target_column")))] = {
                str(item.get("original")) for item in mappings if isinstance(item, dict)
            }
    reviewed: list[dict[str, object]] = []
    for group in payload.groups:
        key = (group.dimension, group.target_column)
        if key not in proposed:
            raise HTTPException(
                status_code=422,
                detail="La decisión contiene una dimensión o columna no propuesta.",
            )
        normalized_mappings = []
        for mapping in group.mappings:
            if mapping.original not in proposed[key]:
                raise HTTPException(
                    status_code=422,
                    detail="La decisión contiene un valor original no propuesto.",
                )
            normalized_mappings.append(
                {"original": mapping.original, "label_es": mapping.label_es.strip()}
            )
        reviewed.append(
            {
                "dimension": group.dimension,
                "target_column": group.target_column,
                "mappings": normalized_mappings,
            }
        )
    applied = await asyncio.to_thread(apply_spanish_labels, execution.id, reviewed)
    semantic = _applied_semantic_document(
        stored_semantic,
        applied,
        reviewed_by=f"{actor.full_name} <{actor.email}>",
        reviewed_at=datetime.now(UTC).isoformat(),
        analyst_comment=payload.analyst_comment,
    )
    metrics["semantic_interpretation"] = semantic
    execution.metrics_document = metrics
    execution.status = "succeeded"
    execution.validation_document = {
        **execution.validation_document,
        "message": "El datamart quedó materializado, conciliado e interpretado en español.",
    }
    await add_audit_event(
        session,
        actor.id,
        "etl.execution.interpret_spanish.apply",
        "etl_execution",
        str(execution.id),
        {"groups_applied": len(reviewed), "comment": payload.analyst_comment},
    )
    await session.commit()
    await session.refresh(execution)
    return execution
