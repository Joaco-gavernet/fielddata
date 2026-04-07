from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin
from app.models.enums import EventType, RelativeWindowUnit, ValidityWindowKind


if TYPE_CHECKING:
    from app.models.field import Field
    from app.models.notification import Notification
    from app.models.user import User


class WeatherAlert(TimestampMixin, Base):
    __tablename__ = "weather_alerts"
    __table_args__ = (Index("ix_weather_alerts_field_event_active", "field_id", "event_type", "is_active"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[EventType] = mapped_column(SqlEnum(EventType, name="event_type"), nullable=False)
    probability_threshold_percent: Mapped[float] = mapped_column(Float, nullable=False)
    intensity_threshold_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    user: Mapped[User] = relationship(back_populates="alerts")
    field: Mapped[Field] = relationship(back_populates="alerts")
    validity_windows: Mapped[list[AlertValidityWindow]] = relationship(
        back_populates="alert",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list[Notification]] = relationship(back_populates="alert")


class AlertValidityWindow(TimestampMixin, Base):
    __tablename__ = "alert_validity_windows"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("weather_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[ValidityWindowKind] = mapped_column(SqlEnum(ValidityWindowKind, name="validity_window_kind"), nullable=False)
    relative_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    relative_unit: Mapped[RelativeWindowUnit | None] = mapped_column(
        SqlEnum(RelativeWindowUnit, name="relative_window_unit"),
        nullable=True,
    )
    start_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    alert: Mapped[WeatherAlert] = relationship(back_populates="validity_windows")
