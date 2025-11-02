import asyncio
import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncSession,
)
from pathlib import Path

from app.main import create_app
from app.db.session import get_session as app_get_session
from app.models.base import Base
from app.models.user import User
from app.core.security import get_current_user


DB_FILE = Path("./test_fin_reports.db")
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
            u1 = User(email="rep1@example.com", hashed_password="x")
            s.add(u1)
            await s.commit()

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


def test_reports_balance_and_monthly_by_category(client, app):
    # act as user 1
    async def _get_user1():
        return User(id=1, email="rep1@example.com", hashed_password="x")

    app.dependency_overrides[get_current_user] = _get_user1

    # Create account
    r_acc = client.post("/fin/accounts", json={"name": "Main", "currency": "EUR"})
    assert r_acc.status_code == 201
    acc_id = r_acc.json()["id"]

    # Categories
    r_ci = client.post("/fin/categories", json={"name": "Salary", "type": "INCOME"})
    r_ce = client.post("/fin/categories", json={"name": "Food", "type": "EXPENSE"})
    assert r_ci.status_code == 201 and r_ce.status_code == 201
    cat_income = r_ci.json()["id"]
    cat_exp = r_ce.json()["id"]

    # Month now
    now = dt.datetime.now(dt.timezone.utc)
    now_iso = now.isoformat()
    # Another month (previous month)
    prev = now - dt.timedelta(days=31)
    prev_iso = prev.isoformat()

    # Create txs in current month: +100.00 (INCOME), +50.00 (INCOME), -20.00 (EXPENSE)
    assert client.post("/fin/transactions", json={"account_id": acc_id, "category_id": cat_income, "amount": "100.00", "occurred_at": now_iso}).status_code == 201
    assert client.post("/fin/transactions", json={"account_id": acc_id, "category_id": cat_income, "amount": "50.00", "occurred_at": now_iso}).status_code == 201
    assert client.post("/fin/transactions", json={"account_id": acc_id, "category_id": cat_exp, "amount": "20.00", "occurred_at": now_iso}).status_code == 201

    # One tx in previous month to ensure filtering
    assert client.post("/fin/transactions", json={"account_id": acc_id, "category_id": cat_income, "amount": "7.00", "occurred_at": prev_iso}).status_code == 201

    # Balance by account: 100 + 50 - 20 = 130.00
    rb = client.get("/fin/reports/balance-by-account")
    assert rb.status_code == 200, rb.text
    items = rb.json()
    assert len(items) >= 1
    bal = next(i for i in items if i["account_id"] == acc_id)
    assert bal["currency"] == "EUR"
    assert bal["balance"] == "130.00"

    # Monthly by category for current month
    rm = client.get(f"/fin/reports/monthly-by-category?year={now.year}&month={now.month}")
    assert rm.status_code == 200, rm.text
    rows = rm.json()
    # Expect 2 rows: INCOME 150.00 (Salary), EXPENSE -20.00 (Food)
    d = { (r["category_name"], r["type"]): r["total"] for r in rows }
    assert d[("Salary", "INCOME")] == "150.00"
    assert d[("Food", "EXPENSE")] == "-20.00"

