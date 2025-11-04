import datetime as dt
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.main import create_app
from app.db.session import get_session as app_get_session
from app.db.base import Base
from app.core.auth.persistence.models.user import User
from app.core.auth.security import get_current_user


DB_FILE = Path("./test_fin_guard.db")
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
            u1 = User(email="guard@example.com", hashed_password="x")
            s.add_all([u1])
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


def test_cannot_modify_or_delete_transfer_transactions(client, app):
    _as_user(app, 1, "guard@example.com")
    # create accounts
    eur = client.post("/fin/accounts", json={"name": "EUR", "currency": "EUR"}).json()["id"]
    brl = client.post("/fin/accounts", json={"name": "BRL", "currency": "BRL"}).json()["id"]

    when = dt.datetime(2025, 1, 10, 12, tzinfo=dt.timezone.utc).isoformat()
    payload = {
        "src_account_id": eur,
        "dst_account_id": brl,
        "src_amount": "10.00",
        "fx_rate": "5.00",
        "occurred_at": when,
    }
    tr = client.post("/fin/transfers", json=payload)
    assert tr.status_code == 201, tr.text

    # fetch transactions on each account
    src_tx = client.get("/fin/transactions", params={"account_id": eur}).json()
    dst_tx = client.get("/fin/transactions", params={"account_id": brl}).json()
    assert len(src_tx) == 1 and len(dst_tx) == 1
    t_id = src_tx[0]["id"]

    # PATCH description should be blocked
    r_patch = client.patch(f"/fin/transactions/{t_id}", json={"description": "should-fail"})
    assert r_patch.status_code == 409

    # PATCH amount should be blocked
    r_amt = client.patch(f"/fin/transactions/{t_id}/amount", json={"amount": "9.00"})
    assert r_amt.status_code == 409

    # VOID should be blocked
    r_void = client.post(f"/fin/transactions/{t_id}/void")
    assert r_void.status_code == 409

    # DELETE should be blocked
    r_del = client.delete(f"/fin/transactions/{t_id}")
    assert r_del.status_code == 409

    # still present
    src_tx2 = client.get("/fin/transactions", params={"account_id": eur}).json()
    assert len(src_tx2) == 1 and src_tx2[0]["id"] == t_id

