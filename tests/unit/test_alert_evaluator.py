from datetime import datetime, timedelta

from app.core.time import APP_TIMEZONE
from app.models.alert import AlertValidityWindow
from app.models.enums import EventType, RelativeWindowUnit, ValidityWindowKind
from app.services.alert_evaluator import (
    is_forecast_in_any_window,
    matches_intensity_threshold,
    resolve_window_bounds,
)


def test_resolve_relative_week_window_from_evaluation_time() -> None:
    evaluation_time = datetime(2026, 4, 6, 10, 0, tzinfo=APP_TIMEZONE)
    window = AlertValidityWindow(
        kind=ValidityWindowKind.RELATIVE,
        relative_value=1,
        relative_unit=RelativeWindowUnit.WEEK,
    )

    start, end = resolve_window_bounds(window, evaluation_time)

    assert start == evaluation_time
    assert end == evaluation_time + timedelta(weeks=1)


def test_resolve_absolute_window_keeps_explicit_range() -> None:
    start_time = datetime(2026, 4, 10, 0, 0, tzinfo=APP_TIMEZONE)
    end_time = datetime(2026, 4, 11, 0, 0, tzinfo=APP_TIMEZONE)
    window = AlertValidityWindow(
        kind=ValidityWindowKind.ABSOLUTE,
        start_datetime=start_time,
        end_datetime=end_time,
    )

    start, end = resolve_window_bounds(window, datetime(2026, 4, 6, 10, 0, tzinfo=APP_TIMEZONE))

    assert start == start_time
    assert end == end_time


def test_matches_intensity_threshold_uses_event_specific_comparators() -> None:
    assert matches_intensity_threshold(EventType.RAIN, threshold=8.0, forecast_value=12.0) is True
    assert matches_intensity_threshold(EventType.RAIN, threshold=8.0, forecast_value=5.0) is False
    assert matches_intensity_threshold(EventType.FROST, threshold=-1.0, forecast_value=-2.0) is True
    assert matches_intensity_threshold(EventType.FROST, threshold=-1.0, forecast_value=1.0) is False


def test_forecast_matches_when_it_falls_in_any_validity_window() -> None:
    evaluation_time = datetime(2026, 4, 6, 10, 0, tzinfo=APP_TIMEZONE)
    windows = [
        AlertValidityWindow(
            kind=ValidityWindowKind.RELATIVE,
            relative_value=1,
            relative_unit=RelativeWindowUnit.DAY,
        ),
        AlertValidityWindow(
            kind=ValidityWindowKind.ABSOLUTE,
            start_datetime=datetime(2026, 4, 20, 0, 0, tzinfo=APP_TIMEZONE),
            end_datetime=datetime(2026, 4, 22, 0, 0, tzinfo=APP_TIMEZONE),
        ),
    ]

    assert is_forecast_in_any_window(
        forecast_datetime=datetime(2026, 4, 6, 15, 0, tzinfo=APP_TIMEZONE),
        windows=windows,
        evaluation_time=evaluation_time,
    ) is True
    assert is_forecast_in_any_window(
        forecast_datetime=datetime(2026, 4, 21, 12, 0, tzinfo=APP_TIMEZONE),
        windows=windows,
        evaluation_time=evaluation_time,
    ) is True
    assert is_forecast_in_any_window(
        forecast_datetime=datetime(2026, 4, 25, 12, 0, tzinfo=APP_TIMEZONE),
        windows=windows,
        evaluation_time=evaluation_time,
    ) is False
