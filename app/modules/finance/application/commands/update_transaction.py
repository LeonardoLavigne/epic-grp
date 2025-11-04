from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.modules.finance.domain.entities.transaction import Transaction
from app.modules.finance.domain.repositories.transactions import TransactionRepository, TransactionUpdateData


@dataclass(slots=True)
class UpdateTransactionCommand:
    user_id: int
    transaction_id: int
    category_id: int | None = None
    occurred_at: datetime | None = None
    description: str | None = None


class UpdateTransactionUseCase:
    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    async def execute(self, command: UpdateTransactionCommand) -> Transaction | None:
        data = TransactionUpdateData(
            category_id=command.category_id,
            occurred_at=command.occurred_at,
            description=command.description,
        )
        return await self._repository.update(command.user_id, command.transaction_id, data)
