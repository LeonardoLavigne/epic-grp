from pydantic import BaseModel, Field, ConfigDict, field_validator


class AccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    currency: str = Field(default="EUR")

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v: str) -> str:
        v = (v or "").upper()
        if len(v) != 3:
            raise ValueError("currency must be a 3-letter code")
        return v


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    currency: str | None = None

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.upper()
        if len(v) != 3:
            raise ValueError("currency must be a 3-letter code")
        return v


class AccountOut(AccountBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

