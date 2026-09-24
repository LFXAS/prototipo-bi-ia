from fastapi import APIRouter

from app.modules.copilot.router import router as copilot_router
from app.modules.etl.router import router as etl_router
from app.modules.metadata.router import router as metadata_router
from app.modules.parameters.router import router as parameters_router
from app.modules.security.router import router as security_router
from app.modules.system.router import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(security_router)
api_router.include_router(parameters_router)
api_router.include_router(metadata_router)
api_router.include_router(copilot_router)
api_router.include_router(etl_router)
