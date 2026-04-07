from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models.user import User


async def get_settings_dependency() -> Settings:
    return get_settings()


async def get_default_user(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> User:
    user = await session.scalar(select(User).where(User.phone == settings.default_user_phone))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Default user not found. Run the bootstrap seed first.",
        )
    return user
