import asyncio
import datetime as dt
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import delete

from app.models.base import Base
from app.models.user import User
from app.crud.finance.account import create_account, list_accounts
from app.crud.finance.category import create_category
from app.crud.finance.transaction import (
    create_transaction,
    list_transactions,
    update_transaction_amount,
)
from app.schemas.finance.account import AccountCreate
from app.schemas.finance.category import CategoryCreate
from app.schemas.finance.transaction import TransactionCreate


TEST_DB_URL = "sqlite+aiosqlite:///./test_fin_crud.db"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def session(engine):
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with SessionLocal() as s:
        # Clean users between tests to avoid unique conflicts
        await s.execute(delete(User))
        await s.commit()
        # Ensure a user exists
        u = User(email="u1@example.com", hashed_password="h")
        s.add(u)
        u2 = User(email="u2@example.com", hashed_password="h")
        s.add(u2)
        await s.commit()
        await s.refresh(u)
        await s.refresh(u2)
        yield s


@pytest.mark.asyncio
async def test_fin_crud_workflow(session: AsyncSession):
    # Create account and categories for user 1
    acc = await create_account(session, user_id=1, data=AccountCreate(name="Main"))
    cat_income = await create_category(session, user_id=1, data=CategoryCreate(name="Salary", type="INCOME"))
    cat_exp = await create_category(session, user_id=1, data=CategoryCreate(name="Food", type="EXPENSE"))

    # Create transactions
    t1 = await create_transaction(
        session,
        user_id=1,
        data=TransactionCreate(account_id=acc.id, category_id=cat_income.id, amount=Decimal("10.50"), occurred_at=dt.datetime.now(dt.timezone.utc)),
    )
    assert t1.amount_cents == 1050

    t2 = await create_transaction(
        session,
        user_id=1,
        data=TransactionCreate(account_id=acc.id, category_id=cat_exp.id, amount=Decimal("2.00"), occurred_at=dt.datetime.now(dt.timezone.utc)),
    )
    assert t2.amount_cents == 200

    # List
    txs = await list_transactions(session, user_id=1)
    assert len(txs) >= 2

    # Update amount
    t1u = await update_transaction_amount(session, user_id=1, transaction_id=t1.id, amount=Decimal("3.00"))
    assert t1u.amount_cents == 300


@pytest.mark.asyncio
async def test_user_isolation(session: AsyncSession):
    # Account for user 2
    acc2 = await create_account(session, user_id=2, data=AccountCreate(name="Other"))

    # Try to create transaction for user 1 using account from user 2
    with pytest.raises(ValueError):
        await create_transaction(
            session,
            user_id=1,
            data=TransactionCreate(account_id=acc2.id, category_id=None, amount=Decimal("1.00"), occurred_at=dt.datetime.now(dt.timezone.utc)),
        )
