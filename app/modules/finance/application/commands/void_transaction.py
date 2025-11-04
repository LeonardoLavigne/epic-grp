from __future__ import annotations

from dataclasses import dataclass

from app.modules.finance.domain.entities.transaction import Transaction
from app.modules.finance.domain.repositories.transactions import TransactionRepository


@dataclass(slots=True)
class VoidTransactionCommand:
    user_id: int
    transaction_id: int


class VoidTransactionUseCase:
    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    async def execute(self, command: VoidTransactionCommand) -> Transaction | None:
        return await self._repository.void(command.user_id, command.transaction_id)
