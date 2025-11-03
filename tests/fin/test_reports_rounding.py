import asyncio
import datetime as dt
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.main import create_app
from app.core.security import get_current_user
from app.db.session import get_session as app_get_session
from app.models.base import Base
from app.models.user import User


DB_FILE = Path("./test_fin_reports_rounding.db")
TEST_DB_URL = f"sqlite+aiosqlite:///{DB_FILE}"


def _setup_client_and_user():
    # Fresh DB per test module (simple file-based SQLite)
    if DB_FILE.exists():
        DB_FILE.unlink()

    engine = create_async_engine(TEST_DB_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # seed user id=1
        async with async_session() as s:
            u1 = User(email="round@example.com", hashed_password="x")
            s.add(u1)
            await s.commit()

    asyncio.run(init_models())

    app = create_app()
    client = TestClient(app)

    async def _get_user1():
        return User(id=1, email="round@example.com", hashed_password="x")

    async def override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_current_user] = _get_user1
    app.dependency_overrides[app_get_session] = override_get_session

    return app, client


def test_balance_respects_jpy_exponent(tmp_path):
    app, client = _setup_client_and_user()

    # Create JPY account and a couple of transactions
    acc = client.post("/fin/accounts", json={"name": "JPY_ACC", "currency": "JPY"}).json()["id"]
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    # +100 JPY (income), -1 JPY (expense) => 99 (no decimals)
    inc_cat = client.post("/fin/categories", json={"name": "INC", "type": "INCOME"}).json()["id"]
    exp_cat = client.post("/fin/categories", json={"name": "EXP", "type": "EXPENSE"}).json()["id"]
    assert client.post("/fin/transactions", json={"account_id": acc, "category_id": inc_cat, "amount": "100", "occurred_at": now}).status_code == 201
    assert client.post("/fin/transactions", json={"account_id": acc, "category_id": exp_cat, "amount": "1", "occurred_at": now}).status_code == 201

    rb = client.get("/fin/reports/balance-by-account")
    assert rb.status_code == 200
    rows = rb.json(); by_id = { r["account_id"]: r for r in rows }
    assert by_id[acc]["currency"] == "JPY"
    assert by_id[acc]["balance"] == "99"


def test_kwd_three_decimals_in_totals():
    app, client = _setup_client_and_user()

    # Create two KWD accounts (A: target, B: temp) with 3-decimal precision
    acc = client.post("/fin/accounts", json={"name": "KWD_ACC", "currency": "KWD"}).json()["id"]
    tmp = client.post("/fin/accounts", json={"name": "KWD_TMP", "currency": "KWD"}).json()["id"]
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    # Use transfers in/out to A to bypass schema-level EUR precision;
    # CRUD valida por currency (KWD: 3 casas). Resultado líquido esperado: +1.233
    when = now
    # +1.234 into A (from TMP)
    r1 = client.post("/fin/transfers", json={
        "src_account_id": tmp,
        "dst_account_id": acc,
        "src_amount": "1.234",
        "fx_rate": "1",
        "occurred_at": when,
    })
    assert r1.status_code == 201
    # +0.001 into A
    r2 = client.post("/fin/transfers", json={
        "src_account_id": tmp,
        "dst_account_id": acc,
        "src_amount": "0.001",
        "fx_rate": "1",
        "occurred_at": when,
    })
    assert r2.status_code == 201
    # -0.002 out of A
    r3 = client.post("/fin/transfers", json={
        "src_account_id": acc,
        "dst_account_id": tmp,
        "src_amount": "0.002",
        "fx_rate": "1",
        "occurred_at": when,
    })
    assert r3.status_code == 201

    rb = client.get("/fin/reports/balance-by-account")
    assert rb.status_code == 200
    rows = rb.json(); by_id = { r["account_id"]: r for r in rows }
    assert by_id[acc]["currency"] == "KWD"
    assert by_id[acc]["balance"] == "1.233"
