from __future__ import annotations

import asyncio
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.time import now_tz
from app.db.session import AsyncSessionLocal
from app.models.alert import AlertValidityWindow, WeatherAlert
from app.models.enums import EventType, RelativeWindowUnit, ValidityWindowKind
from app.models.field import Field
from app.models.forecast import WeatherForecast
from app.models.user import User


async def bootstrap_database(session: AsyncSession, include_sample_alerts: bool = True) -> None:
    settings = get_settings()
    user = await session.scalar(select(User).where(User.phone == settings.default_user_phone))
    if user is None:
        user = User(name=settings.default_user_name, phone=settings.default_user_phone)
        session.add(user)
        await session.flush()

    field_names = ["North Field", "South Field"]
    fields_by_name: dict[str, Field] = {}
    existing_fields = list((await session.scalars(select(Field).where(Field.user_id == user.id))).all())
    for field in existing_fields:
        fields_by_name[field.name] = field

    for field_name in field_names:
        if field_name not in fields_by_name:
            field = Field(user_id=user.id, name=field_name)
            session.add(field)
            await session.flush()
            fields_by_name[field_name] = field

    base_time = now_tz().replace(minute=0, second=0, microsecond=0)
    forecast_rows = [
        {
            "field_id": fields_by_name["North Field"].id,
            "forecast_datetime": base_time + timedelta(hours=1),
            "event_type": EventType.RAIN,
            "probability_percent": 85.0,
            "intensity_value": 12.0,
        },
        {
            "field_id": fields_by_name["North Field"].id,
            "forecast_datetime": base_time + timedelta(days=1),
            "event_type": EventType.STRONG_WIND,
            "probability_percent": 72.0,
            "intensity_value": 58.0,
        },
        {
            "field_id": fields_by_name["North Field"].id,
            "forecast_datetime": base_time + timedelta(days=6),
            "event_type": EventType.FROST,
            "probability_percent": 91.0,
            "intensity_value": -2.0,
        },
        {
            "field_id": fields_by_name["South Field"].id,
            "forecast_datetime": base_time + timedelta(days=2),
            "event_type": EventType.HAIL,
            "probability_percent": 67.0,
            "intensity_value": 9.0,
        },
        {
            "field_id": fields_by_name["South Field"].id,
            "forecast_datetime": base_time + timedelta(days=30),
            "event_type": EventType.RAIN,
            "probability_percent": 83.0,
            "intensity_value": 15.0,
        },
    ]

    await session.execute(
        insert(WeatherForecast)
        .values(forecast_rows)
        .on_conflict_do_nothing(index_elements=["field_id", "forecast_datetime", "event_type"])
    )

    if include_sample_alerts:
        existing_rain_alert = await session.scalar(
            select(WeatherAlert).where(
                WeatherAlert.user_id == user.id,
                WeatherAlert.field_id == fields_by_name["North Field"].id,
                WeatherAlert.event_type == EventType.RAIN,
            )
        )
        if existing_rain_alert is None:
            session.add(
                WeatherAlert(
                    user_id=user.id,
                    field_id=fields_by_name["North Field"].id,
                    event_type=EventType.RAIN,
                    probability_threshold_percent=80.0,
                    intensity_threshold_value=8.0,
                    validity_windows=[
                        AlertValidityWindow(
                            kind=ValidityWindowKind.RELATIVE,
                            relative_value=1,
                            relative_unit=RelativeWindowUnit.WEEK,
                        )
                    ],
                )
            )

    await session.commit()


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await bootstrap_database(session)


if __name__ == "__main__":
    asyncio.run(main())
