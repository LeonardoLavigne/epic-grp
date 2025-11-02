from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.account import Account
from app.models.finance.transaction import Transaction
from app.schemas.finance.account import AccountCreate, AccountUpdate


async def create_account(session: AsyncSession, *, user_id: int, data: AccountCreate) -> Account:
    acc = Account(user_id=user_id, name=data.name, currency=data.currency)
    session.add(acc)
    await session.commit()
    await session.refresh(acc)
    return acc


async def list_accounts(
    session: AsyncSession,
    *,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    name: str | None = None,
) -> Sequence[Account]:
    q = select(Account).where(Account.user_id == user_id)
    if name:
        # case-insensitive contains filter, portable across SQLite/Postgres
        pattern = f"%{name.lower()}%"
        q = q.where(func.lower(Account.name).like(pattern))
    q = q.offset(skip).limit(limit)
    res = await session.execute(q)
    return res.scalars().all()


async def update_account(session: AsyncSession, *, user_id: int, account_id: int, data: AccountUpdate) -> Account | None:
    res = await session.execute(select(Account).where(Account.id == account_id, Account.user_id == user_id))
    acc = res.scalars().first()
    if not acc:
        return None
    if data.name is not None:
        acc.name = data.name
    if data.currency is not None:
        acc.currency = data.currency
    session.add(acc)
    await session.commit()
    await session.refresh(acc)
    return acc


async def get_account(session: AsyncSession, *, user_id: int, account_id: int) -> Account | None:
    res = await session.execute(select(Account).where(Account.id == account_id, Account.user_id == user_id))
    return res.scalars().first()


async def delete_account(session: AsyncSession, *, user_id: int, account_id: int) -> bool:
    res = await session.execute(select(Account).where(Account.id == account_id, Account.user_id == user_id))
    acc = res.scalars().first()
    if not acc:
        return False
    # check usage
    used = await session.execute(select(Transaction.id).where(Transaction.account_id == account_id).limit(1))
    if used.first():
        raise ValueError("account in use")
    await session.delete(acc)
    await session.commit()
    return True


async def close_account(session: AsyncSession, *, user_id: int, account_id: int) -> Account | None:
    acc = await get_account(session, user_id=user_id, account_id=account_id)
    if not acc:
        return None
    acc.status = "CLOSED"
    session.add(acc)
    await session.commit()
    await session.refresh(acc)
    return acc
