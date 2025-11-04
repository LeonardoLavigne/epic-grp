from dataclasses import dataclass
from decimal import Decimal
import datetime as dt
from typing import List, Any

from app.core.money import cents_to_amount, quantize_amount
from app.services.fx import get_rate, RateNotFound


@dataclass
class GenerateBalanceByAccountRequest:
    user_id: int
    year: int
    month: int
    include_closed: bool = False
    include_inactive: bool = False
    report_currency: str | None = None


@dataclass
class GenerateMonthlyByCategoryRequest:
    user_id: int
    year: int
    month: int
    include_closed: bool = False
    include_inactive: bool = False
    report_currency: str | None = None


@dataclass
class BalanceByAccountItem:
    account_id: int
    currency: str
    balance: Decimal


@dataclass
class MonthlyByCategoryItem:
    category_id: int
    category_name: str
    type: str
    total: Decimal


class GenerateReportsUseCase:
    """Use case for generating financial reports with complex aggregations."""

    def __init__(self, session: Any) -> None:
        self.session = session

    async def generate_balance_by_account(
        self, request: GenerateBalanceByAccountRequest
    ) -> List[BalanceByAccountItem]:
        """Generate balance by account report."""
        from app.modules.finance.infrastructure.persistence.models.account import Account
        from app.modules.finance.infrastructure.persistence.models.category import Category
        from app.modules.finance.infrastructure.persistence.models.transaction import Transaction
        from sqlalchemy import select

        # Fetch accounts for user
        acc_rows = (
            (
                await self.session.execute(
                    select(Account).where(Account.user_id == request.user_id)
                )
            )
            .scalars()
            .all()
        )
        if not request.include_closed:
            acc_rows = [a for a in acc_rows if getattr(a, "status", "ACTIVE") != "CLOSED"]

        # Initialize totals
        totals_cents: dict[int, int] = {a.id: 0 for a in acc_rows}
        totals_report: dict[int, Decimal] | None = None
        target = (request.report_currency or "").upper() or None
        if target:
            totals_report = {a.id: Decimal("0") for a in acc_rows}

        # Fetch and process transactions
        tx_rows = (
            await self.session.execute(
                select(Transaction, Category, Account)
                .join(Account, Transaction.account_id == Account.id)
                .join(Category, Transaction.category_id == Category.id, isouter=True)
                .where(Transaction.user_id == request.user_id)
                .where(Transaction.voided.is_(False))
            )
        ).all()

        for tx, cat, acc in tx_rows:
            occ = tx.occurred_at
            if occ.tzinfo is not None:
                occ = occ.astimezone(dt.timezone.utc)
            # Filter by year/month
            if occ.year != request.year or occ.month != request.month:
                continue
            # Skip closed accounts unless included
            if not request.include_closed and acc and getattr(acc, "status", "ACTIVE") == "CLOSED":
                continue

            sign = 1
            if cat is not None and cat.type.upper() == "EXPENSE":
                sign = -1

            if target and acc:
                val = await self._convert_amount(tx, acc, target, sign)
                assert totals_report is not None
                totals_report[tx.account_id] = (
                    totals_report.get(tx.account_id, Decimal("0")) + val
                )
            else:
                totals_cents[tx.account_id] = totals_cents.get(tx.account_id, 0) + (
                    sign * tx.amount_cents
                )

        # Build response
        result = []
        for a in acc_rows:
            if target and totals_report is not None:
                cur = target
                bal = totals_report.get(a.id, Decimal("0"))
                result.append(BalanceByAccountItem(
                    account_id=a.id, currency=cur, balance=quantize_amount(bal, cur)
                ))
            else:
                result.append(BalanceByAccountItem(
                    account_id=a.id,
                    currency=a.currency,
                    balance=cents_to_amount(totals_cents.get(a.id, 0), a.currency),
                ))
        return result

    async def generate_monthly_by_category(
        self, request: GenerateMonthlyByCategoryRequest
    ) -> List[MonthlyByCategoryItem]:
        """Generate monthly by category report."""
        from app.modules.finance.infrastructure.persistence.models.account import Account
        from app.modules.finance.infrastructure.persistence.models.category import Category
        from app.modules.finance.infrastructure.persistence.models.transaction import Transaction
        from sqlalchemy import select

        # Fetch transactions
        rows = (
            await self.session.execute(
                select(Transaction, Category, Account)
                .join(Account, Transaction.account_id == Account.id)
                .join(Category, Transaction.category_id == Category.id, isouter=True)
                .where(Transaction.user_id == request.user_id)
                .where(Transaction.voided.is_(False))
            )
        ).all()

        # Initialize aggregations
        agg_cents: dict[tuple[int, str, str], int] = {}
        agg_report: dict[tuple[int, str, str], Decimal] | None = None
        target = (request.report_currency or "").upper() or None
        if target:
            agg_report = {}

        for tx, cat, acc in rows:
            occ = tx.occurred_at
            if occ.tzinfo is not None:
                occ = occ.astimezone(dt.timezone.utc)
            # Filter by year/month
            if occ.year != request.year or occ.month != request.month:
                continue
            # Skip closed accounts unless included
            if not request.include_closed and acc and getattr(acc, "status", "ACTIVE") == "CLOSED":
                continue
            if cat is None:
                continue  # Skip uncategorized
            # Skip inactive categories unless included
            if not request.include_inactive and not bool(getattr(cat, "active", True)):
                continue

            key = (cat.id, cat.type.upper(), cat.name)
            sign = -1 if cat.type.upper() == "EXPENSE" else 1

            if target and acc:
                val = await self._convert_amount(tx, acc, target, sign)
                assert agg_report is not None
                agg_report[key] = agg_report.get(key, Decimal("0")) + val
            else:
                agg_cents[key] = agg_cents.get(key, 0) + sign * tx.amount_cents

        # Build response
        result = []
        if target and agg_report is not None:
            for (cat_id, typ, name), dec_total in agg_report.items():
                result.append(MonthlyByCategoryItem(
                    category_id=cat_id,
                    category_name=name,
                    type=typ,
                    total=quantize_amount(dec_total, target),
                ))
        else:
            for (cat_id, typ, name), cents in agg_cents.items():
                result.append(MonthlyByCategoryItem(
                    category_id=cat_id,
                    category_name=name,
                    type=typ,
                    total=cents_to_amount(cents, "EUR"),
                ))
        return result

    async def _convert_amount(self, tx: Any, acc: Any, target_currency: str, sign: int) -> Decimal:
        """Convert transaction amount to target currency."""
        src_cur = acc.currency
        amt_dec = cents_to_amount(tx.amount_cents, src_cur)
        if src_cur.upper() == target_currency:
            return amt_dec * sign
        else:
            rate = await get_rate(self.session, date=tx.occurred_at.date(), base=src_cur, quote=target_currency)
            return (amt_dec * rate) * sign