from __future__ import annotations

from dataclasses import dataclass

from app.modules.finance.domain.entities.account import Account
from app.modules.finance.domain.repositories.accounts import AccountRepository


@dataclass(slots=True)
class CloseAccountCommand:
    user_id: int
    account_id: int


class CloseAccountUseCase:
    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    async def execute(self, command: CloseAccountCommand) -> Account | None:
        return await self._repository.close(command.user_id, command.account_id)
