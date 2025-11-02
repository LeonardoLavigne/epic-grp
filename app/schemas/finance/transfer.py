import datetime as dt
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from app.core.money import validate_amount_for_currency


class TransferCreate(BaseModel):
    src_account_id: int
    dst_account_id: int
    src_amount: Decimal = Field(gt=Decimal("0"))
    occurred_at: dt.datetime
    dst_amount: Decimal | None = None
    fx_rate: Decimal | None = None

    @field_validator("occurred_at")
    @classmethod
    def _ensure_utc(cls, v: dt.datetime) -> dt.datetime:
        if v.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        return v.astimezone(dt.timezone.utc)

    @field_validator("fx_rate")
    @classmethod
    def _fx_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("fx_rate must be > 0")
        return v


class TransferOut(BaseModel):
    id: int
    src_account_id: int
    dst_account_id: int
    src_amount: Decimal
    dst_amount: Decimal
    rate_value: Decimal
    rate_base: str
    rate_quote: str
    occurred_at: dt.datetime


class TransferResponse(BaseModel):
    transfer: TransferOut
    src_transaction_id: int
    dst_transaction_id: int

