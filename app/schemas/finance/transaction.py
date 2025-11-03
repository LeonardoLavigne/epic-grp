import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.core.money import validate_amount_for_currency


class TransactionBase(BaseModel):
    account_id: int
    category_id: int | None = None
    amount: Decimal = Field(gt=Decimal("0"))
    occurred_at: dt.datetime
    description: str | None = Field(default=None, max_length=1000)

    # Nota: a validação de casas decimais por moeda depende da currency da conta
    # e é feita na camada de CRUD (create/update) onde a account é conhecida.
    # Aqui mantemos apenas validações genéricas (ex.: > 0 via Field).

    @field_validator("occurred_at")
    @classmethod
    def _ensure_utc(cls, v: dt.datetime) -> dt.datetime:
        if v.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware (UTC recommended)")
        return v.astimezone(dt.timezone.utc)


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = Field(default=None)
    occurred_at: dt.datetime | None = None
    description: str | None = Field(default=None, max_length=1000)

    # Ver comentário acima: validação por moeda ocorre no CRUD; aqui pass-through.

    @field_validator("occurred_at")
    @classmethod
    def _ensure_utc(cls, v: dt.datetime | None) -> dt.datetime | None:
        if v is None:
            return None
        if v.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware (UTC recommended)")
        return v.astimezone(dt.timezone.utc)


class TransactionOut(TransactionBase):
    id: int
    from_transfer: bool = False
    transfer_id: int | None = None
    model_config = ConfigDict(from_attributes=True)
