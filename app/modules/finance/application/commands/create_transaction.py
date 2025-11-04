from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from app.modules.finance.domain.entities.transaction import Transaction
from app.modules.finance.domain.repositories.transactions import TransactionCreateData, TransactionRepository


@dataclass(slots=True)
class CreateTransactionCommand:
    user_id: int
    account_id: int
    category_id: int | None
    amount: Decimal
    occurred_at: datetime
    description: str | None
    transfer_id: int | None


class CreateTransactionUseCase:
    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    async def execute(self, command: CreateTransactionCommand) -> Transaction:
        data = TransactionCreateData(
            user_id=command.user_id,
            account_id=command.account_id,
            category_id=command.category_id,
            amount=command.amount,
            occurred_at=command.occurred_at,
            description=command.description,
            transfer_id=command.transfer_id,
        )
        return await self._repository.create(data)