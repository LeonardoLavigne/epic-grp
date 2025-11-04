from __future__ import annotations

from dataclasses import dataclass

from app.modules.finance.domain.entities.transaction import Transaction
from app.modules.finance.domain.repositories.transactions import TransactionRepository


@dataclass(slots=True)
class GetTransactionQuery:
    user_id: int
    transaction_id: int


class GetTransactionUseCase:
    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    async def execute(self, query: GetTransactionQuery) -> Transaction | None:
        return await self._repository.get_by_id(query.user_id, query.transaction_id)
