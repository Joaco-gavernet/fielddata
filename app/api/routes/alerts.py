from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_default_user
from app.db.session import get_db_session
from app.models.alert import AlertValidityWindow, WeatherAlert
from app.models.field import Field
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertRead, AlertUpdate


router = APIRouter(prefix="/alerts", tags=["alerts"])


async def get_user_field(session: AsyncSession, user_id: int, field_id: int) -> Field | None:
    return await session.scalar(select(Field).where(Field.id == field_id, Field.user_id == user_id))


async def get_user_alert(session: AsyncSession, user_id: int, alert_id: int) -> WeatherAlert | None:
    return await session.scalar(
        select(WeatherAlert)
        .where(WeatherAlert.id == alert_id, WeatherAlert.user_id == user_id)
        .options(selectinload(WeatherAlert.validity_windows))
    )


def build_windows(payload_windows) -> list[AlertValidityWindow]:
    return [
        AlertValidityWindow(
            kind=window.kind,
            relative_value=window.relative_value,
            relative_unit=window.relative_unit,
            start_datetime=window.start_datetime,
            end_datetime=window.end_datetime,
        )
        for window in payload_windows
    ]


@router.get("", response_model=list[AlertRead])
async def list_alerts(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_default_user),
) -> list[AlertRead]:
    alerts = list(
        (
            await session.scalars(
                select(WeatherAlert)
                .where(WeatherAlert.user_id == user.id)
                .options(selectinload(WeatherAlert.validity_windows))
                .order_by(WeatherAlert.id)
            )
        ).all()
    )
    return [AlertRead.from_model(alert) for alert in alerts]


@router.post("", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
async def create_alert(
    payload: AlertCreate,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_default_user),
) -> AlertRead:
    field = await get_user_field(session=session, user_id=user.id, field_id=payload.field_id)
    if field is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    alert = WeatherAlert(
        user_id=user.id,
        field_id=field.id,
        event_type=payload.event_type,
        probability_threshold_percent=payload.probability_threshold_percent,
        intensity_threshold_value=payload.intensity_threshold_value,
        validity_windows=build_windows(payload.validity_windows),
    )
    session.add(alert)
    await session.commit()

    persisted_alert = await get_user_alert(session=session, user_id=user.id, alert_id=alert.id)
    if persisted_alert is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Alert not found after creation")
    return AlertRead.from_model(persisted_alert)


@router.get("/{alert_id}", response_model=AlertRead)
async def get_alert(
    alert_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_default_user),
) -> AlertRead:
    alert = await get_user_alert(session=session, user_id=user.id, alert_id=alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return AlertRead.from_model(alert)


@router.patch("/{alert_id}", response_model=AlertRead)
async def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_default_user),
) -> AlertRead:
    alert = await get_user_alert(session=session, user_id=user.id, alert_id=alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field_name in ("probability_threshold_percent", "intensity_threshold_value", "is_active"):
        if field_name in update_data:
            setattr(alert, field_name, update_data[field_name])

    if "validity_windows" in update_data:
        alert.validity_windows = build_windows(payload.validity_windows or [])

    await session.commit()
    refreshed_alert = await get_user_alert(session=session, user_id=user.id, alert_id=alert_id)
    if refreshed_alert is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Alert not found after update")
    return AlertRead.from_model(refreshed_alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_default_user),
) -> Response:
    alert = await get_user_alert(session=session, user_id=user.id, alert_id=alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.is_active = False
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
