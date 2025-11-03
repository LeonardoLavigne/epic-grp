import datetime as dt

from fastapi.testclient import TestClient

from app.main import create_app
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from app.db.session import get_session as app_get_session
from app.models.base import Base
from app.models.user import User
import asyncio
from pathlib import Path

DB_FILE = Path("./test_security_authz.db")
TEST_DB_URL = f"sqlite+aiosqlite:///{DB_FILE}"
from app.core.settings import get_settings, Settings
from app.core.security import create_access_token


def test_auth_me_unauthenticated():
    app = create_app()
    client = TestClient(app)
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_auth_me_invalid_token():
    app = create_app()
    client = TestClient(app)
    r = client.get("/auth/me", headers={"Authorization": "Bearer abc"})
    assert r.status_code == 401


def test_auth_me_invalid_payload_and_user_not_found(monkeypatch):
    # App with sqlite session override
    app = create_app()
    if DB_FILE.exists():
        DB_FILE.unlink()
    engine = create_async_engine(TEST_DB_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(init_models())

    async def override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[app_get_session] = override_get_session
    client = TestClient(app)

    s = get_settings()
    # Missing sub
    token_missing_sub = create_access_token({}, s)
    r1 = client.get("/auth/me", headers={"Authorization": f"Bearer {token_missing_sub}"})
    assert r1.status_code == 401

    # Unknown user
    token_unknown = create_access_token({"sub": "unknown@example.com"}, s)
    r2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token_unknown}"})
    assert r2.status_code == 401


def test_require_module_finance_disabled():
    app = create_app()

    # Override settings to disable finance
    def _disabled_settings() -> Settings:
        base = get_settings()
        return Settings(  # type: ignore[call-arg]
            secret_key=base.secret_key,
            algorithm=base.algorithm,
            access_token_expire_minutes=base.access_token_expire_minutes,
            enable_finance=False,
            enable_health=base.enable_health,
        )

    app.dependency_overrides[get_settings] = _disabled_settings

    # Create sqlite session with a valid user so auth passes
    if DB_FILE.exists():
        DB_FILE.unlink()
    engine = create_async_engine(TEST_DB_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with async_session() as s:
            u = User(email="mod@example.com", hashed_password="x")
            s.add(u)
            await s.commit()
    asyncio.run(init_models())

    async def override_get_session():
        async with async_session() as session:
            yield session
    app.dependency_overrides[app_get_session] = override_get_session

    client = TestClient(app)
    token = create_access_token({"sub": "mod@example.com"}, get_settings())

    # Any finance endpoint should be forbidden (403)
    r = client.get("/fin/accounts", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
