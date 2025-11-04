import datetime as dt
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from pydantic import ValidationInfo


class FxRateUpsert(BaseModel):
    base: str
    quote: str
    date: dt.date
    rate: Decimal = Field(gt=Decimal("0"))

    @field_validator("base", "quote")
    @classmethod
    def _upper(cls, v: str) -> str:
        return (v or "").upper()

    @field_validator("quote")
    @classmethod
    def _neq(cls, v: str, info: ValidationInfo) -> str:
        base = (info.data or {}).get("base")
        if base and v and v.upper() == str(base).upper():
            raise ValueError("base must differ from quote")
        return v

    @field_validator("rate")
    @classmethod
    def _scale(cls, v: Decimal) -> Decimal:
        # max 10 decimal places
        s = str(v)
        if "." in s:
            frac = s.split(".", 1)[1]
            if len(frac) > 10:
                raise ValueError("rate must have at most 10 decimal places")
        return v


class FxRateOut(BaseModel):
    date: dt.date
    rate: Decimal
