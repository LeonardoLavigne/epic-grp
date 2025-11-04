from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CLOSED = "CLOSED"


@dataclass(slots=True)
class Account:
    id: int | None
    user_id: int
    name: str
    currency: str
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_active(self) -> bool:
        return self.status == AccountStatus.ACTIVE

    def is_closed(self) -> bool:
        return self.status == AccountStatus.CLOSED
