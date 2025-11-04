from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from app.modules.finance.domain.entities.transfer import Transfer
from app.modules.finance.domain.entities.transaction import Transaction


@dataclass(slots=True)
class TransferCreateData:
    user_id: int
    src_account_id: int
    dst_account_id: int
    src_amount_cents: int
    dst_amount_cents: int
    rate_base: str
    rate_quote: str
    rate_value: Decimal
    occurred_at: datetime
    vet_value: Decimal | None = None
    ref_rate_value: Decimal | None = None
    ref_rate_date: datetime | None = None
    ref_rate_source: str | None = None


class TransferRepository(ABC):
    """Contrato para operações de transferência e seus efeitos colaterais."""

    @abstractmethod
    async def create_with_transactions(
        self,
        data: TransferCreateData,
    ) -> tuple[Transfer, Transaction, Transaction]:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: int, transfer_id: int) -> Transfer | None:
        ...

    @abstractmethod
    async def list_by_user(
        self,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Transfer]:
        ...

    @abstractmethod
    async def void(self, user_id: int, transfer_id: int) -> Transfer | None:
        ...