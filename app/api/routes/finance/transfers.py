from decimal import Decimal, ROUND_HALF_UP
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.models.finance.transfer import Transfer
from app.schemas.finance.transfer import TransferCreate, TransferResponse, TransferOut
from app.core.money import cents_to_amount
from app.crud.finance.transfer import create_transfer as _create_transfer
from app.crud.finance.transfer import void_transfer as _void_transfer

router = APIRouter(prefix="/transfers")


def _q2(v: Decimal | None) -> Decimal | None:
    if v is None:
        return None
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    data: TransferCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransferResponse:
    try:
        tr, tx_out, tx_in = await _create_transfer(
            session, user_id=current_user.id, data=data
        )
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
        occurred_at=tr.occurred_at
        if tr.occurred_at.tzinfo
        else tr.occurred_at.replace(tzinfo=dt.timezone.utc),
        fx_rate_2dp=_q2(Decimal(str(tr.rate_value))),
        vet_2dp=_q2(Decimal(str(tr.vet_value)) if tr.vet_value is not None else None),
        ref_rate_2dp=_q2(
            Decimal(str(tr.ref_rate_value)) if tr.ref_rate_value is not None else None
        ),
    )
    # fees derived preferencing reference FX when available
    base_fx = out.ref_rate_2dp or out.fx_rate_2dp
    if base_fx is not None and out.vet_2dp is not None and base_fx != 0:
        out.fees_per_unit_2dp = (out.vet_2dp - base_fx).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        out.fees_pct = ((out.vet_2dp / base_fx) - Decimal("1")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    return TransferResponse(
        transfer=out, src_transaction_id=tx_out.id, dst_transaction_id=tx_in.id
    )


@router.post("/{transfer_id}/void", response_model=TransferOut)
async def void_transfer(
    transfer_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransferOut:
    tr = await _void_transfer(session, user_id=current_user.id, transfer_id=transfer_id)
    if not tr:
        raise HTTPException(status_code=404, detail="Transfer not found")
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
        occurred_at=tr.occurred_at
        if tr.occurred_at.tzinfo
        else tr.occurred_at.replace(tzinfo=dt.timezone.utc),
        fx_rate_2dp=_q2(Decimal(str(tr.rate_value))),
        vet_2dp=_q2(Decimal(str(tr.vet_value)) if tr.vet_value is not None else None),
        ref_rate_2dp=_q2(
            Decimal(str(tr.ref_rate_value)) if tr.ref_rate_value is not None else None
        ),
    )
    base_fx = out.ref_rate_2dp or out.fx_rate_2dp
    if base_fx is not None and out.vet_2dp is not None and base_fx != 0:
        out.fees_per_unit_2dp = (out.vet_2dp - base_fx).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        out.fees_pct = ((out.vet_2dp / base_fx) - Decimal("1")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    return out


@router.delete("/{transfer_id}")
async def delete_transfer(
    transfer_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Hard delete is disabled to preserve audit trail
    raise HTTPException(
        status_code=405,
        detail="Deletion disabled. Use POST /fin/transfers/{id}/void instead.",
    )


@router.get("/{transfer_id}", response_model=TransferOut)
async def get_transfer(
    transfer_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    tr = (
        (
            await session.execute(
                select(Transfer).where(
                    Transfer.id == transfer_id, Transfer.user_id == current_user.id
                )
            )
        )
        .scalars()
        .first()
    )
    if not tr:
        raise HTTPException(status_code=404, detail="Transfer not found")
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
        occurred_at=tr.occurred_at
        if tr.occurred_at.tzinfo
        else tr.occurred_at.replace(tzinfo=dt.timezone.utc),
        fx_rate_2dp=_q2(Decimal(str(tr.rate_value))),
        vet_2dp=_q2(Decimal(str(tr.vet_value)) if tr.vet_value is not None else None),
        ref_rate_2dp=_q2(
            Decimal(str(tr.ref_rate_value)) if tr.ref_rate_value is not None else None
        ),
    )
    base_fx = out.ref_rate_2dp or out.fx_rate_2dp
    if base_fx is not None and out.vet_2dp is not None and base_fx != 0:
        out.fees_per_unit_2dp = (out.vet_2dp - base_fx).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        out.fees_pct = ((out.vet_2dp / base_fx) - Decimal("1")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    return out
