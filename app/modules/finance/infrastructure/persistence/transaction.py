from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.errors import DomainConflict
from app.modules.finance.domain.entities.transaction import Transaction
from app.modules.finance.domain.repositories.transactions import (
    TransactionCreateData,
    TransactionUpdateData,
)
from app.modules.finance.infrastructure.persistence.repositories.transactions import (
    SQLAlchemyTransactionRepository,
)
from app.modules.finance.interfaces.api.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
)


def _repository(session: AsyncSession) -> SQLAlchemyTransactionRepository:
    return SQLAlchemyTransactionRepository(session)


async def create_transaction(
    session: AsyncSession,
    *,
    user_id: int,
    data: TransactionCreate,
) -> Transaction:
    repo = _repository(session)
    return await repo.create(
        TransactionCreateData(
            user_id=user_id,
            account_id=data.account_id,
            category_id=data.category_id,
            amount=data.amount,
            occurred_at=data.occurred_at,
            description=data.description,
        )
    )


async def list_transactions(
    session: AsyncSession,
    *,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    include_voided: bool = False,
) -> Sequence[Transaction]:
    repo = _repository(session)
    return await repo.list_by_user(
        user_id,
        include_voided=include_voided,
        skip=skip,
        limit=limit,
    )


async def update_transaction_amount(
    session: AsyncSession,
    *,
    user_id: int,
    transaction_id: int,
    amount: Decimal,
) -> Transaction:
    repo = _repository(session)
    return await repo.update_amount(
        user_id=user_id,
        transaction_id=transaction_id,
        amount=amount,
    )


async def get_transaction(
    session: AsyncSession,
    *,
    user_id: int,
    transaction_id: int,
) -> Transaction | None:
    repo = _repository(session)
    return await repo.get_by_id(user_id, transaction_id)


async def update_transaction(
    session: AsyncSession,
    *,
    user_id: int,
    transaction_id: int,
    data: TransactionUpdate,
) -> Transaction | None:
    repo = _repository(session)
    if data.amount is not None:
        updated = await repo.update_amount(
            user_id=user_id,
            transaction_id=transaction_id,
            amount=Decimal(data.amount),
        )
        descr = data.description if data.description is not None else updated.description
        return Transaction(
            id=updated.id,
            user_id=updated.user_id,
            account_id=updated.account_id,
            category_id=updated.category_id if data.category_id is None else data.category_id,
            amount_cents=updated.amount_cents,
            occurred_at=data.occurred_at or updated.occurred_at,
            description=descr,
            transfer_id=updated.transfer_id,
            voided=updated.voided,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
    return await repo.update(
        user_id=user_id,
        transaction_id=transaction_id,
        data=TransactionUpdateData(
            category_id=data.category_id,
            occurred_at=data.occurred_at,
            description=data.description,
        ),
    )


async def delete_transaction(
    session: AsyncSession,
    *,
    user_id: int,
    transaction_id: int,
) -> bool:
    repo = _repository(session)
    return await repo.delete(user_id, transaction_id)


async def void_transaction(
    session: AsyncSession,
    *,
    user_id: int,
    transaction_id: int,
) -> Transaction | None:
    repo = _repository(session)
    tx = await repo.void(user_id, transaction_id)
    if tx and tx.transfer_id is not None:
        raise DomainConflict("transaction is part of a transfer; manage via /fin/transfers")
    return tx
