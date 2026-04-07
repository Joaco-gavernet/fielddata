from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_default_user
from app.db.session import get_db_session
from app.models.enums import EventType
from app.models.field import Field
from app.models.forecast import WeatherForecast
from app.models.user import User
from app.schemas.forecast import ForecastRead


router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.get("", response_model=list[ForecastRead])
async def list_forecasts(
    field_id: int | None = None,
    event_type: EventType | None = None,
    from_datetime: datetime | None = Query(default=None),
    to_datetime: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_default_user),
) -> list[ForecastRead]:
    statement = (
        select(WeatherForecast)
        .join(Field, WeatherForecast.field_id == Field.id)
        .where(Field.user_id == user.id)
        .order_by(WeatherForecast.forecast_datetime, WeatherForecast.id)
    )

    if field_id is not None:
        statement = statement.where(WeatherForecast.field_id == field_id)
    if event_type is not None:
        statement = statement.where(WeatherForecast.event_type == event_type)
    if from_datetime is not None:
        statement = statement.where(WeatherForecast.forecast_datetime >= from_datetime)
    if to_datetime is not None:
        statement = statement.where(WeatherForecast.forecast_datetime <= to_datetime)

    forecasts = list((await session.scalars(statement)).all())
    return [ForecastRead.from_model(forecast) for forecast in forecasts]
