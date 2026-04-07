from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import get_event_definition
from app.core.time import now_tz
from app.models.alert import AlertValidityWindow, WeatherAlert
from app.models.enums import EventType, RelativeWindowUnit, ValidityWindowKind
from app.models.forecast import WeatherForecast
from app.models.notification import Notification


@dataclass(slots=True)
class AlertEvaluationResult:
    evaluated_alerts: int = 0
    matched_forecasts: int = 0
    created_notifications: int = 0


def resolve_window_bounds(window: AlertValidityWindow, evaluation_time: datetime) -> tuple[datetime, datetime]:
    if window.kind == ValidityWindowKind.ABSOLUTE:
        if window.start_datetime is None or window.end_datetime is None:
            raise ValueError("Absolute windows require start and end datetimes")
        return window.start_datetime, window.end_datetime

    if window.relative_value is None or window.relative_unit is None:
        raise ValueError("Relative windows require a value and unit")

    if window.relative_unit == RelativeWindowUnit.HOUR:
        delta = timedelta(hours=window.relative_value)
    elif window.relative_unit == RelativeWindowUnit.DAY:
        delta = timedelta(days=window.relative_value)
    elif window.relative_unit == RelativeWindowUnit.WEEK:
        delta = timedelta(weeks=window.relative_value)
    elif window.relative_unit == RelativeWindowUnit.MONTH:
        delta = relativedelta(months=window.relative_value)
    elif window.relative_unit == RelativeWindowUnit.YEAR:
        delta = relativedelta(years=window.relative_value)
    else:
        raise ValueError(f"Unsupported relative unit: {window.relative_unit}")

    return evaluation_time, evaluation_time + delta


def matches_intensity_threshold(event_type: EventType, threshold: float | None, forecast_value: float | None) -> bool:
    if threshold is None:
        return True
    if forecast_value is None:
        return False

    comparator = get_event_definition(event_type).intensity_comparator
    return comparator(forecast_value, threshold)


def is_forecast_in_any_window(
    forecast_datetime: datetime,
    windows: list[AlertValidityWindow],
    evaluation_time: datetime,
) -> bool:
    return any(
        start <= forecast_datetime <= end
        for start, end in (resolve_window_bounds(window, evaluation_time) for window in windows)
    )


def build_notification_message(alert: WeatherAlert, forecast: WeatherForecast) -> str:
    event_definition = get_event_definition(alert.event_type)
    intensity_fragment = ""
    if forecast.intensity_value is not None:
        intensity_fragment = (
            f" and intensity {forecast.intensity_value:.2f} {event_definition.intensity_unit.value}"
        )

    return (
        f"Alert triggered for field {alert.field.name}: {forecast.event_type.value} forecast at "
        f"{forecast.forecast_datetime.isoformat()} with probability "
        f"{forecast.probability_percent:.2f}%{intensity_fragment}."
    )


async def evaluate_alerts(
    session: AsyncSession,
    evaluation_time: datetime | None = None,
) -> AlertEvaluationResult:
    evaluation_time = evaluation_time or now_tz()
    result = AlertEvaluationResult()

    alerts = list(
        (
            await session.scalars(
                select(WeatherAlert)
                .where(WeatherAlert.is_active.is_(True))
                .options(
                    selectinload(WeatherAlert.field),
                    selectinload(WeatherAlert.validity_windows),
                )
            )
        ).all()
    )

    result.evaluated_alerts = len(alerts)

    for alert in alerts:
        if not alert.validity_windows:
            continue

        window_clauses = []
        for window in alert.validity_windows:
            start, end = resolve_window_bounds(window, evaluation_time)
            window_clauses.append(
                and_(
                    WeatherForecast.forecast_datetime >= start,
                    WeatherForecast.forecast_datetime <= end,
                )
            )

        forecasts = list(
            (
                await session.scalars(
                    select(WeatherForecast)
                    .where(
                        WeatherForecast.field_id == alert.field_id,
                        WeatherForecast.event_type == alert.event_type,
                        or_(*window_clauses),
                    )
                )
            ).all()
        )

        for forecast in forecasts:
            if not is_forecast_in_any_window(
                forecast_datetime=forecast.forecast_datetime,
                windows=alert.validity_windows,
                evaluation_time=evaluation_time,
            ):
                continue

            if forecast.probability_percent < alert.probability_threshold_percent:
                continue

            if not matches_intensity_threshold(
                event_type=alert.event_type,
                threshold=alert.intensity_threshold_value,
                forecast_value=forecast.intensity_value,
            ):
                continue

            result.matched_forecasts += 1

            statement = (
                insert(Notification)
                .values(
                    alert_id=alert.id,
                    forecast_id=forecast.id,
                    user_id=alert.user_id,
                    field_id=alert.field_id,
                    event_type=alert.event_type,
                    forecast_datetime=forecast.forecast_datetime,
                    trigger_probability_percent=forecast.probability_percent,
                    trigger_intensity_value=forecast.intensity_value,
                    message=build_notification_message(alert, forecast),
                    created_at=evaluation_time,
                )
                .on_conflict_do_nothing(index_elements=["alert_id", "forecast_id"])
            )
            execution = await session.execute(statement)
            if execution.rowcount:
                result.created_notifications += 1

    await session.commit()
    return result
