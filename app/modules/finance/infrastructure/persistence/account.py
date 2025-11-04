from __future__ import annotations

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.domain.entities.account import Account
from app.modules.finance.domain.repositories.accounts import AccountCreateData, AccountUpdateData
from app.modules.finance.infrastructure.persistence.repositories.accounts import SQLAlchemyAccountRepository
from app.modules.finance.interfaces.api.schemas.account import AccountCreate, AccountUpdate


def _repository(session: AsyncSession) -> SQLAlchemyAccountRepository:
    return SQLAlchemyAccountRepository(session)


async def create_account(session: AsyncSession, *, user_id: int, data: AccountCreate) -> Account:
    repo = _repository(session)
    return await repo.create(
        AccountCreateData(user_id=user_id, name=data.name, currency=data.currency)
    )


async def list_accounts(
    session: AsyncSession,
    *,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    name: str | None = None,
) -> Sequence[Account]:
    repo = _repository(session)
    return await repo.list_by_user(user_id, skip=skip, limit=limit, name=name)


async def update_account(
    session: AsyncSession,
    *,
    user_id: int,
    account_id: int,
    data: AccountUpdate,
) -> Account | None:
    repo = _repository(session)
    return await repo.update(
        user_id,
        account_id,
        AccountUpdateData(name=data.name, currency=data.currency),
    )


async def get_account(
    session: AsyncSession,
    *,
    user_id: int,
    account_id: int,
) -> Account | None:
    repo = _repository(session)
    return await repo.get_by_id(user_id, account_id)


async def delete_account(
    session: AsyncSession,
    *,
    user_id: int,
    account_id: int,
) -> bool:
    repo = _repository(session)
    return await repo.delete(user_id, account_id)


async def close_account(
    session: AsyncSession,
    *,
    user_id: int,
    account_id: int,
) -> Account | None:
    repo = _repository(session)
    return await repo.close(user_id, account_id)
