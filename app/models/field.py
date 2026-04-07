from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin


if TYPE_CHECKING:
    from app.models.alert import WeatherAlert
    from app.models.forecast import WeatherForecast
    from app.models.notification import Notification
    from app.models.user import User


class Field(TimestampMixin, Base):
    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped[User] = relationship(back_populates="fields")
    forecasts: Mapped[list[WeatherForecast]] = relationship(back_populates="field", cascade="all, delete-orphan")
    alerts: Mapped[list[WeatherAlert]] = relationship(back_populates="field", cascade="all, delete-orphan")
    notifications: Mapped[list[Notification]] = relationship(back_populates="field", cascade="all, delete-orphan")
