from datetime import datetime

from pydantic import field_serializer

from app.schemas.common import APIModel, to_app_timezone


class FieldCreate(APIModel):
    name: str


class FieldRead(APIModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetimes(self, value: datetime) -> datetime:
        return to_app_timezone(value)
