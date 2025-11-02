import os
import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncSession,
)

from app.main import create_app
from app.db.session import get_session as app_get_session
from app.models.base import Base


TEST_DB_URL = "sqlite+aiosqlite:///./test_auth.db"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def app():
    # Ensure a test secret is always set for predictable JWTs
    os.environ.setdefault("SECRET_KEY", "test-secret-key-change-me")
    os.environ.setdefault("ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    app = create_app()
    return app


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db(app):
    engine = create_async_engine(TEST_DB_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_models())

    async def override_get_session():
        async with async_session() as session:
            yield session

    # Override dependency
    app.dependency_overrides[app_get_session] = override_get_session

    yield

    # Teardown
    async def drop_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(drop_models())
    try:
        os.remove("./test_auth.db")
    except FileNotFoundError:
        pass


def test_register_and_login_flow(client):
    # Register
    payload = {"email": "user@example.com", "password": "secret123"}
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["email"] == payload["email"]
    assert "id" in data

    # Login
    r2 = client.post("/auth/login", json=payload)
    assert r2.status_code == 200, r2.text
    token = r2.json()
    assert token["token_type"] == "bearer"
    assert isinstance(token["access_token"], str) and len(token["access_token"]) > 10

    # Access protected endpoint
    headers = {"Authorization": f"Bearer {token['access_token']}"}
    r3 = client.get("/me", headers=headers)
    assert r3.status_code == 200, r3.text
    me = r3.json()
    assert me["email"] == payload["email"]


def test_register_duplicate_email(client):
    email = "dup@example.com"
    payload = {"email": email, "password": "secret123"}
    r1 = client.post("/auth/register", json=payload)
    assert r1.status_code in (201, 400)
    # second attempt must fail with 400
    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code == 400


def test_login_invalid_credentials(client):
    # user does not exist
    payload = {"email": "nouser@example.com", "password": "bad"}
    r = client.post("/auth/login", json=payload)
    assert r.status_code == 401


def test_me_without_token(client):
    r = client.get("/me")
    assert r.status_code == 401
