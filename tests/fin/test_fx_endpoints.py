import asyncio
import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.main import create_app
from app.db.session import get_session as app_get_session
from app.db.base import Base
from app.core.auth.security import get_current_user
from app.core.auth.persistence.models.user import User


DB_FILE = Path("./test_fin_fx_endpoints.db")
TEST_DB_URL = f"sqlite+aiosqlite:///{DB_FILE}"


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_db(app):
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

    yield

    async def drop_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    asyncio.run(drop_models())
    try:
        DB_FILE.unlink()
    except FileNotFoundError:
        pass


def _as_user(app, user_id: int, email: str):
    async def _get_user():
        return User(id=user_id, email=email, hashed_password="x")
    app.dependency_overrides[get_current_user] = _get_user


def test_post_fx_rates_create_and_update(client, app):
    _as_user(app, 1, "fx@example.com")
    # Create
    payload = {"base": "EUR", "quote": "BRL", "date": "2025-01-02", "rate": "5.1234567890"}
    r1 = client.post("/fin/fx-rates", json=payload)
    assert r1.status_code == 201, r1.text

    # Update same key
    payload2 = {"base": "eur", "quote": "brl", "date": "2025-01-02", "rate": "5.50"}
    r2 = client.post("/fin/fx-rates", json=payload2)
    assert r2.status_code == 200, r2.text

    # Read range and confirm value
    r3 = client.get("/fin/fx-rates", params={"base": "EUR", "quote": "BRL", "from": "2025-01-01", "to": "2025-01-03"})
    assert r3.status_code == 200, r3.text
    data = r3.json()
    assert any(row["date"] == "2025-01-02" and Decimal(row["rate"]) == Decimal("5.50") for row in data)


def test_fx_rates_get_validations(client, app):
    _as_user(app, 1, "fx@example.com")
    # Missing/invalid range
    r = client.get("/fin/fx-rates", params={"base": "EUR", "quote": "BRL", "from": "2025-01-10", "to": "2025-01-01"})
    assert r.status_code == 422
    # base == quote
    r2 = client.get("/fin/fx-rates", params={"base": "EUR", "quote": "EUR", "from": "2025-01-01", "to": "2025-01-02"})
    assert r2.status_code == 422


def test_post_fx_rates_validations(client, app):
    _as_user(app, 1, "fx@example.com")
    # base == quote
    bad = {"base": "USD", "quote": "usd", "date": "2025-01-01", "rate": "1.0"}
    r = client.post("/fin/fx-rates", json=bad)
    assert r.status_code == 422
    # too many decimals
    bad2 = {"base": "EUR", "quote": "BRL", "date": "2025-01-01", "rate": "5.12345678901"}
    r2 = client.post("/fin/fx-rates", json=bad2)
    assert r2.status_code == 422
