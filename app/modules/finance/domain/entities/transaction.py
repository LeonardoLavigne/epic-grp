from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


from dataclasses import dataclass

@dataclass(slots=True)
class Transaction:
    id: int | None
    user_id: int
    account_id: int
    category_id: int | None
    amount_cents: int
    occurred_at: datetime
    description: str | None = None
    transfer_id: int | None = None
    voided: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_voided(self) -> bool:
        return self.voided
