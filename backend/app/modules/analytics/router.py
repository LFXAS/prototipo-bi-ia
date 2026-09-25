from __future__ import annotations

import asyncio
import hashlib
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.modules.copilot.models import BiProposal
from app.modules.etl.models import EtlExecution
from app.modules.metadata.models import MetadataSnapshot
from app.modules.parameters.models import LlmConfiguration, Parameter, Secret
from app.modules.parameters.providers import ProviderGenerationError, generate_json
from app.modules.parameters.secrets import SecretCipher, SecretDecryptionError
from app.modules.reports.analytics_export import build_analytics_pdf, build_analytics_xlsx
from app.modules.security.models import User
from app.modules.security.service import add_audit_event, require_permission, user_permission_codes

from .schemas import AnalyticsCopilotRead, AnalyticsCopilotRequest, AnalyticsDashboardRead
from .service import AnalyticsUnavailableError, build_dashboard

router = APIRouter(tags=["analytics"])
_secret_cipher = SecretCipher(settings.secrets_key_path)

_ANALYTICS_COPILOT_INSTRUCTION = """
Eres un copiloto de análisis de ventas. Responde en español claro para el perfil indicado.
Usa exclusivamente los indicadores, puntos agregados, filtros, hallazgos y controles de
calidad incluidos en el contexto. No inventes cifras, causas, relaciones, pronósticos ni
acciones ejecutadas. Distingue un patrón observado de una relación causal. Si la pregunta
no puede responderse con la evidencia disponible, indícalo y explica qué dato agregado
faltaría. Nunca enumeres causas hipotéticas ni afirmes que existe un problema estructural
si el contexto no aporta evidencia causal. Si el usuario pregunta "por qué", separa con
claridad lo observado de lo que aún debe investigarse; expresa los datos adicionales como
necesidades de validación, no como explicaciones posibles. No generes SQL. Devuelve
únicamente el objeto JSON solicitado.
""".strip()

_ANALYTICS_COPILOT_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answer": {"type": "string", "minLength": 20, "maxLength": 1800},
        "evidence": {
            "type": "array",
            "minItems": 1,
            "maxItems": 5,
            "items": {"type": "string", "minLength": 5, "maxLength": 300},
        },
        "suggested_questions": {
            "type": "array",
            "minItems": 2,
            "maxItems": 3,
            "items": {"type": "string", "minLength": 5, "maxLength": 180},
        },
        "caveat": {"type": "string", "minLength": 5, "maxLength": 300},
    },
    "required": ["answer", "evidence", "suggested_questions", "caveat"],
}


async def _active_llm(session: AsyncSession) -> LlmConfiguration | None:
    return (
        await session.execute(
            select(LlmConfiguration).where(LlmConfiguration.is_active.is_(True)).limit(1)
        )
    ).scalar_one_or_none()


async def _llm_credential(configuration: LlmConfiguration, session: AsyncSession) -> str | None:
    if configuration.provider_kind == "ollama-local":
        return None
    secret = await session.get(Secret, configuration.secret_id) if configuration.secret_id else None
    if secret is None:
        return None
    try:
        return _secret_cipher.decrypt(secret.ciphertext)
    except (SecretDecryptionError, OSError):
        return None


async def _load_dashboard(
    session: AsyncSession,
    *,
    execution_id: int | None,
    metric_code: str | None,
    year: int | None,
    territory: str | None,
) -> AnalyticsDashboardRead:
    statement = select(EtlExecution).where(EtlExecution.status == "succeeded")
    if execution_id is not None:
        statement = statement.where(EtlExecution.id == execution_id)
    execution = (
        await session.execute(
            statement.order_by(EtlExecution.finished_at.desc(), EtlExecution.id.desc()).limit(1)
        )
    ).scalar_one_or_none()
    if execution is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Todavía no existe una ejecución ETL conciliada y publicada. Complete la "
                "validación del datamart antes de abrir el análisis."
            ),
        )
    reconciliation = execution.metrics_document.get("reconciliation", {})
    if not isinstance(reconciliation, dict) or not bool(reconciliation.get("passed")):
        raise HTTPException(
            status_code=409,
            detail="La ejecución seleccionada no conserva una conciliación aprobada.",
        )
    proposal = await session.get(BiProposal, execution.proposal_id)
    snapshot = await session.get(MetadataSnapshot, execution.metadata_snapshot_id)
    if proposal is None or snapshot is None:
        raise HTTPException(
            status_code=409,
            detail="El expediente perdió la propuesta o la instantánea requerida para analizarlo.",
        )
    try:
        return await build_dashboard(
            session,
            execution,
            proposal,
            snapshot,
            metric_code=metric_code,
            year=year,
            territory=territory,
        )
    except AnalyticsUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/analytics/dashboard", response_model=AnalyticsDashboardRead)
async def analytics_dashboard(
    execution_id: int | None = Query(default=None, gt=0),
    metric_code: str | None = Query(default=None, min_length=1, max_length=80),
    year: int | None = Query(default=None, ge=1900, le=2200),
    territory: str | None = Query(default=None, min_length=1, max_length=100),
    _: User = Depends(require_permission("analytics.dashboard.read")),
    session: AsyncSession = Depends(get_session),
) -> AnalyticsDashboardRead:
    return await _load_dashboard(
        session,
        execution_id=execution_id,
        metric_code=metric_code,
        year=year,
        territory=territory,
    )


@router.post("/analytics/copilot", response_model=AnalyticsCopilotRead)
async def analytics_copilot(
    payload: AnalyticsCopilotRequest,
    actor: User = Depends(require_permission("analytics.dashboard.read")),
    session: AsyncSession = Depends(get_session),
) -> AnalyticsCopilotRead:
    dashboard = await _load_dashboard(
        session,
        execution_id=payload.execution_id,
        metric_code=payload.metric_code,
        year=payload.year,
        territory=payload.territory,
    )
    configuration = await _active_llm(session)
    if configuration is None or configuration.last_test_status != "ok":
        raise HTTPException(
            status_code=422,
            detail="El copiloto requiere una configuración LLM activa y probada.",
        )
    credential = await _llm_credential(configuration, session)
    if configuration.provider_kind != "ollama-local" and credential is None:
        raise HTTPException(
            status_code=422,
            detail="La configuración activa no dispone de una credencial utilizable.",
        )
    timeout_value = await session.scalar(
        select(Parameter.value).where(Parameter.key == "LLM_TIMEOUT_SECONDS")
    )
    context = {
        "audience": "dirección y gerencia" if payload.view == "executive" else "analista BI",
        "question": payload.question,
        "history": [item.model_dump() for item in payload.history[-6:]],
        "selection": {
            "execution_id": dashboard.execution_id,
            "proposal_id": dashboard.proposal_id,
            "period": dashboard.period_label,
            "metric_code": dashboard.metric_code,
            "currency": dashboard.currency_code,
            "year": dashboard.filters.selected_year,
            "territory": dashboard.filters.selected_territory,
        },
        "kpis": [item.model_dump() for item in dashboard.kpis],
        "visuals": [item.model_dump() for item in dashboard.visuals],
        "deterministic_insights": [item.model_dump() for item in dashboard.insights],
        "quality": dashboard.quality.model_dump(),
        "grain": dashboard.grain,
    }
    try:
        generated = await generate_json(
            configuration,
            _ANALYTICS_COPILOT_INSTRUCTION,
            context,
            credential=credential,
            timeout_seconds=int(timeout_value or 30),
            max_output_tokens=1400,
            response_schema=_ANALYTICS_COPILOT_SCHEMA,
        )
        result = AnalyticsCopilotRead(
            **generated,
            provider_kind=configuration.provider_kind,
            model_id=configuration.model_id,
        )
    except (ProviderGenerationError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    await add_audit_event(
        session,
        actor.id,
        "analytics.copilot.ask",
        "etl_execution",
        str(dashboard.execution_id),
        {
            "question_hash": hashlib.sha256(payload.question.encode()).hexdigest()[:12],
            "history_turns": len(payload.history),
            "view": payload.view,
            "metric_code": dashboard.metric_code,
            "year": payload.year,
            "territory": payload.territory,
            "provider": configuration.provider_kind,
            "model": configuration.model_id,
        },
    )
    await session.commit()
    return result


@router.get("/analytics/reports/{report_format}")
async def export_analytics_report(
    report_format: Literal["pdf", "xlsx"],
    view: Literal["executive", "analyst"] = Query(default="executive"),
    execution_id: int | None = Query(default=None, gt=0),
    metric_code: str | None = Query(default=None, min_length=1, max_length=80),
    year: int | None = Query(default=None, ge=1900, le=2200),
    territory: str | None = Query(default=None, min_length=1, max_length=100),
    actor: User = Depends(require_permission("reports.analytics.export")),
    session: AsyncSession = Depends(get_session),
) -> Response:
    if "analytics.dashboard.read" not in user_permission_codes(actor):
        raise HTTPException(
            status_code=403,
            detail="El permiso de exportación requiere también acceso al panel analítico.",
        )
    dashboard = await _load_dashboard(
        session,
        execution_id=execution_id,
        metric_code=metric_code,
        year=year,
        territory=territory,
    )
    if report_format == "pdf":
        content = await asyncio.to_thread(build_analytics_pdf, dashboard, view)
        media_type = "application/pdf"
    else:
        content = await asyncio.to_thread(build_analytics_xlsx, dashboard, view)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    filename = f"ventas-ejecucion-{dashboard.execution_id}-{view}.{report_format}"
    await add_audit_event(
        session,
        actor.id,
        "reports.analytics.export",
        "etl_execution",
        str(dashboard.execution_id),
        {
            "format": report_format,
            "view": view,
            "metric_code": dashboard.metric_code,
            "year": year,
            "territory": territory,
        },
    )
    await session.commit()
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
