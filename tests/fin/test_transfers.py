import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncSession,
)
from sqlalchemy import select

from app.main import create_app
from app.db.session import get_session as app_get_session
from app.models.base import Base
from app.models.user import User
from app.models.finance.transaction import Transaction
from app.core.security import get_current_user


DB_FILE = Path("./test_fin_transfers.db")
TEST_DB_URL = f"sqlite+aiosqlite:///{DB_FILE}"


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def app():
    app = create_app()
    return app


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db(app):
    if DB_FILE.exists():
        DB_FILE.unlink()

    engine = create_async_engine(TEST_DB_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # seed users
        async with async_session() as s:
            u1 = User(email="tr1@example.com", hashed_password="x")
            u2 = User(email="tr2@example.com", hashed_password="x")
            s.add_all([u1, u2])
            await s.commit()

    import asyncio
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


def test_transfer_with_dst_amount(client, app):
    _as_user(app, 1, "tr1@example.com")
    # create accounts
    eur = client.post("/fin/accounts", json={"name": "EUR", "currency": "EUR"}).json()["id"]
    brl = client.post("/fin/accounts", json={"name": "BRL", "currency": "BRL"}).json()["id"]

    when = dt.datetime(2025, 1, 10, 12, tzinfo=dt.timezone.utc).isoformat()
    payload = {
        "src_account_id": eur,
        "dst_account_id": brl,
        "src_amount": "122.12",
        "dst_amount": "650.00",
        "occurred_at": when,
    }
    r = client.post("/fin/transfers", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["transfer"]["src_account_id"] == eur
    assert data["transfer"]["dst_account_id"] == brl
    assert data["transfer"]["src_amount"] == "122.12"
    assert data["transfer"]["dst_amount"] == "650.00"
    # transactions created
    src_tx = client.get("/fin/transactions", params={"account_id": eur}).json()
    dst_tx = client.get("/fin/transactions", params={"account_id": brl}).json()
    assert len(src_tx) == 1 and len(dst_tx) == 1


def test_transfer_with_fx_rate(client, app):
    _as_user(app, 1, "tr1@example.com")
    eur = client.post("/fin/accounts", json={"name": "EUR2", "currency": "EUR"}).json()["id"]
    brl = client.post("/fin/accounts", json={"name": "BRL2", "currency": "BRL"}).json()["id"]
    when = dt.datetime(2025, 1, 11, 12, tzinfo=dt.timezone.utc).isoformat()
    payload = {
        "src_account_id": eur,
        "dst_account_id": brl,
        "src_amount": "100.00",
        "fx_rate": "6.50",
        "occurred_at": when,
    }
    r = client.post("/fin/transfers", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["transfer"]["dst_amount"] == "650.00"


def test_transfer_same_account_or_invalid_fx(client, app):
    _as_user(app, 1, "tr1@example.com")
    eur = client.post("/fin/accounts", json={"name": "EUR3", "currency": "EUR"}).json()["id"]
    when = dt.datetime(2025, 1, 12, 12, tzinfo=dt.timezone.utc).isoformat()
    # same account
    r = client.post("/fin/transfers", json={
        "src_account_id": eur,
        "dst_account_id": eur,
        "src_amount": "10.00",
        "occurred_at": when,
        "fx_rate": "6.50",
    })
    assert r.status_code == 422
    # invalid fx_rate if used
    brl = client.post("/fin/accounts", json={"name": "BRL3", "currency": "BRL"}).json()["id"]
    r2 = client.post("/fin/transfers", json={
        "src_account_id": eur,
        "dst_account_id": brl,
        "src_amount": "10.00",
        "occurred_at": when,
        "fx_rate": "0",
    })
    assert r2.status_code == 422

