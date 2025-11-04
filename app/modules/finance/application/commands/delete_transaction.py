from __future__ import annotations

from dataclasses import dataclass

from app.modules.finance.domain.repositories.transactions import TransactionRepository


@dataclass(slots=True)
class DeleteTransactionCommand:
    user_id: int
    transaction_id: int


class DeleteTransactionUseCase:
    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    async def execute(self, command: DeleteTransactionCommand) -> bool:
        return await self._repository.delete(command.user_id, command.transaction_id)
