from __future__ import annotations

import os

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.session import get_db_session
from app.main import create_app
from app.seeds.bootstrap import bootstrap_database


@pytest.fixture(scope="session")
def test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not set; skipping Postgres integration tests")
    return database_url


@pytest.fixture(scope="session")
def migrated_test_database(test_database_url: str) -> str:
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", test_database_url)
    command.upgrade(alembic_config, "head")
    return test_database_url


@pytest_asyncio.fixture
async def integration_engine(migrated_test_database: str):
    engine = create_async_engine(migrated_test_database, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(integration_engine):
    return async_sessionmaker(integration_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def prepared_database(session_factory):
    async with session_factory() as session:
        await session.execute(
            text(
                "TRUNCATE notifications, alert_validity_windows, weather_alerts, "
                "weather_forecasts, fields, users RESTART IDENTITY CASCADE"
            )
        )
        await session.commit()
        await bootstrap_database(session, include_sample_alerts=False)
    yield


@pytest_asyncio.fixture
async def client(session_factory, prepared_database):
    app = create_app()

    async def override_get_db_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
            yield test_client

    app.dependency_overrides.clear()
