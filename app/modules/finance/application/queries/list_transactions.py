from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Sequence

from app.modules.finance.domain.entities.transaction import Transaction
from app.modules.finance.domain.repositories.transactions import TransactionRepository


@dataclass(slots=True)
class ListTransactionsQuery:
    user_id: int
    from_date: datetime | None = None
    to_date: datetime | None = None
    account_id: int | None = None
    category_id: int | None = None
    type_filter: str | None = None
    include_voided: bool = False


class ListTransactionsUseCase:
    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    async def execute(self, query: ListTransactionsQuery) -> List[Transaction]:
        return await self._repository.list_filtered(
            query.user_id,
            from_date=query.from_date,
            to_date=query.to_date,
            account_id=query.account_id,
            category_id=query.category_id,
            type_filter=query.type_filter,
            include_voided=query.include_voided,
        )
