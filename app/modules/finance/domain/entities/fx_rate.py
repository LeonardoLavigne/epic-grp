from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class FxRate:
    id: int
    date: date
    base: str
    quote: str
    rate_value: Decimal
    created_at: datetime | None = None
    updated_at: datetime | None = None
