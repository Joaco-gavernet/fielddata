from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.time import APP_TIMEZONE


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def to_app_timezone(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.astimezone(APP_TIMEZONE)
