from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.alert_evaluator import evaluate_alerts


router = APIRouter(prefix="/internal/jobs", tags=["internal"])


@router.post("/evaluate-alerts")
async def trigger_alert_evaluation(session: AsyncSession = Depends(get_db_session)) -> dict[str, int]:
    result = await evaluate_alerts(session)
    return {
        "evaluated_alerts": result.evaluated_alerts,
        "matched_forecasts": result.matched_forecasts,
        "created_notifications": result.created_notifications,
    }
