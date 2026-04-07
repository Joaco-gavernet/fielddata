from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EventType


if TYPE_CHECKING:
    from app.models.alert import WeatherAlert
    from app.models.field import Field
    from app.models.forecast import WeatherForecast
    from app.models.user import User


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("alert_id", "forecast_id", name="uq_notifications_alert_forecast"),
        Index("ix_notifications_user_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("weather_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_id: Mapped[int] = mapped_column(ForeignKey("weather_forecasts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[EventType] = mapped_column(SqlEnum(EventType, name="event_type"), nullable=False)
    forecast_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trigger_probability_percent: Mapped[float] = mapped_column(Float, nullable=False)
    trigger_intensity_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    message: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[User] = relationship(back_populates="notifications")
    field: Mapped[Field] = relationship(back_populates="notifications")
    alert: Mapped[WeatherAlert] = relationship(back_populates="notifications")
    forecast: Mapped[WeatherForecast] = relationship(back_populates="notifications")
