from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.transaction import Transaction
from app.models.finance.account import Account
from app.models.finance.category import Category
from app.schemas.finance.transaction import TransactionCreate, TransactionUpdate
from app.core.money import amount_to_cents, validate_amount_for_currency


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
) -> Sequence[Transaction]:
    res = await session.execute(
        select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.occurred_at.desc()).offset(skip).limit(limit)
    )
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

