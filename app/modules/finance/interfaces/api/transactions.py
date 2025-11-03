from decimal import Decimal
import datetime as dt
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.models.finance.account import Account
from app.models.finance.category import Category
from app.models.finance.transaction import Transaction
from app.schemas.finance.transaction import (
    TransactionCreate,
    TransactionOut,
    TransactionUpdate,
)
from app.core.money import currency_exponent
from app.crud.finance.transaction import (
    create_transaction as _create_transaction,
    update_transaction_amount as _update_transaction_amount,
    get_transaction as _get_transaction,
    update_transaction as _update_transaction,
    delete_transaction as _delete_transaction,
)
from app.crud.finance.transaction import void_transaction as _void_transaction
from app.crud.errors import DomainConflict

router = APIRouter(prefix="/transactions")


def _present_tx(tx: Transaction, currency: str) -> TransactionOut:
    exp = currency_exponent(currency)
    amount = (Decimal(tx.amount_cents) / (Decimal(10) ** exp)).quantize(
        Decimal(1).scaleb(-exp)
    )
    occ = tx.occurred_at
    if occ.tzinfo is None:
        occ = occ.replace(tzinfo=dt.timezone.utc)
    else:
        occ = occ.astimezone(dt.timezone.utc)
    return TransactionOut(
        id=tx.id,
        account_id=tx.account_id,
        category_id=tx.category_id,
        amount=amount,
        occurred_at=occ,
        description=tx.description,
        from_transfer=bool(tx.transfer_id),
        transfer_id=tx.transfer_id,
    )


def _parse_query_dt(value: str | None) -> dt.datetime | None:
    if value is None:
        return None
    v = value.replace("Z", "+00:00").replace(" ", "+")
    try:
        dtv = dt.datetime.fromisoformat(v)
    except Exception:
        raise HTTPException(status_code=422, detail="invalid datetime format")
    if dtv.tzinfo is not None:
        return dtv.astimezone(dt.timezone.utc)
    return dtv.replace(tzinfo=dt.timezone.utc)


@router.get("", response_model=List[TransactionOut])
async def list_transactions(
    from_date: str | None = None,
    to_date: str | None = None,
    account_id: int | None = None,
    category_id: int | None = None,
    type: str | None = None,
    include_voided: bool = False,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[TransactionOut]:
    q = (
        select(Transaction, Account, Category)
        .join(Account, Transaction.account_id == Account.id)
        .join(Category, Transaction.category_id == Category.id, isouter=True)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.occurred_at.desc())
    )

    if from_date is not None:
        fd = _parse_query_dt(from_date)
        q = q.where(Transaction.occurred_at >= fd)
    if to_date is not None:
        td = _parse_query_dt(to_date)
        q = q.where(Transaction.occurred_at <= td)
    if account_id is not None:
        q = q.where(Transaction.account_id == account_id)
    if category_id is not None:
        q = q.where(Transaction.category_id == category_id)
    if type is not None:
        typ = type.upper()
        if typ not in {"INCOME", "EXPENSE"}:
            raise HTTPException(status_code=422, detail="invalid type")
        q = q.where(Category.type == typ)

    if not include_voided:
        q = q.where(Transaction.voided.is_(False))
    rows = (await session.execute(q)).all()

    result: list[TransactionOut] = []
    for tx, acc, cat in rows:
        currency = acc.currency if acc else "EUR"
        result.append(_present_tx(tx, currency))
    return result


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionOut:
    try:
        tx = await _create_transaction(session, user_id=current_user.id, data=data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    acc = (
        (await session.execute(select(Account).where(Account.id == tx.account_id)))
        .scalars()
        .first()
    )
    currency = acc.currency if acc else "EUR"
    return _present_tx(tx, currency)


@router.get("/{transaction_id}", response_model=TransactionOut)
async def get_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionOut:
    tx = await _get_transaction(
        session, user_id=current_user.id, transaction_id=transaction_id
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    acc = (
        (await session.execute(select(Account).where(Account.id == tx.account_id)))
        .scalars()
        .first()
    )
    currency = acc.currency if acc else "EUR"
    return _present_tx(tx, currency)


@router.patch("/{transaction_id}", response_model=TransactionOut)
async def patch_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionOut:
    try:
        tx = await _update_transaction(
            session, user_id=current_user.id, transaction_id=transaction_id, data=data
        )
    except DomainConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    acc = (
        (await session.execute(select(Account).where(Account.id == tx.account_id)))
        .scalars()
        .first()
    )
    currency = acc.currency if acc else "EUR"
    dto = _present_tx(tx, currency)
    dto.description = (
        data.description if data.description is not None else dto.description
    )
    return dto


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        ok = await _delete_transaction(
            session, user_id=current_user.id, transaction_id=transaction_id
        )
    except DomainConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return None


@router.patch("/{transaction_id}/amount", response_model=TransactionOut)
async def update_transaction_amount(
    transaction_id: int,
    data: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionOut:
    if "amount" not in data:
        raise HTTPException(status_code=422, detail="amount required")
    try:
        amount = Decimal(str(data["amount"]))
    except Exception:
        raise HTTPException(status_code=422, detail="invalid amount")
    try:
        tx = await _update_transaction_amount(
            session,
            user_id=current_user.id,
            transaction_id=transaction_id,
            amount=amount,
        )
    except DomainConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    acc = (
        (await session.execute(select(Account).where(Account.id == tx.account_id)))
        .scalars()
        .first()
    )
    currency = acc.currency if acc else "EUR"
    return _present_tx(tx, currency)


@router.post("/{transaction_id}/void", response_model=TransactionOut)
async def void_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionOut:
    try:
        tx = await _void_transaction(
            session, user_id=current_user.id, transaction_id=transaction_id
        )
    except DomainConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    acc = (
        (await session.execute(select(Account).where(Account.id == tx.account_id)))
        .scalars()
        .first()
    )
    currency = acc.currency if acc else "EUR"
    return _present_tx(tx, currency)
