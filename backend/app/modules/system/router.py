from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session

router = APIRouter(prefix="/health", tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok", "not_ready"]
    service: str
    version: str
    postgres: Literal["not_checked", "ok", "unavailable"]


@router.get("/live", response_model=HealthResponse)
async def live() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        postgres="not_checked",
    )


@router.get("/ready", response_model=HealthResponse)
async def ready(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HealthResponse:
    settings = get_settings()
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="not_ready",
            service=settings.app_name,
            version=settings.app_version,
            postgres="unavailable",
        )
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        postgres="ok",
    )
