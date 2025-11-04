from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.modules.finance.domain.entities.transaction import Transaction
from app.modules.finance.domain.repositories.transactions import TransactionRepository


@dataclass(slots=True)
class UpdateTransactionAmountCommand:
    user_id: int
    transaction_id: int
    amount: Decimal


class UpdateTransactionAmountUseCase:
    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    async def execute(self, command: UpdateTransactionAmountCommand) -> Transaction:
        return await self._repository.update_amount(command.user_id, command.transaction_id, command.amount)
