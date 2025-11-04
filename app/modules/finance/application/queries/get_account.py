from __future__ import annotations

from dataclasses import dataclass

from app.modules.finance.domain.entities.account import Account
from app.modules.finance.domain.repositories.accounts import AccountRepository


@dataclass(slots=True)
class GetAccountQuery:
    user_id: int
    account_id: int


class GetAccountUseCase:
    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    async def execute(self, query: GetAccountQuery) -> Account | None:
        return await self._repository.get_by_id(query.user_id, query.account_id)
