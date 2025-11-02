import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import create_app
from app.db.session import get_session as app_get_session
from app.models.base import Base
from app.models.user import User
from app.core.security import get_current_user


DB_FILE = Path("./test_modules_flags.db")
TEST_DB_URL = f"sqlite+aiosqlite:///{DB_FILE}"


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


def build_app_with_db(monkeypatch):
    # Ensure SECRET_KEY for settings
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-modules")
    # Fresh DB file
    if DB_FILE.exists():
        DB_FILE.unlink()
    engine = create_async_engine(TEST_DB_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    import asyncio

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_models())

    app = create_app()

    async def override_get_session():
        async with async_session() as s:
            yield s

    app.dependency_overrides[app_get_session] = override_get_session

    async def _get_user():
        return User(id=1, email="mod@example.com", hashed_password="x")

    app.dependency_overrides[get_current_user] = _get_user
    return app, engine


def teardown_db(engine):
    import asyncio

    async def drop_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(drop_models())
    try:
        DB_FILE.unlink()
    except FileNotFoundError:
        pass


def test_finance_guard_denies_when_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_FINANCE", "false")
    app, engine = build_app_with_db(monkeypatch)
    try:
        with TestClient(app) as client:
            r = client.get("/fin/accounts")
            assert r.status_code == 403
    finally:
        teardown_db(engine)


def test_finance_guard_allows_when_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_FINANCE", "true")
    app, engine = build_app_with_db(monkeypatch)
    try:
        with TestClient(app) as client:
            r = client.get("/fin/accounts")
            assert r.status_code == 200
            assert r.json() == []
    finally:
        teardown_db(engine)

