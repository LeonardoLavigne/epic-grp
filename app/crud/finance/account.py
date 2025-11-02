from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.account import Account
from app.schemas.finance.account import AccountCreate, AccountUpdate


async def create_account(session: AsyncSession, *, user_id: int, data: AccountCreate) -> Account:
    acc = Account(user_id=user_id, name=data.name, currency=data.currency)
    session.add(acc)
    await session.commit()
    await session.refresh(acc)
    return acc


async def list_accounts(session: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100) -> Sequence[Account]:
    res = await session.execute(
        select(Account).where(Account.user_id == user_id).offset(skip).limit(limit)
    )
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

