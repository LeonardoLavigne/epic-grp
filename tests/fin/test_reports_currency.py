import asyncio
import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.main import create_app
from app.db.session import get_session as app_get_session
from app.models.base import Base
from app.models.user import User
from app.modules.finance.infrastructure.persistence.models.fx_rate import FxRate
from app.core.security import get_current_user


DB_FILE = Path("./test_fin_reports_currency.db")
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
        # seed user id=1
        async with async_session() as s:
            u1 = User(email="repconv@example.com", hashed_password="x")
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


def _as_user(app, user_id: int, email: str):
    async def _get_user():
        return User(id=user_id, email=email, hashed_password="x")
    app.dependency_overrides[get_current_user] = _get_user


def test_monthly_by_category_converts_to_report_currency(client, app):
    _as_user(app, 1, "repconv@example.com")
    # Accounts
    eur = client.post("/fin/accounts", json={"name": "EUR_ACC", "currency": "EUR"}).json()["id"]
    # Categories
    inc = client.post("/fin/categories", json={"name": "INC", "type": "INCOME"}).json()["id"]
    exp = client.post("/fin/categories", json={"name": "EXP", "type": "EXPENSE"}).json()["id"]

    # Date and FX rate EUR->BRL = 5.00 on the day
    now = dt.datetime(2025, 1, 10, 12, tzinfo=dt.timezone.utc)
    async def insert_rate():
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import text
        # Direct insert via engine-bound session from app override
        # Get the session factory from the dependency override closure
        pass

    # Insert fx into DB using a short async block
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import insert
    # Use the app override to get the session factory
    async_session_factory = app.dependency_overrides[app_get_session].__closure__[0].cell_contents
    async def _seed_fx():
        async with async_session_factory() as s:  # type: AsyncSession
            fx = FxRate(date=now.date(), base="EUR", quote="BRL", rate_value=Decimal("5.00"))
            s.add(fx)
            await s.commit()
    asyncio.run(_seed_fx())

    # Create txs in EUR in target month
    when = now.isoformat()
    assert client.post("/fin/transactions", json={"account_id": eur, "category_id": inc, "amount": "100.00", "occurred_at": when}).status_code == 201
    assert client.post("/fin/transactions", json={"account_id": eur, "category_id": inc, "amount": "50.00", "occurred_at": when}).status_code == 201
    assert client.post("/fin/transactions", json={"account_id": eur, "category_id": exp, "amount": "20.00", "occurred_at": when}).status_code == 201

    r = client.get(f"/fin/reports/monthly-by-category?year={now.year}&month={now.month}&report_currency=BRL")
    assert r.status_code == 200, r.text
    rows = r.json()
    m = {(row["category_name"], row["type"]): row["total"] for row in rows}
    # 150 * 5 = 750.00; -20 * 5 = -100.00
    assert m[("INC", "INCOME")] == "750.00"
    assert m[("EXP", "EXPENSE")] == "-100.00"


def test_balance_by_account_converts_to_report_currency(client, app):
    _as_user(app, 1, "repconv@example.com")
    # One EUR account and one BRL account
    eur = client.post("/fin/accounts", json={"name": "EUR_ACC2", "currency": "EUR"}).json()["id"]
    brl = client.post("/fin/accounts", json={"name": "BRL_ACC2", "currency": "BRL"}).json()["id"]
    # Categories
    inc = client.post("/fin/categories", json={"name": "I2", "type": "INCOME"}).json()["id"]
    exp = client.post("/fin/categories", json={"name": "E2", "type": "EXPENSE"}).json()["id"]
    # FX: EUR->BRL 5.0
    day = dt.date(2025, 1, 15)
    async_session_factory = app.dependency_overrides[app_get_session].__closure__[0].cell_contents
    async def _seed_fx2():
        async with async_session_factory() as s:
            s.add(FxRate(date=day, base="EUR", quote="BRL", rate_value=Decimal("5.00")))
            await s.commit()
    asyncio.run(_seed_fx2())

    when = dt.datetime(day.year, day.month, day.day, 13, tzinfo=dt.timezone.utc).isoformat()
    # EUR +10.00, BRL +5.00
    assert client.post("/fin/transactions", json={"account_id": eur, "category_id": inc, "amount": "10.00", "occurred_at": when}).status_code == 201
    assert client.post("/fin/transactions", json={"account_id": brl, "category_id": inc, "amount": "5.00", "occurred_at": when}).status_code == 201

    r = client.get(f"/fin/reports/balance-by-account?year={day.year}&month={day.month}&report_currency=BRL")
    assert r.status_code == 200, r.text
    by_id = {row["account_id"]: row for row in r.json()}
    # Both balances expressed in BRL now
    assert by_id[eur]["currency"] == "BRL"
    assert by_id[eur]["balance"] == "50.00"
    assert by_id[brl]["currency"] == "BRL"
    assert by_id[brl]["balance"] == "5.00"


def test_reports_missing_rate_returns_422(client, app):
    _as_user(app, 1, "repconv@example.com")
    # Make a EUR account and tx but do NOT insert a rate for that day
    eur = client.post("/fin/accounts", json={"name": "EUR_ONLY", "currency": "EUR"}).json()["id"]
    inc = client.post("/fin/categories", json={"name": "I3", "type": "INCOME"}).json()["id"]
    when = dt.datetime(2025, 2, 2, 12, tzinfo=dt.timezone.utc).isoformat()
    assert client.post("/fin/transactions", json={"account_id": eur, "category_id": inc, "amount": "1.00", "occurred_at": when}).status_code == 201

    # Query with report_currency=BRL but no rate → 422
    r1 = client.get("/fin/reports/monthly-by-category?year=2025&month=2&report_currency=BRL")
    assert r1.status_code == 422
    r2 = client.get("/fin/reports/balance-by-account?year=2025&month=2&report_currency=BRL")
    assert r2.status_code == 422

