from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.transaction import Transaction
from app.models.finance.account import Account
from app.models.finance.category import Category
from app.schemas.finance.transaction import TransactionCreate, TransactionUpdate
from app.core.money import amount_to_cents, validate_amount_for_currency
from app.crud.errors import DomainConflict


async def _get_account_for_user(session: AsyncSession, *, user_id: int, account_id: int) -> Account | None:
    res = await session.execute(select(Account).where(Account.id == account_id, Account.user_id == user_id))
    return res.scalars().first()


async def _validate_category_for_user(session: AsyncSession, *, user_id: int, category_id: int | None) -> Category | None:
    if category_id is None:
        return None
    res = await session.execute(select(Category).where(Category.id == category_id, Category.user_id == user_id))
    return res.scalars().first()


async def create_transaction(session: AsyncSession, *, user_id: int, data: TransactionCreate) -> Transaction:
    acc = await _get_account_for_user(session, user_id=user_id, account_id=data.account_id)
    if not acc:
        raise ValueError("account not found or not owned by user")
    if acc.status and acc.status.upper() == "CLOSED":
        raise ValueError("account closed")
    cat = await _validate_category_for_user(session, user_id=user_id, category_id=data.category_id)
    if data.category_id is not None and not cat:
        raise ValueError("category not found or not owned by user")

    # Convert Decimal amount to cents based on account currency
    validate_amount_for_currency(data.amount, acc.currency)
    cents = amount_to_cents(data.amount, acc.currency)

    tx = Transaction(
        user_id=user_id,
        account_id=acc.id,
        category_id=data.category_id,
        amount_cents=cents,
        occurred_at=data.occurred_at,
        description=data.description,
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return tx


async def list_transactions(
    session: AsyncSession,
    *,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    include_voided: bool = False,
) -> Sequence[Transaction]:
    stmt = select(Transaction).where(Transaction.user_id == user_id)
    if not include_voided:
        stmt = stmt.where(Transaction.voided.is_(False))
    stmt = stmt.order_by(Transaction.occurred_at.desc()).offset(skip).limit(limit)
    res = await session.execute(stmt)
    return res.scalars().all()


async def update_transaction_amount(
    session: AsyncSession, *, user_id: int, transaction_id: int, amount: Decimal
) -> Transaction:
    res = await session.execute(
        select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id)
    )
    tx = res.scalars().first()
    if not tx:
        raise ValueError("transaction not found")
    if tx.transfer_id is not None:
        raise DomainConflict("transaction is part of a transfer; manage via /fin/transfers")

    # Need account to apply currency rules
    acc = await _get_account_for_user(session, user_id=user_id, account_id=tx.account_id)
    if not acc:
        raise ValueError("account not found for transaction")
    validate_amount_for_currency(amount, acc.currency)
    tx.amount_cents = amount_to_cents(amount, acc.currency)

    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return tx


async def get_transaction(session: AsyncSession, *, user_id: int, transaction_id: int) -> Transaction | None:
    res = await session.execute(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id))
    return res.scalars().first()


async def update_transaction(
    session: AsyncSession, *, user_id: int, transaction_id: int, data: TransactionUpdate
) -> Transaction | None:
    tx = await get_transaction(session, user_id=user_id, transaction_id=transaction_id)
    if not tx:
        return None
    if tx.transfer_id is not None:
        raise DomainConflict("transaction is part of a transfer; manage via /fin/transfers")
    # account for currency rules
    acc = await _get_account_for_user(session, user_id=user_id, account_id=tx.account_id)
    if data.amount is not None:
        validate_amount_for_currency(data.amount, acc.currency)
        tx.amount_cents = amount_to_cents(data.amount, acc.currency)
    if data.category_id is not None:
        cat = await _validate_category_for_user(session, user_id=user_id, category_id=data.category_id)
        if data.category_id is not None and not cat:
            raise ValueError("category not found or not owned by user")
        tx.category_id = data.category_id
    if data.occurred_at is not None:
        tx.occurred_at = data.occurred_at
    if data.description is not None:
        tx.description = data.description
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return tx


async def delete_transaction(session: AsyncSession, *, user_id: int, transaction_id: int) -> bool:
    tx = await get_transaction(session, user_id=user_id, transaction_id=transaction_id)
    if not tx:
        return False
    if tx.transfer_id is not None:
        raise DomainConflict("transaction is part of a transfer; manage via /fin/transfers")
    await session.delete(tx)
    await session.commit()
    return True


async def void_transaction(session: AsyncSession, *, user_id: int, transaction_id: int) -> Transaction | None:
    # Fetch by id, then check ownership to avoid edge cases with filtering
    res = await session.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = res.scalars().first()
    if not tx or tx.user_id != user_id:
        return None
    if tx.transfer_id is not None:
        raise DomainConflict("transaction is part of a transfer; manage via /fin/transfers")
    tx.voided = True
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return tx
