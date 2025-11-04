from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from app.modules.finance.domain.entities.transaction import Transaction


@dataclass(slots=True)
class TransactionCreateData:
    user_id: int
    account_id: int
    category_id: int | None
    amount: Decimal
    occurred_at: datetime
    description: str | None = None
    transfer_id: int | None = None


@dataclass(slots=True)
class TransactionUpdateData:
    category_id: int | None = None
    occurred_at: datetime | None = None
    description: str | None = None


class TransactionRepository(ABC):
    """Contrato de acesso a transações financeiras."""

    @abstractmethod
    async def create(self, data: TransactionCreateData) -> Transaction:
        ...

    @abstractmethod
    async def list_by_user(
        self,
        user_id: int,
        *,
        include_voided: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Transaction]:
        ...

    @abstractmethod
    async def list_filtered(
        self,
        user_id: int,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        account_id: int | None = None,
        category_id: int | None = None,
        type_filter: str | None = None,
        include_voided: bool = False,
    ) -> Sequence[Transaction]:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: int, transaction_id: int) -> Transaction | None:
        ...

    @abstractmethod
    async def update(
        self,
        user_id: int,
        transaction_id: int,
        data: TransactionUpdateData,
    ) -> Transaction | None:
        ...

    @abstractmethod
    async def delete(self, user_id: int, transaction_id: int) -> bool:
        ...

    @abstractmethod
    async def void(self, user_id: int, transaction_id: int) -> Transaction | None:
        ...

    @abstractmethod
    async def update_amount(
        self,
        user_id: int,
        transaction_id: int,
        amount: Decimal,
    ) -> Transaction:
        ...