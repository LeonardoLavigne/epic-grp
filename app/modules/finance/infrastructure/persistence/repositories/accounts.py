from __future__ import annotations

from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.domain.entities.account import Account, AccountStatus
from app.modules.finance.domain.repositories.accounts import (
    AccountCreateData,
    AccountRepository,
    AccountUpdateData,
)
from app.modules.finance.infrastructure.persistence.models.account import Account as AccountModel
from app.modules.finance.infrastructure.persistence.models.transaction import (
    Transaction as TransactionModel,
)


def _to_entity(model: AccountModel) -> Account:
    return Account(
        id=model.id,
        user_id=model.user_id,
        name=model.name,
        currency=model.currency,
        status=AccountStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyAccountRepository(AccountRepository):
    """Implementação de AccountRepository usando SQLAlchemy assíncrono."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: AccountCreateData) -> Account:
        model = AccountModel(
            user_id=data.user_id,
            name=data.name,
            currency=data.currency,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def list_by_user(
        self,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
        name: str | None = None,
    ) -> Sequence[Account]:
        stmt = select(AccountModel).where(AccountModel.user_id == user_id)
        if name:
            pattern = f"%{name.lower()}%"
            stmt = stmt.where(func.lower(AccountModel.name).like(pattern))
        stmt = stmt.offset(skip).limit(limit)
        res = await self._session.execute(stmt)
        return [_to_entity(model) for model in res.scalars().all()]

    async def get_by_id(self, user_id: int, account_id: int) -> Account | None:
        res = await self._session.execute(
            select(AccountModel).where(
                AccountModel.id == account_id,
                AccountModel.user_id == user_id,
            )
        )
        model = res.scalars().first()
        return _to_entity(model) if model else None

    async def update(
        self,
        user_id: int,
        account_id: int,
        data: AccountUpdateData,
    ) -> Account | None:
        res = await self._session.execute(
            select(AccountModel).where(
                AccountModel.id == account_id,
                AccountModel.user_id == user_id,
            )
        )
        model = res.scalars().first()
        if not model:
            return None
        if data.name is not None:
            model.name = data.name
        if data.currency is not None:
            model.currency = data.currency
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def close(self, user_id: int, account_id: int) -> Account | None:
        model = await self.get_by_id(user_id, account_id)
        if model is None:
            return None
        res = await self._session.execute(
            select(AccountModel).where(
                AccountModel.id == account_id,
                AccountModel.user_id == user_id,
            )
        )
        db_model = res.scalars().first()
        if not db_model:
            return None
        db_model.status = AccountStatus.CLOSED.value
        self._session.add(db_model)
        await self._session.commit()
        await self._session.refresh(db_model)
        return _to_entity(db_model)

    async def delete(self, user_id: int, account_id: int) -> bool:
        res = await self._session.execute(
            select(AccountModel).where(
                AccountModel.id == account_id,
                AccountModel.user_id == user_id,
            )
        )
        model = res.scalars().first()
        if not model:
            return False
        used = await self._session.execute(
            select(TransactionModel.id).where(
                TransactionModel.account_id == account_id,
            ).limit(1)
        )
        if used.first():
            raise ValueError("account in use")
        await self._session.delete(model)
        await self._session.commit()
        return True