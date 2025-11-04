from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from app.modules.finance.domain.entities.account import Account, AccountStatus
from app.modules.finance.domain.repositories.accounts import AccountRepository


@dataclass(slots=True)
class ListAccountsQuery:
    user_id: int
    include_closed: bool = False
    name: str | None = None
    skip: int = 0
    limit: int = 100


class ListAccountsUseCase:
    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    async def execute(self, query: ListAccountsQuery) -> List[Account]:
        accounts: Sequence[Account] = await self._repository.list_by_user(
            query.user_id,
            skip=query.skip,
            limit=query.limit,
            name=query.name,
        )
        if query.include_closed:
            return list(accounts)
        return [account for account in accounts if account.status != AccountStatus.CLOSED]
