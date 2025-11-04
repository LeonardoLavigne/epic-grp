from decimal import Decimal
import datetime as dt
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.modules.finance.infrastructure.persistence.models.account import Account
from app.modules.finance.infrastructure.persistence.models.category import Category
from app.modules.finance.infrastructure.persistence.models.transaction import Transaction
from app.modules.finance.interfaces.api.schemas.reports import BalanceByAccountItem, MonthlyByCategoryItem
from app.services.fx import get_rate, RateNotFound
from app.core.money import cents_to_amount, quantize_amount
from app.modules.finance.application.use_cases.generate_reports import (
    GenerateReportsUseCase,
    GenerateBalanceByAccountRequest,
    GenerateMonthlyByCategoryRequest,
)
from app.modules.finance.interfaces.api.schemas.reports import BalanceByAccountItem, MonthlyByCategoryItem

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

    # Use hexagonal use case
    use_case = GenerateReportsUseCase(session)
    request = GenerateBalanceByAccountRequest(
        user_id=current_user.id,
        year=year,
        month=month,
        include_closed=include_closed,
        include_inactive=include_inactive,
        report_currency=report_currency
    )
    try:
        result = await use_case.generate_balance_by_account(request)
        # Convert to schema types
        return [
            BalanceByAccountItem(
                account_id=item.account_id,
                currency=item.currency,
                balance=item.balance
            )
            for item in result
        ]
    except RateNotFound:
        raise HTTPException(
            status_code=422, detail="missing fx rate for conversion"
        )


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
    # Use hexagonal use case
    use_case = GenerateReportsUseCase(session)
    request = GenerateMonthlyByCategoryRequest(
        user_id=current_user.id,
        year=year,
        month=month,
        include_closed=include_closed,
        include_inactive=include_inactive,
        report_currency=report_currency
    )
    try:
        result = await use_case.generate_monthly_by_category(request)
        # Convert to schema types
        return [
            MonthlyByCategoryItem(
                category_id=item.category_id,
                category_name=item.category_name,
                type=item.type,
                total=item.total
            )
            for item in result
        ]
    except RateNotFound:
        raise HTTPException(
            status_code=422, detail="missing fx rate for conversion"
        )
