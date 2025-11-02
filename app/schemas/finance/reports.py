from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class BalanceByAccountItem(BaseModel):
    account_id: int
    currency: str
    balance: Decimal


class MonthlyByCategoryItem(BaseModel):
    category_id: int
    category_name: str
    type: str
    total: Decimal

