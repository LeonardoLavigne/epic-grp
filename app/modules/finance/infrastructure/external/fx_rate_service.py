import datetime as dt
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.infrastructure.persistence.models.fx_rate import FxRate


class RateNotFound(Exception):
    pass


async def get_rate(session: AsyncSession, *, date: dt.date, base: str, quote: str) -> Decimal:
    b = (base or "").upper()
    q = (quote or "").upper()
    if b == q:
        return Decimal("1.0")
    res = await session.execute(
        select(FxRate.rate_value).where(FxRate.date == date, FxRate.base == b, FxRate.quote == q)
    )
    value = res.scalar()
    if value is None:
        raise RateNotFound(f"rate not found for {date} {b}->{q}")
    # ensure Decimal (Numeric returns Decimal typically)
    return Decimal(str(value))

