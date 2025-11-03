import datetime as dt
from typing import List

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_session
from app.models.finance.fx_rate import FxRate
from app.schemas.finance.fx_rate_api import FxRateUpsert, FxRateOut

router = APIRouter(prefix="/fx-rates")


@router.post("", status_code=status.HTTP_201_CREATED)
async def upsert_fx_rate(
    payload: FxRateUpsert, response: Response, session: AsyncSession = Depends(get_session)
) -> dict:
    base = payload.base.upper()
    quote = payload.quote.upper()
    if base == quote:
        raise HTTPException(status_code=422, detail="base must differ from quote")
    # check if exists
    res = await session.execute(
        select(FxRate).where(
            FxRate.date == payload.date, FxRate.base == base, FxRate.quote == quote
        )
    )
    row = res.scalars().first()
    if row:
        row.rate_value = payload.rate
        session.add(row)
        await session.commit()
        # Override default 201 with 200 for updates
        response.status_code = status.HTTP_200_OK
        return {"status": "updated"}
    fx = FxRate(date=payload.date, base=base, quote=quote, rate_value=payload.rate)
    session.add(fx)
    await session.commit()
    return {"status": "created"}


@router.get("", response_model=List[FxRateOut])
async def list_fx_rates(
    base: str,
    quote: str,
    from_: str = Query(alias="from"),
    to: str = Query(alias="to"),
    session: AsyncSession = Depends(get_session),
) -> List[FxRateOut]:
    b = (base or "").upper()
    q = (quote or "").upper()
    if b == q:
        raise HTTPException(status_code=422, detail="base must differ from quote")
    try:
        dfrom = dt.date.fromisoformat(from_)
        dto = dt.date.fromisoformat(to)
    except Exception:
        raise HTTPException(status_code=422, detail="invalid date format")
    if dfrom > dto:
        raise HTTPException(status_code=422, detail="invalid range")
    rows = (
        await session.execute(
            select(FxRate.date, FxRate.rate_value)
            .where(
                FxRate.base == b,
                FxRate.quote == q,
                FxRate.date >= dfrom,
                FxRate.date <= dto,
            )
            .order_by(FxRate.date.asc())
        )
    ).all()
    out: list[FxRateOut] = []
    for d, r in rows:
        out.append(FxRateOut(date=d, rate=Decimal(str(r))))
    return out
