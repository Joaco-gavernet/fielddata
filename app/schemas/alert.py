from datetime import datetime

from pydantic import AwareDatetime, Field, field_serializer, model_validator

from app.core.events import get_event_definition
from app.models.enums import EventType, IntensityUnit, RelativeWindowUnit, ValidityWindowKind
from app.schemas.common import APIModel, to_app_timezone


class AlertValidityWindowCreate(APIModel):
    kind: ValidityWindowKind
    relative_value: int | None = None
    relative_unit: RelativeWindowUnit | None = None
    start_datetime: AwareDatetime | None = None
    end_datetime: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_window(self) -> "AlertValidityWindowCreate":
        utc_minus_three_seconds = -3 * 60 * 60

        if self.kind == ValidityWindowKind.RELATIVE:
            if self.relative_value is None or self.relative_unit is None:
                raise ValueError("Relative windows require relative_value and relative_unit")
            if self.relative_value <= 0:
                raise ValueError("relative_value must be greater than zero")
            if self.start_datetime is not None or self.end_datetime is not None:
                raise ValueError("Relative windows cannot define absolute datetimes")

        if self.kind == ValidityWindowKind.ABSOLUTE:
            if self.start_datetime is None or self.end_datetime is None:
                raise ValueError("Absolute windows require start_datetime and end_datetime")
            if self.start_datetime >= self.end_datetime:
                raise ValueError("start_datetime must be earlier than end_datetime")
            if self.start_datetime.utcoffset() is None or self.end_datetime.utcoffset() is None:
                raise ValueError("Absolute windows require timezone-aware datetimes")
            if int(self.start_datetime.utcoffset().total_seconds()) != utc_minus_three_seconds:
                raise ValueError("start_datetime must use the -03:00 offset")
            if int(self.end_datetime.utcoffset().total_seconds()) != utc_minus_three_seconds:
                raise ValueError("end_datetime must use the -03:00 offset")
            if self.relative_value is not None or self.relative_unit is not None:
                raise ValueError("Absolute windows cannot define relative values")

        return self


class AlertValidityWindowRead(APIModel):
    id: int
    kind: ValidityWindowKind
    relative_value: int | None = None
    relative_unit: RelativeWindowUnit | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    @field_serializer("start_datetime", "end_datetime")
    def serialize_datetimes(self, value: datetime | None) -> datetime | None:
        return to_app_timezone(value)


class AlertCreate(APIModel):
    field_id: int
    event_type: EventType
    probability_threshold_percent: float = Field(ge=0, le=100)
    intensity_threshold_value: float | None = None
    validity_windows: list[AlertValidityWindowCreate] = Field(min_length=1)


class AlertUpdate(APIModel):
    probability_threshold_percent: float | None = Field(default=None, ge=0, le=100)
    intensity_threshold_value: float | None = None
    is_active: bool | None = None
    validity_windows: list[AlertValidityWindowCreate] | None = Field(default=None, min_length=1)


class AlertRead(APIModel):
    id: int
    field_id: int
    event_type: EventType
    probability_threshold_percent: float
    intensity_threshold_value: float | None
    intensity_unit: IntensityUnit
    is_active: bool
    validity_windows: list[AlertValidityWindowRead]
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetimes(self, value: datetime) -> datetime:
        return to_app_timezone(value)

    @classmethod
    def from_model(cls, alert) -> "AlertRead":
        return cls(
            id=alert.id,
            field_id=alert.field_id,
            event_type=alert.event_type,
            probability_threshold_percent=alert.probability_threshold_percent,
            intensity_threshold_value=alert.intensity_threshold_value,
            intensity_unit=get_event_definition(alert.event_type).intensity_unit,
            is_active=alert.is_active,
            validity_windows=alert.validity_windows,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )
