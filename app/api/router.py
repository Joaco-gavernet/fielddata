from fastapi import APIRouter

from app.api.routes.alerts import router as alerts_router
from app.api.routes.fields import router as fields_router
from app.api.routes.forecasts import router as forecasts_router
from app.api.routes.health import router as health_router
from app.api.routes.internal import router as internal_router
from app.api.routes.notifications import router as notifications_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(fields_router)
api_router.include_router(alerts_router)
api_router.include_router(forecasts_router)
api_router.include_router(notifications_router)
api_router.include_router(internal_router)
