from decimal import Decimal
import datetime as dt
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.models.finance.account import Account
from app.models.finance.category import Category
from app.models.finance.transaction import Transaction
from app.schemas.finance.reports import BalanceByAccountItem, MonthlyByCategoryItem
from app.services.fx import get_rate, RateNotFound
from app.core.money import cents_to_amount, quantize_amount

router = APIRouter(prefix="/reports")


@router.get("/balance-by-account", response_model=List[BalanceByAccountItem])
async def balance_by_account(
    year: int | None = None,
    month: int | None = None,
    include_closed: bool = False,
    include_inactive: bool = False,
    report_currency: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[BalanceByAccountItem]:
    # Default to current UTC month when not provided
    now = dt.datetime.now(dt.timezone.utc)
    year = year or now.year
    month = month or now.month
    # Fetch accounts for user
    acc_rows = (
        (
            await session.execute(
                select(Account).where(Account.user_id == current_user.id)
            )
        )
        .scalars()
        .all()
    )
    if not include_closed:
        acc_rows = [a for a in acc_rows if getattr(a, "status", "ACTIVE") != "CLOSED"]
    # Initialize map
    totals_cents: dict[int, int] = {a.id: 0 for a in acc_rows}
    totals_report: dict[int, Decimal] | None = None
    target = (report_currency or "").upper() or None
    if target:
        totals_report = {a.id: Decimal("0") for a in acc_rows}

    # Fetch transactions with categories (exclude voided)
    tx_rows = (
        await session.execute(
            select(Transaction, Category, Account)
            .join(Account, Transaction.account_id == Account.id)
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .where(Transaction.user_id == current_user.id)
            .where(Transaction.voided.is_(False))
        )
    ).all()

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
        # IMPORTANT: For balance-by-account, category active/inactive must NOT
        # exclude the transaction from the account balance; category is a label.
        # Therefore, do not filter out inactive categories here.
        sign = 1
        if cat is not None and cat.type.upper() == "EXPENSE":
            sign = -1
        if target and acc:
            src_cur = acc.currency
            amt_dec = cents_to_amount(tx.amount_cents, src_cur)
            if src_cur.upper() == target:
                val = amt_dec * sign
            else:
                try:
                    rate = await get_rate(
                        session, date=occ.date(), base=src_cur, quote=target
                    )
                except RateNotFound:
                    raise HTTPException(
                        status_code=422, detail="missing fx rate for conversion"
                    )
                val = (amt_dec * rate) * sign
            assert totals_report is not None
            totals_report[tx.account_id] = (
                totals_report.get(tx.account_id, Decimal("0")) + val
            )
        else:
            totals_cents[tx.account_id] = totals_cents.get(tx.account_id, 0) + (
                sign * tx.amount_cents
            )

    # Present
    out: list[BalanceByAccountItem] = []
    for a in acc_rows:
        if target and totals_report is not None:
            cur = target
            bal = totals_report.get(a.id, 0.0)
            # round to target exponent
            out.append(
                BalanceByAccountItem(
                    account_id=a.id, currency=cur, balance=quantize_amount(bal, cur)
                )
            )
        else:
            out.append(
                BalanceByAccountItem(
                    account_id=a.id,
                    currency=a.currency,
                    balance=cents_to_amount(totals_cents.get(a.id, 0), a.currency),
                )
            )
    return out


@router.get("/monthly-by-category", response_model=List[MonthlyByCategoryItem])
async def monthly_by_category(
    year: int,
    month: int,
    include_closed: bool = False,
    include_inactive: bool = False,
    report_currency: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[MonthlyByCategoryItem]:
    # Fetch transactions + categories for the user
    rows = (
        await session.execute(
            select(Transaction, Category, Account)
            .join(Account, Transaction.account_id == Account.id)
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .where(Transaction.user_id == current_user.id)
            .where(Transaction.voided.is_(False))
        )
    ).all()

    # Aggregate in Python for the given year/month
    agg_cents: dict[tuple[int, str, str], int] = {}
    agg_report: dict[tuple[int, str, str], Decimal] | None = None
    target = (report_currency or "").upper() or None
    if target:
        agg_report = {}
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
        if target and acc:
            src_cur = acc.currency
            amt_dec = cents_to_amount(tx.amount_cents, src_cur)
            if src_cur.upper() == target:
                val = amt_dec * sign
            else:
                try:
                    rate = await get_rate(
                        session, date=occ.date(), base=src_cur, quote=target
                    )
                except RateNotFound:
                    raise HTTPException(
                        status_code=422, detail="missing fx rate for conversion"
                    )
                val = (amt_dec * rate) * sign
            assert agg_report is not None
            agg_report[key] = agg_report.get(key, Decimal("0")) + val
        else:
            agg_cents[key] = agg_cents.get(key, 0) + sign * tx.amount_cents

    out: list[MonthlyByCategoryItem] = []
    if target and agg_report is not None:
        for (cat_id, typ, name), dec_total in agg_report.items():
            out.append(
                MonthlyByCategoryItem(
                    category_id=cat_id,
                    category_name=name,
                    type=typ,
                    total=quantize_amount(dec_total, target),
                )
            )
    else:
        for (cat_id, typ, name), cents in agg_cents.items():
            out.append(
                MonthlyByCategoryItem(
                    category_id=cat_id,
                    category_name=name,
                    type=typ,
                    total=cents_to_amount(cents, "EUR"),
                )
            )
    return out
