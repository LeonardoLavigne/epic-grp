from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class Transfer:
    id: int
    user_id: int
    src_account_id: int
    dst_account_id: int
    src_amount_cents: int
    dst_amount_cents: int
    rate_base: str
    rate_quote: str
    rate_value: float
    occurred_at: datetime
    voided: bool = False
    vet_value: float | None = None
    ref_rate_value: float | None = None
    ref_rate_date: date | None = None
    ref_rate_source: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_voided(self) -> bool:
        return self.voided
