from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CategoryType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


@dataclass(slots=True)
class Category:
    id: int | None
    user_id: int
    name: str
    type: CategoryType
    active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_income(self) -> bool:
        return self.type == CategoryType.INCOME

    def is_expense(self) -> bool:
        return self.type == CategoryType.EXPENSE
