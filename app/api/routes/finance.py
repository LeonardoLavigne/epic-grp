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
from app.models.finance.transfer import Transfer
from app.schemas.finance.account import AccountCreate, AccountOut, AccountUpdate
from app.schemas.finance.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.schemas.finance.transaction import TransactionCreate, TransactionOut, TransactionUpdate
from app.schemas.finance.transfer import TransferCreate, TransferResponse, TransferOut
from app.core.money import currency_exponent, cents_to_amount
from app.schemas.finance.reports import BalanceByAccountItem, MonthlyByCategoryItem
from app.core.modules import require_module
from app.crud.finance.account import (
    create_account as _create_account,
    list_accounts as _list_accounts,
    update_account as _update_account,
    get_account as _get_account,
    delete_account as _delete_account,
    close_account as _close_account,
)
from app.crud.finance.category import (
    create_category as _create_category,
    list_categories as _list_categories,
    update_category as _update_category,
    get_category as _get_category,
    delete_category as _delete_category,
    deactivate_category as _deactivate_category,
    merge_categories as _merge_categories,
)
from app.crud.finance.transaction import (
    create_transaction as _create_transaction,
    list_transactions as _list_transactions,
    update_transaction_amount as _update_transaction_amount,
    get_transaction as _get_transaction,
    update_transaction as _update_transaction,
    delete_transaction as _delete_transaction,
)
from app.crud.finance.transaction import void_transaction as _void_transaction
from app.crud.finance.transfer import create_transfer as _create_transfer
from app.crud.finance.transfer import void_transfer as _void_transfer
from app.crud.errors import DomainConflict


router = APIRouter(prefix="/fin", tags=["finances"], dependencies=[Depends(require_module("finance"))])


def _present_tx(tx: Transaction, currency: str) -> TransactionOut:
    exp = currency_exponent(currency)
    amount = (Decimal(tx.amount_cents) / (Decimal(10) ** exp)).quantize(Decimal(1).scaleb(-exp))
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
    )


@router.get("/accounts", response_model=List[AccountOut])
async def list_accounts(
    include_closed: bool = False,
    name: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    items = await _list_accounts(session, user_id=current_user.id, name=name)
    if not include_closed:
        items = [a for a in items if (getattr(a, "status", "ACTIVE") or "ACTIVE") != "CLOSED"]
    return items


@router.post("/accounts", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await _create_account(session, user_id=current_user.id, data=data)


@router.post("/accounts/{account_id}/close", response_model=AccountOut)
async def close_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    acc = await _close_account(session, user_id=current_user.id, account_id=account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return acc


@router.patch("/accounts/{account_id}", response_model=AccountOut)
async def update_account(
    account_id: int,
    data: AccountUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    acc = await _update_account(session, user_id=current_user.id, account_id=account_id, data=data)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return acc


@router.get("/accounts/{account_id}", response_model=AccountOut)
async def get_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    acc = await _get_account(session, user_id=current_user.id, account_id=account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return acc


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        ok = await _delete_account(session, user_id=current_user.id, account_id=account_id)
    except ValueError:
        raise HTTPException(status_code=409, detail="Account in use")
    if not ok:
        raise HTTPException(status_code=404, detail="Account not found")
    return None


@router.get("/categories", response_model=List[CategoryOut])
async def list_categories(
    include_inactive: bool = False,
    type: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    type_filter: str | None = None
    if type is not None:
        typ = type.upper()
        if typ not in {"INCOME", "EXPENSE"}:
            raise HTTPException(status_code=422, detail="invalid type")
        type_filter = typ
    items = await _list_categories(session, user_id=current_user.id, type=type_filter)
    if not include_inactive:
        items = [c for c in items if bool(getattr(c, "active", True))]
    return items


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await _create_category(session, user_id=current_user.id, data=data)


@router.post("/categories/{category_id}/deactivate", response_model=CategoryOut)
async def deactivate_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    cat = await _deactivate_category(session, user_id=current_user.id, category_id=category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.post("/categories/merge")
async def merge_categories(
    payload: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        src = int(payload.get("src_category_id"))
        dst = int(payload.get("dst_category_id"))
    except Exception:
        raise HTTPException(status_code=422, detail="invalid payload")
    try:
        moved = await _merge_categories(session, user_id=current_user.id, src_category_id=src, dst_category_id=dst)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"moved": moved}


@router.patch("/categories/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    cat = await _update_category(session, user_id=current_user.id, category_id=category_id, data=data)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.get("/categories/{category_id}", response_model=CategoryOut)
async def get_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    cat = await _get_category(session, user_id=current_user.id, category_id=category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        ok = await _delete_category(session, user_id=current_user.id, category_id=category_id)
    except ValueError:
        raise HTTPException(status_code=409, detail="Category in use")
    if not ok:
        raise HTTPException(status_code=404, detail="Category not found")
    return None


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


@router.get("/transactions", response_model=List[TransactionOut])
async def list_transactions(
    from_date: str | None = None,
    to_date: str | None = None,
    account_id: int | None = None,
    category_id: int | None = None,
    type: str | None = None,
    include_voided: bool = False,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
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


@router.post("/transactions", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        tx = await _create_transaction(session, user_id=current_user.id, data=data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    acc = (await session.execute(select(Account).where(Account.id == tx.account_id))).scalars().first()
    currency = acc.currency if acc else "EUR"
    return _present_tx(tx, currency)


@router.get("/transactions/{transaction_id}", response_model=TransactionOut)
async def get_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    tx = await _get_transaction(session, user_id=current_user.id, transaction_id=transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    acc = (await session.execute(select(Account).where(Account.id == tx.account_id))).scalars().first()
    currency = acc.currency if acc else "EUR"
    return _present_tx(tx, currency)


@router.patch("/transactions/{transaction_id}", response_model=TransactionOut)
async def patch_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        tx = await _update_transaction(session, user_id=current_user.id, transaction_id=transaction_id, data=data)
    except DomainConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    acc = (await session.execute(select(Account).where(Account.id == tx.account_id))).scalars().first()
    currency = acc.currency if acc else "EUR"
    dto = _present_tx(tx, currency)
    dto.description = data.description if data.description is not None else dto.description
    return dto


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        ok = await _delete_transaction(session, user_id=current_user.id, transaction_id=transaction_id)
    except DomainConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return None


@router.patch("/transactions/{transaction_id}/amount", response_model=TransactionOut)
async def update_transaction_amount(
    transaction_id: int,
    data: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if "amount" not in data:
        raise HTTPException(status_code=422, detail="amount required")
    try:
        amount = Decimal(str(data["amount"]))
    except Exception:
        raise HTTPException(status_code=422, detail="invalid amount")
    try:
        tx = await _update_transaction_amount(session, user_id=current_user.id, transaction_id=transaction_id, amount=amount)
    except DomainConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    acc = (await session.execute(select(Account).where(Account.id == tx.account_id))).scalars().first()
    currency = acc.currency if acc else "EUR"
    return _present_tx(tx, currency)


@router.post("/transfers", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    data: TransferCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        tr, tx_out, tx_in = await _create_transfer(session, user_id=current_user.id, data=data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Present amounts and rate in Decimals according to currency
    src_amount = cents_to_amount(tr.src_amount_cents, tr.rate_base)
    dst_amount = cents_to_amount(tr.dst_amount_cents, tr.rate_quote)
    out = TransferOut(
        id=tr.id,
        src_account_id=tr.src_account_id,
        dst_account_id=tr.dst_account_id,
        src_amount=src_amount,
        dst_amount=dst_amount,
        rate_value=Decimal(str(tr.rate_value)),
        rate_base=tr.rate_base,
        rate_quote=tr.rate_quote,
        occurred_at=tr.occurred_at if tr.occurred_at.tzinfo else tr.occurred_at.replace(tzinfo=dt.timezone.utc),
    )
    return TransferResponse(transfer=out, src_transaction_id=tx_out.id, dst_transaction_id=tx_in.id)


@router.get("/transfers/{transfer_id}", response_model=TransferOut)
async def get_transfer(
    transfer_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    tr = (await session.execute(select(Transfer).where(Transfer.id == transfer_id, Transfer.user_id == current_user.id))).scalars().first()
    if not tr:
        raise HTTPException(status_code=404, detail="Transfer not found")
    src_amount = cents_to_amount(tr.src_amount_cents, tr.rate_base)
    dst_amount = cents_to_amount(tr.dst_amount_cents, tr.rate_quote)
    return TransferOut(
        id=tr.id,
        src_account_id=tr.src_account_id,
        dst_account_id=tr.dst_account_id,
        src_amount=src_amount,
        dst_amount=dst_amount,
        rate_value=Decimal(str(tr.rate_value)),
        rate_base=tr.rate_base,
        rate_quote=tr.rate_quote,
        occurred_at=tr.occurred_at if tr.occurred_at.tzinfo else tr.occurred_at.replace(tzinfo=dt.timezone.utc),
    )


@router.post("/transfers/{transfer_id}/void", response_model=TransferOut)
async def void_transfer(
    transfer_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    tr = await _void_transfer(session, user_id=current_user.id, transfer_id=transfer_id)
    if not tr:
        raise HTTPException(status_code=404, detail="Transfer not found")
    src_amount = cents_to_amount(tr.src_amount_cents, tr.rate_base)
    dst_amount = cents_to_amount(tr.dst_amount_cents, tr.rate_quote)
    return TransferOut(
        id=tr.id,
        src_account_id=tr.src_account_id,
        dst_account_id=tr.dst_account_id,
        src_amount=src_amount,
        dst_amount=dst_amount,
        rate_value=Decimal(str(tr.rate_value)),
        rate_base=tr.rate_base,
        rate_quote=tr.rate_quote,
        occurred_at=tr.occurred_at if tr.occurred_at.tzinfo else tr.occurred_at.replace(tzinfo=dt.timezone.utc),
    )


@router.post("/transactions/{transaction_id}/void", response_model=TransactionOut)
async def void_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        tx = await _void_transaction(session, user_id=current_user.id, transaction_id=transaction_id)
    except DomainConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    acc = (await session.execute(select(Account).where(Account.id == tx.account_id))).scalars().first()
    currency = acc.currency if acc else "EUR"
    return _present_tx(tx, currency)


@router.delete("/transfers/{transfer_id}")
async def delete_transfer(
    transfer_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Hard delete is disabled to preserve audit trail
    raise HTTPException(status_code=405, detail="Deletion disabled. Use POST /fin/transfers/{id}/void instead.")


@router.get("/transfers/{transfer_id}", response_model=TransferOut)
async def get_transfer(
    transfer_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    tr = (await session.execute(select(Transfer).where(Transfer.id == transfer_id, Transfer.user_id == current_user.id))).scalars().first()
    if not tr:
        raise HTTPException(status_code=404, detail="Transfer not found")
    src_amount = cents_to_amount(tr.src_amount_cents, tr.rate_base)
    dst_amount = cents_to_amount(tr.dst_amount_cents, tr.rate_quote)
    return TransferOut(
        id=tr.id,
        src_account_id=tr.src_account_id,
        dst_account_id=tr.dst_account_id,
        src_amount=src_amount,
        dst_amount=dst_amount,
        rate_value=Decimal(str(tr.rate_value)),
        rate_base=tr.rate_base,
        rate_quote=tr.rate_quote,
        occurred_at=tr.occurred_at if tr.occurred_at.tzinfo else tr.occurred_at.replace(tzinfo=dt.timezone.utc),
    )


@router.get("/reports/balance-by-account", response_model=List[BalanceByAccountItem])
async def balance_by_account(
    year: int | None = None,
    month: int | None = None,
    include_closed: bool = False,
    include_inactive: bool = False,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Default to current UTC month when not provided
    now = dt.datetime.now(dt.timezone.utc)
    year = year or now.year
    month = month or now.month
    # Fetch accounts for user
    acc_rows = (await session.execute(select(Account).where(Account.user_id == current_user.id))).scalars().all()
    if not include_closed:
        acc_rows = [a for a in acc_rows if getattr(a, "status", "ACTIVE") != "CLOSED"]
    # Initialize map
    totals: dict[int, int] = {a.id: 0 for a in acc_rows}

    # Fetch transactions with categories
    tx_rows = (await session.execute(
        select(Transaction, Category, Account)
        .join(Account, Transaction.account_id == Account.id)
        .join(Category, Transaction.category_id == Category.id, isouter=True)
        .where(Transaction.user_id == current_user.id)
    )).all()

    for tx, cat, acc in tx_rows:
        occ = tx.occurred_at
        if occ.tzinfo is not None:
            occ = occ.astimezone(dt.timezone.utc)
        # SQLite may be naive; treat as UTC
        if occ.year != year or occ.month != month:
            continue
        # skip transactions from closed accounts unless included
        if not include_closed and acc and getattr(acc, "status", "ACTIVE") == "CLOSED":
            continue
        # skip inactive categories unless included
        if not include_inactive and cat is not None and not bool(getattr(cat, "active", True)):
            continue
        sign = 1
        if cat is not None and cat.type.upper() == "EXPENSE":
            sign = -1
        totals[tx.account_id] = totals.get(tx.account_id, 0) + (sign * tx.amount_cents)

    # Present
    out: list[BalanceByAccountItem] = []
    for a in acc_rows:
        out.append(BalanceByAccountItem(account_id=a.id, currency=a.currency, balance=cents_to_amount(totals.get(a.id, 0), a.currency)))
    return out


@router.get("/reports/monthly-by-category", response_model=List[MonthlyByCategoryItem])
async def monthly_by_category(
    year: int,
    month: int,
    include_closed: bool = False,
    include_inactive: bool = False,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Fetch transactions + categories for the user
    rows = (await session.execute(
        select(Transaction, Category, Account)
        .join(Account, Transaction.account_id == Account.id)
        .join(Category, Transaction.category_id == Category.id, isouter=True)
        .where(Transaction.user_id == current_user.id)
    )).all()

    # Aggregate in Python for the given year/month
    agg: dict[tuple[int, str, str], int] = {}
    for tx, cat, acc in rows:
        occ = tx.occurred_at
        if occ.tzinfo is not None:
            occ = occ.astimezone(dt.timezone.utc)
        # SQLite may be naive; treat as UTC
        if occ.year != year or occ.month != month:
            continue
        # skip closed accounts unless included
        if not include_closed and acc and getattr(acc, "status", "ACTIVE") == "CLOSED":
            continue
        if cat is None:
            # skip uncategorized for this report
            continue
        # skip inactive categories unless included
        if not include_inactive and not bool(getattr(cat, "active", True)):
            continue
        key = (cat.id, cat.type.upper(), cat.name)
        sign = -1 if cat.type.upper() == "EXPENSE" else 1
        agg[key] = agg.get(key, 0) + sign * tx.amount_cents

    out: list[MonthlyByCategoryItem] = []
    for (cat_id, typ, name), cents in agg.items():
        # Use account currency; mixed-currency not handled yet (future work)
        # Pick first account currency seen (acc.currency not stored in key)
        # For now assume EUR as agreed default
        out.append(MonthlyByCategoryItem(category_id=cat_id, category_name=name, type=typ, total=cents_to_amount(cents, "EUR")))
    return out
