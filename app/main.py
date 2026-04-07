from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.seeds.bootstrap import bootstrap_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.seed_on_startup:
        async with AsyncSessionLocal() as session:
            await bootstrap_database(session)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="FieldData Weather Alerts", lifespan=lifespan)
    app.include_router(api_router)
    return app


app = create_app()
