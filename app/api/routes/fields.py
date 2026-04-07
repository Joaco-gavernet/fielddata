from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_default_user
from app.db.session import get_db_session
from app.models.field import Field
from app.models.user import User
from app.schemas.field import FieldCreate, FieldRead


router = APIRouter(prefix="/fields", tags=["fields"])


@router.get("", response_model=list[FieldRead])
async def list_fields(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_default_user),
) -> list[FieldRead]:
    fields = list((await session.scalars(select(Field).where(Field.user_id == user.id).order_by(Field.id))).all())
    return [FieldRead.model_validate(field) for field in fields]


@router.post("", response_model=FieldRead, status_code=status.HTTP_201_CREATED)
async def create_field(
    payload: FieldCreate,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_default_user),
) -> FieldRead:
    field = Field(user_id=user.id, name=payload.name.strip())
    session.add(field)
    await session.commit()
    await session.refresh(field)
    return FieldRead.model_validate(field)
