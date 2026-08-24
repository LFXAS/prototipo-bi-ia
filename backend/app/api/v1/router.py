from fastapi import APIRouter

from app.modules.system.router import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)

# Los routers de security, parameters y negocio se agregaran en iteraciones posteriores.
