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
from app.models.base import Base
from app.models.user import User
from app.core.security import get_current_user


DB_FILE = Path("./test_fin_lifecycle.db")
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
            u1 = User(email="life1@example.com", hashed_password="x")
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


def test_close_account_and_block_new_tx(client, app):
    _as_user(app, 1, "life1@example.com")
    acc_id = client.post("/fin/accounts", json={"name": "C1", "currency": "EUR"}).json()["id"]
    r_close = client.post(f"/fin/accounts/{acc_id}/close")
    assert r_close.status_code == 200
    when = dt.datetime(2025, 1, 1, 12, tzinfo=dt.timezone.utc).isoformat()
    r_tx = client.post("/fin/transactions", json={"account_id": acc_id, "category_id": None, "amount": "1.00", "occurred_at": when})
    assert r_tx.status_code == 422


def test_deactivate_category_and_merge(client, app):
    _as_user(app, 1, "life1@example.com")
    acc_id = client.post("/fin/accounts", json={"name": "C2", "currency": "EUR"}).json()["id"]
    c1 = client.post("/fin/categories", json={"name": "Old", "type": "EXPENSE"}).json()["id"]
    c2 = client.post("/fin/categories", json={"name": "New", "type": "EXPENSE"}).json()["id"]
    when = dt.datetime(2025, 1, 1, 12, tzinfo=dt.timezone.utc).isoformat()
    client.post("/fin/transactions", json={"account_id": acc_id, "category_id": c1, "amount": "2.00", "occurred_at": when})
    # deactivate
    r_deact = client.post(f"/fin/categories/{c1}/deactivate")
    assert r_deact.status_code == 200
    # merge: move tx from c1 to c2
    r_merge = client.post("/fin/categories/merge", json={"src_category_id": c1, "dst_category_id": c2})
    assert r_merge.status_code == 200
    # delete old
    r_del_old = client.delete(f"/fin/categories/{c1}")
    assert r_del_old.status_code == 204


def test_void_transaction_and_transfer(client, app):
    _as_user(app, 1, "life1@example.com")
    acc_eur = client.post("/fin/accounts", json={"name": "C3EUR", "currency": "EUR"}).json()["id"]
    acc_brl = client.post("/fin/accounts", json={"name": "C3BRL", "currency": "BRL"}).json()["id"]
    when = dt.datetime(2025, 1, 3, 12, tzinfo=dt.timezone.utc).isoformat()
    # transaction
    tx = client.post("/fin/transactions", json={"account_id": acc_eur, "category_id": None, "amount": "1.00", "occurred_at": when}).json()
    r_void = client.post(f"/fin/transactions/{tx['id']}/void")
    assert r_void.status_code == 200
    # default listing excludes voided
    items = client.get("/fin/transactions").json()
    assert all(i["id"] != tx["id"] for i in items)
    # transfer and void
    tr = client.post("/fin/transfers", json={"src_account_id": acc_eur, "dst_account_id": acc_brl, "src_amount": "10.00", "dst_amount": "50.00", "occurred_at": when}).json()["transfer"]
    r_vt = client.post(f"/fin/transfers/{tr['id']}/void")
    assert r_vt.status_code == 200
    # the two tx from transfer should not appear in default list
    items2 = client.get("/fin/transactions").json()
    assert len(items2) == 0 or all(i["description"] not in ("Transfer Out", "Transfer In") for i in items2)

