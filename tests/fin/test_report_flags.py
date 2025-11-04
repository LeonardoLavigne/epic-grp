import datetime as dt
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
from app.db.base import Base
from app.core.auth.persistence.models.user import User
from app.core.auth.security import get_current_user


DB_FILE = Path("./test_fin_report_flags.db")
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
            u1 = User(email="flags1@example.com", hashed_password="x")
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


def _as_user(app, user_id: int, email: str):
    async def _get_user():
        return User(id=user_id, email=email, hashed_password="x")
    app.dependency_overrides[get_current_user] = _get_user


def test_reports_flags_include_closed_and_inactive(client, app):
    _as_user(app, 1, "flags1@example.com")
    # Create account and category
    acc = client.post("/fin/accounts", json={"name": "ACCX", "currency": "EUR"}).json()
    acc_id = acc["id"]
    cat = client.post("/fin/categories", json={"name": "CATX", "type": "INCOME"}).json()
    cat_id = cat["id"]

    # Add a tx for current month
    now = dt.datetime.now(dt.timezone.utc)
    now_iso = now.isoformat()
    client.post("/fin/transactions", json={"account_id": acc_id, "category_id": cat_id, "amount": "5.00", "occurred_at": now_iso})

    # Close account and deactivate category after the transaction exists
    client.post(f"/fin/accounts/{acc_id}/close")
    client.post(f"/fin/categories/{cat_id}/deactivate")

    # Balance by account: default excludes closed
    rb = client.get("/fin/reports/balance-by-account")
    assert rb.status_code == 200
    # The closed account should be filtered out
    assert all(i["account_id"] != acc_id for i in rb.json())

    # With include_closed=true → account appears
    rb2 = client.get("/fin/reports/balance-by-account", params={"include_closed": True})
    assert rb2.status_code == 200
    assert any(i["account_id"] == acc_id for i in rb2.json())

    # Monthly by category default excludes inactive categories
    rm = client.get(f"/fin/reports/monthly-by-category?year={now.year}&month={now.month}")
    assert rm.status_code == 200
    assert all(r["category_name"] != "CATX" for r in rm.json())

    # With include_inactive=true → category appears
    rm2 = client.get(
        f"/fin/reports/monthly-by-category?year={now.year}&month={now.month}&include_inactive=true&include_closed=true"
    )
    assert rm2.status_code == 200
    assert any(r["category_name"] == "CATX" for r in rm2.json())


def test_delete_transfer_returns_405_and_include_voided(client, app):
    _as_user(app, 1, "flags1@example.com")
    eur = client.post("/fin/accounts", json={"name": "ACC1", "currency": "EUR"}).json()["id"]
    brl = client.post("/fin/accounts", json={"name": "ACC2", "currency": "BRL"}).json()["id"]
    when = dt.datetime(2025, 1, 10, 12, tzinfo=dt.timezone.utc).isoformat()
    tr = client.post("/fin/transfers", json={"src_account_id": eur, "dst_account_id": brl, "src_amount": "10.00", "dst_amount": "50.00", "occurred_at": when}).json()["transfer"]
    # DELETE not allowed
    r_del = client.delete(f"/fin/transfers/{tr['id']}")
    assert r_del.status_code == 405

    # Void a transaction and ensure include_voided flag returns it
    tx = client.post("/fin/transactions", json={"account_id": eur, "category_id": None, "amount": "1.00", "occurred_at": when}).json()
    client.post(f"/fin/transactions/{tx['id']}/void")
    r_default = client.get("/fin/transactions")
    assert all(i["id"] != tx["id"] for i in r_default.json())
    r_inc = client.get("/fin/transactions", params={"include_voided": True})
    assert any(i["id"] == tx["id"] for i in r_inc.json())
