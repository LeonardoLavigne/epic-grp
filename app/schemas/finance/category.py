from pydantic import BaseModel, Field, ConfigDict, field_validator


ALLOWED_TYPES = {"INCOME", "EXPENSE"}


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str

    @field_validator("type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        v = (v or "").upper()
        if v not in ALLOWED_TYPES:
            raise ValueError("type must be INCOME or EXPENSE")
        return v


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    type: str | None = None

    @field_validator("type")
    @classmethod
    def _validate_type(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.upper()
        if v not in ALLOWED_TYPES:
            raise ValueError("type must be INCOME or EXPENSE")
        return v


class CategoryOut(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

