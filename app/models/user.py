from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin


if TYPE_CHECKING:
    from app.models.alert import WeatherAlert
    from app.models.field import Field
    from app.models.notification import Notification


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # TODO: enforce E.164 phone validation once country-specific normalization rules are defined.
    phone: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)

    fields: Mapped[list[Field]] = relationship(back_populates="user", cascade="all, delete-orphan")
    alerts: Mapped[list[WeatherAlert]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list[Notification]] = relationship(back_populates="user", cascade="all, delete-orphan")
