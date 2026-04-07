from datetime import datetime

from pydantic import field_serializer

from app.core.events import get_event_definition
from app.models.enums import EventType, IntensityUnit
from app.schemas.common import APIModel, to_app_timezone


class NotificationRead(APIModel):
    id: int
    alert_id: int
    forecast_id: int
    field_id: int
    event_type: EventType
    forecast_datetime: datetime
    trigger_probability_percent: float
    trigger_intensity_value: float | None
    intensity_unit: IntensityUnit
    message: str
    created_at: datetime

    @field_serializer("forecast_datetime", "created_at")
    def serialize_datetimes(self, value: datetime) -> datetime:
        return to_app_timezone(value)

    @classmethod
    def from_model(cls, notification) -> "NotificationRead":
        return cls(
            id=notification.id,
            alert_id=notification.alert_id,
            forecast_id=notification.forecast_id,
            field_id=notification.field_id,
            event_type=notification.event_type,
            forecast_datetime=notification.forecast_datetime,
            trigger_probability_percent=notification.trigger_probability_percent,
            trigger_intensity_value=notification.trigger_intensity_value,
            intensity_unit=get_event_definition(notification.event_type).intensity_unit,
            message=notification.message,
            created_at=notification.created_at,
        )
