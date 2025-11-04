import datetime as dt
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
from app.db.base import Base
from app.core.auth.persistence.models.user import User
from app.core.auth.security import get_current_user


DB_FILE = Path("./test_fin_crud_complete.db")
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
            u1 = User(email="crud15@example.com", hashed_password="x")
            u2 = User(email="crud15b@example.com", hashed_password="x")
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


def test_accounts_categories_transactions_crud_complete(client, app):
    _as_user(app, 1, "crud15@example.com")
    # Create account
    acc = client.post("/fin/accounts", json={"name": "A1", "currency": "EUR"}).json()
    acc_id = acc["id"]
    # GET account by id (to be implemented)
    r_get_acc = client.get(f"/fin/accounts/{acc_id}")
    assert r_get_acc.status_code == 200
    assert r_get_acc.json()["id"] == acc_id

    # Create category
    cat = client.post("/fin/categories", json={"name": "Food", "type": "EXPENSE"}).json()
    cat_id = cat["id"]
    r_get_cat = client.get(f"/fin/categories/{cat_id}")
    assert r_get_cat.status_code == 200
    assert r_get_cat.json()["id"] == cat_id

    # Create transaction
    now_iso = dt.datetime(2025, 1, 1, 12, tzinfo=dt.timezone.utc).isoformat()
    tx = client.post("/fin/transactions", json={"account_id": acc_id, "category_id": cat_id, "amount": "3.00", "occurred_at": now_iso, "description": "snack"}).json()
    tx_id = tx["id"]

    # GET transaction by id
    r_get_tx = client.get(f"/fin/transactions/{tx_id}")
    assert r_get_tx.status_code == 200
    assert r_get_tx.json()["id"] == tx_id

    # PATCH transaction (update description and occurred_at)
    new_when = dt.datetime(2025, 1, 2, 15, tzinfo=dt.timezone.utc).isoformat()
    r_patch = client.patch(f"/fin/transactions/{tx_id}", json={"description": "snack2", "occurred_at": new_when})
    assert r_patch.status_code == 200
    assert r_patch.json()["description"] == "snack2"

    # DELETE transaction
    r_del_tx = client.delete(f"/fin/transactions/{tx_id}")
    assert r_del_tx.status_code == 204
    r_get_tx2 = client.get(f"/fin/transactions/{tx_id}")
    assert r_get_tx2.status_code == 404

    # Attempt delete category in use (should fail while in use)
    # Recreate a tx using the category
    tx2 = client.post("/fin/transactions", json={"account_id": acc_id, "category_id": cat_id, "amount": "1.00", "occurred_at": now_iso}).json()
    r_del_cat_fail = client.delete(f"/fin/categories/{cat_id}")
    assert r_del_cat_fail.status_code in (409, 422)

    # Remove tx and then delete category
    client.delete(f"/fin/transactions/{tx2['id']}")
    r_del_cat_ok = client.delete(f"/fin/categories/{cat_id}")
    assert r_del_cat_ok.status_code == 204

    # Attempt delete account while in use (tx referencing it)
    # create tx
    new_cat = client.post("/fin/categories", json={"name": "Misc", "type": "EXPENSE"}).json()
    tx3 = client.post("/fin/transactions", json={"account_id": acc_id, "category_id": new_cat["id"], "amount": "2.00", "occurred_at": now_iso}).json()
    r_del_acc_fail = client.delete(f"/fin/accounts/{acc_id}")
    assert r_del_acc_fail.status_code in (409, 422)
    # delete tx then account
    client.delete(f"/fin/transactions/{tx3['id']}")
    r_del_acc_ok = client.delete(f"/fin/accounts/{acc_id}")
    assert r_del_acc_ok.status_code == 204


def test_transfers_get_by_id(client, app):
    _as_user(app, 1, "crud15@example.com")
    eur = client.post("/fin/accounts", json={"name": "AEUR", "currency": "EUR"}).json()["id"]
    brl = client.post("/fin/accounts", json={"name": "ABRL", "currency": "BRL"}).json()["id"]
    when = dt.datetime(2025, 1, 3, 12, tzinfo=dt.timezone.utc).isoformat()
    tr = client.post("/fin/transfers", json={"src_account_id": eur, "dst_account_id": brl, "src_amount": "10.00", "dst_amount": "50.00", "occurred_at": when}).json()["transfer"]
    tr_id = tr["id"]
    r = client.get(f"/fin/transfers/{tr_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == tr_id
    assert body["src_amount"] == "10.00"
    assert body["dst_amount"] == "50.00"

