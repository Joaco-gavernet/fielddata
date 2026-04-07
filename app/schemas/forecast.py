from datetime import datetime

from pydantic import field_serializer

from app.core.events import get_event_definition
from app.models.enums import EventType, IntensityUnit
from app.schemas.common import APIModel, to_app_timezone


class ForecastRead(APIModel):
    id: int
    field_id: int
    forecast_datetime: datetime
    event_type: EventType
    probability_percent: float
    intensity_value: float | None
    intensity_unit: IntensityUnit
    created_at: datetime
    updated_at: datetime

    @field_serializer("forecast_datetime", "created_at", "updated_at")
    def serialize_datetimes(self, value: datetime) -> datetime:
        return to_app_timezone(value)

    @classmethod
    def from_model(cls, forecast) -> "ForecastRead":
        return cls(
            id=forecast.id,
            field_id=forecast.field_id,
            forecast_datetime=forecast.forecast_datetime,
            event_type=forecast.event_type,
            probability_percent=forecast.probability_percent,
            intensity_value=forecast.intensity_value,
            intensity_unit=get_event_definition(forecast.event_type).intensity_unit,
            created_at=forecast.created_at,
            updated_at=forecast.updated_at,
        )
