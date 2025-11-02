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

from app.main import create_app
from app.db.session import get_session as app_get_session
from app.models.base import Base
from app.models.user import User
from app.core.security import get_current_user


DB_FILE = Path("./test_fin_filters.db")
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
            u1 = User(email="flt1@example.com", hashed_password="x")
            s.add(u1)
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


def test_transactions_filters(client, app):
    async def _get_user():
        return User(id=1, email="flt1@example.com", hashed_password="x")

    app.dependency_overrides[get_current_user] = _get_user

    # account + categories
    acc_id = client.post("/fin/accounts", json={"name": "A1", "currency": "EUR"}).json()["id"]
    cat_inc = client.post("/fin/categories", json={"name": "Salary", "type": "INCOME"}).json()["id"]
    cat_exp = client.post("/fin/categories", json={"name": "Food", "type": "EXPENSE"}).json()["id"]

    day1 = dt.datetime(2025, 1, 1, 12, tzinfo=dt.timezone.utc).isoformat()
    day2 = dt.datetime(2025, 1, 2, 12, tzinfo=dt.timezone.utc).isoformat()
    day3 = dt.datetime(2025, 1, 3, 12, tzinfo=dt.timezone.utc).isoformat()

    # create txs
    client.post("/fin/transactions", json={"account_id": acc_id, "category_id": cat_inc, "amount": "10.00", "occurred_at": day1})
    client.post("/fin/transactions", json={"account_id": acc_id, "category_id": cat_exp, "amount": "5.00", "occurred_at": day2})
    client.post("/fin/transactions", json={"account_id": acc_id, "category_id": cat_inc, "amount": "7.00", "occurred_at": day3})

    # filter by date range
    r = client.get(f"/fin/transactions?from_date={day2}&to_date={day3}")
    assert r.status_code == 200
    items = r.json()
    # Expect 2 txs (day2 and day3)
    assert len(items) == 2

    # filter by type
    r2 = client.get("/fin/transactions", params={"type": "EXPENSE"})
    assert r2.status_code == 200
    exp_items = r2.json()
    assert all(i.get("amount") == "5.00" or i.get("amount") == "-5.00" for i in exp_items) or len(exp_items) == 1

    # filter by category
    r3 = client.get("/fin/transactions", params={"category_id": cat_inc})
    assert r3.status_code == 200
    inc_items = r3.json()
    assert len(inc_items) >= 2


def test_patch_invalid_amount(client, app):
    async def _get_user():
        return User(id=1, email="flt1@example.com", hashed_password="x")

    app.dependency_overrides[get_current_user] = _get_user

    acc_id = client.post("/fin/accounts", json={"name": "A2", "currency": "EUR"}).json()["id"]
    now_iso = dt.datetime(2025, 1, 1, 12, tzinfo=dt.timezone.utc).isoformat()
    tx = client.post("/fin/transactions", json={"account_id": acc_id, "category_id": None, "amount": "1.00", "occurred_at": now_iso}).json()

    r = client.patch(f"/fin/transactions/{tx['id']}/amount", json={"amount": "abc"})
    assert r.status_code == 422

