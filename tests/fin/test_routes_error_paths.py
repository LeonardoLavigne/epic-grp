import asyncio
import datetime as dt
from pathlib import Path

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.main import create_app
from app.db.session import get_session as app_get_session
from app.models.base import Base
from app.models.user import User
from app.core.security import get_current_user


DB_FILE = Path("./test_fin_error_paths.db")
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
def setup_db(app):
    if DB_FILE.exists():
        DB_FILE.unlink()
    engine = create_async_engine(TEST_DB_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # seed user id=1
        async with async_session() as s:
            u1 = User(email="err@example.com", hashed_password="x")
            s.add(u1)
            await s.commit()

    asyncio.run(init_models())

    async def override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[app_get_session] = override_get_session

    async def _as_user():
        return User(id=1, email="err@example.com", hashed_password="x")

    app.dependency_overrides[get_current_user] = _as_user

    yield

    async def drop_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    asyncio.run(drop_models())
    try:
        DB_FILE.unlink()
    except FileNotFoundError:
        pass


def test_accounts_filters_and_404s(client):
    # Create accounts
    a1 = client.post("/fin/accounts", json={"name": "Main", "currency": "EUR"}).json()
    a2 = client.post("/fin/accounts", json={"name": "Other", "currency": "EUR"}).json()
    # Filter by name (case-insensitive contains)
    r = client.get("/fin/accounts", params={"name": "oth"})
    assert r.status_code == 200
    names = [i["name"] for i in r.json()]
    assert names == ["Other"]
    # 404 branches
    assert client.get("/fin/accounts/9999").status_code == 404
    assert client.patch("/fin/accounts/9999", json={"name": "X"}).status_code == 404
    assert client.post("/fin/accounts/9999/close").status_code == 404


def test_delete_account_in_use_and_success(client):
    # Set up account + tx
    acc_id = client.post("/fin/accounts", json={"name": "UsedAcc", "currency": "EUR"}).json()["id"]
    cat_id = client.post("/fin/categories", json={"name": "INCX", "type": "INCOME"}).json()["id"]
    when = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    client.post("/fin/transactions", json={"account_id": acc_id, "category_id": cat_id, "amount": "1.00", "occurred_at": when})
    # Deleting in-use -> 409
    r = client.delete(f"/fin/accounts/{acc_id}")
    assert r.status_code == 409
    # Create another account not used -> delete 204
    free_id = client.post("/fin/accounts", json={"name": "FreeAcc", "currency": "EUR"}).json()["id"]
    r2 = client.delete(f"/fin/accounts/{free_id}")
    assert r2.status_code == 204


def test_categories_invalid_type_and_system_guards_and_delete_in_use(client):
    # invalid type on list
    assert client.get("/fin/categories", params={"type": "foo"}).status_code == 422

    # Create a transfer to auto-create system categories
    eur = client.post("/fin/accounts", json={"name": "A1", "currency": "EUR"}).json()["id"]
    brl = client.post("/fin/accounts", json={"name": "A2", "currency": "BRL"}).json()["id"]
    when = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    client.post("/fin/transfers", json={"src_account_id": eur, "dst_account_id": brl, "src_amount": "1.00", "fx_rate": "5.00", "occurred_at": when})

    # Find system categories
    cats = client.get("/fin/categories").json()
    sys_in = next(c for c in cats if c["name"] == "Transfer In")
    sys_out = next(c for c in cats if c["name"] == "Transfer Out")

    # Deactivate system -> 422
    assert client.post(f"/fin/categories/{sys_in['id']}/deactivate").status_code == 422
    # Delete system -> 409 (guarded as "in use" via API)
    assert client.delete(f"/fin/categories/{sys_out['id']}").status_code == 409

    # Delete in-use
    used_cat = client.post("/fin/categories", json={"name": "UsedCat", "type": "INCOME"}).json()["id"]
    client.post("/fin/transactions", json={"account_id": eur, "category_id": used_cat, "amount": "2.00", "occurred_at": when})
    assert client.delete(f"/fin/categories/{used_cat}").status_code == 409

    # Merge: invalid payload
    assert client.post("/fin/categories/merge", json={}).status_code == 422
    # Merge: same id returns moved 0
    dst = client.post("/fin/categories", json={"name": "Dst", "type": "INCOME"}).json()["id"]
    r = client.post("/fin/categories/merge", json={"src_category_id": dst, "dst_category_id": dst})
    assert r.status_code == 200 and r.json()["moved"] == 0
    # Merge: system category involved -> 422
    assert client.post("/fin/categories/merge", json={"src_category_id": sys_in["id"], "dst_category_id": dst}).status_code == 422
    # Merge: move real transactions from src to dst
    src = client.post("/fin/categories", json={"name": "SrcMov", "type": "INCOME"}).json()["id"]
    client.post("/fin/transactions", json={"account_id": eur, "category_id": src, "amount": "1.00", "occurred_at": when})
    r2 = client.post("/fin/categories/merge", json={"src_category_id": src, "dst_category_id": dst})
    assert r2.status_code == 200 and r2.json()["moved"] >= 1


def test_transactions_not_found_and_update_amount_error(client):
    # Not found paths
    assert client.get("/fin/transactions/99999").status_code == 404
    assert client.delete("/fin/categories/99999").status_code == 404
    assert client.delete("/fin/accounts/99999").status_code == 404

    # Create account/tx then amount update + error branch (too many decimals)
    acc = client.post("/fin/accounts", json={"name": "T1", "currency": "EUR"}).json()["id"]
    inc = client.post("/fin/categories", json={"name": "IN1", "type": "INCOME"}).json()["id"]
    when = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    tx = client.post("/fin/transactions", json={"account_id": acc, "category_id": inc, "amount": "3.00", "occurred_at": when}).json()
    # Too many decimals for EUR -> 422
    assert client.patch(f"/fin/transactions/{tx['id']}", json={"amount": "1.001"}).status_code == 422
    # Update amount OK
    r2 = client.patch(f"/fin/transactions/{tx['id']}/amount", json={"amount": "4.50"})
    assert r2.status_code == 200 and r2.json()["amount"] == "4.50"
    # Missing amount key -> 422
    assert client.patch(f"/fin/transactions/{tx['id']}/amount", json={}).status_code == 422
    # Invalid amount parse -> 422
    assert client.patch(f"/fin/transactions/{tx['id']}/amount", json={"amount": "abc"}).status_code == 422

    # Delete transaction from transfer -> 409
    a1 = client.post("/fin/accounts", json={"name": "X1", "currency": "EUR"}).json()["id"]
    a2 = client.post("/fin/accounts", json={"name": "X2", "currency": "EUR"}).json()["id"]
    client.post("/fin/transfers", json={"src_account_id": a1, "dst_account_id": a2, "src_amount": "1.00", "fx_rate": "1.00", "occurred_at": when})
    # Get a transfer-created tx id
    txs = client.get("/fin/transactions").json()
    t_from_transfer = next(t for t in txs if t["from_transfer"])['id']
    assert client.delete(f"/fin/transactions/{t_from_transfer}").status_code == 409

    # Update nonexistent category -> 404
    assert client.patch("/fin/categories/999999", json={"name": "Z"}).status_code == 404

    # Update account fields and verify
    acc2 = client.post("/fin/accounts", json={"name": "Upd", "currency": "EUR"}).json()["id"]
    upd = client.patch(f"/fin/accounts/{acc2}", json={"name": "Upd2", "currency": "BRL"}).json()
    assert upd["name"] == "Upd2" and upd["currency"] == "BRL"

    # Account validators (invalid currency)
    assert client.post("/fin/accounts", json={"name": "Bad", "currency": "EURO"}).status_code == 422
    assert client.patch(f"/fin/accounts/{acc2}", json={"currency": "EU"}).status_code == 422

    # list_transactions invalid filters
    assert client.get("/fin/transactions", params={"type": "foo"}).status_code == 422
    assert client.get("/fin/transactions", params={"from_date": "bad-date"}).status_code == 422
