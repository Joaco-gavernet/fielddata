from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_default_user
from app.db.session import get_db_session
from app.models.enums import EventType
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationRead


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    field_id: int | None = None,
    event_type: EventType | None = None,
    from_datetime: datetime | None = Query(default=None),
    to_datetime: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_default_user),
) -> list[NotificationRead]:
    statement = select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc())

    if field_id is not None:
        statement = statement.where(Notification.field_id == field_id)
    if event_type is not None:
        statement = statement.where(Notification.event_type == event_type)
    if from_datetime is not None:
        statement = statement.where(Notification.created_at >= from_datetime)
    if to_datetime is not None:
        statement = statement.where(Notification.created_at <= to_datetime)

    notifications = list((await session.scalars(statement)).all())
    return [NotificationRead.from_model(notification) for notification in notifications]
