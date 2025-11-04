import asyncio
from pathlib import Path
import datetime as dt
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncSession,
)

from app.main import create_app
from app.db.session import get_session as app_get_session
from app.db.base import Base
from app.core.auth.persistence.models.user import User
from app.core.auth.security import get_current_user


DB_FILE = Path("./test_fin_endpoints.db")
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
    # Ensure clean DB file each run
    if DB_FILE.exists():
        DB_FILE.unlink()

    engine = create_async_engine(TEST_DB_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # seed users
        async with async_session() as s:
            u1 = User(email="fin1@example.com", hashed_password="x")
            u2 = User(email="fin2@example.com", hashed_password="x")
            s.add_all([u1, u2])
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


def test_fin_endpoints_happy_path(client, app):
    # override current_user as user 1
    async def _get_user1():
        return User(id=1, email="fin1@example.com", hashed_password="x")

    app.dependency_overrides[get_current_user] = _get_user1

    # Create account
    r_acc = client.post("/fin/accounts", json={"name": "Main", "currency": "EUR"})
    assert r_acc.status_code == 201, r_acc.text
    acc = r_acc.json()
    assert acc["name"] == "Main"
    acc_id = acc["id"]

    # Create categories
    r_cat_income = client.post("/fin/categories", json={"name": "Salary", "type": "INCOME"})
    assert r_cat_income.status_code == 201
    cat_income_id = r_cat_income.json()["id"]

    r_cat_exp = client.post("/fin/categories", json={"name": "Food", "type": "EXPENSE"})
    assert r_cat_exp.status_code == 201
    cat_exp_id = r_cat_exp.json()["id"]

    # Create transactions
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    r_t1 = client.post(
        "/fin/transactions",
        json={
            "account_id": acc_id,
            "category_id": cat_income_id,
            "amount": "10.50",
            "occurred_at": now_iso,
            "description": "salary",
        },
    )
    assert r_t1.status_code == 201, r_t1.text
    t1 = r_t1.json()
    assert t1["amount"] == "10.50"

    r_t2 = client.post(
        "/fin/transactions",
        json={
            "account_id": acc_id,
            "category_id": cat_exp_id,
            "amount": "2.00",
            "occurred_at": now_iso,
            "description": "lunch",
        },
    )
    assert r_t2.status_code == 201
    t2 = r_t2.json()
    assert t2["amount"] == "2.00"

    # List transactions
    r_list = client.get("/fin/transactions")
    assert r_list.status_code == 200
    items = r_list.json()
    assert isinstance(items, list)
    assert len(items) >= 2

    # Update amount of t1
    r_upd = client.patch(f"/fin/transactions/{t1['id']}/amount", json={"amount": "3.00"})
    assert r_upd.status_code == 200
    upd = r_upd.json()
    assert upd["amount"] == "3.00"


def test_fin_isolation_across_users(client, app):
    # user 2
    async def _get_user2():
        return User(id=2, email="fin2@example.com", hashed_password="x")

    app.dependency_overrides[get_current_user] = _get_user2
    # Should see zero accounts initially
    r_accs = client.get("/fin/accounts")
    assert r_accs.status_code == 200
    assert r_accs.json() == []
