from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin
from app.models.enums import EventType


if TYPE_CHECKING:
    from app.models.field import Field
    from app.models.notification import Notification


class WeatherForecast(TimestampMixin, Base):
    __tablename__ = "weather_forecasts"
    __table_args__ = (
        UniqueConstraint("field_id", "forecast_datetime", "event_type", name="uq_weather_forecast_field_datetime_event"),
        Index("ix_weather_forecasts_field_event_datetime", "field_id", "event_type", "forecast_datetime"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"), nullable=False)
    forecast_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_type: Mapped[EventType] = mapped_column(SqlEnum(EventType, name="event_type"), nullable=False)
    probability_percent: Mapped[float] = mapped_column(Float, nullable=False)
    intensity_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    field: Mapped[Field] = relationship(back_populates="forecasts")
    notifications: Mapped[list[Notification]] = relationship(back_populates="forecast")
