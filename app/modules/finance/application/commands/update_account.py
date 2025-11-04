from __future__ import annotations

from dataclasses import dataclass

from app.modules.finance.domain.entities.account import Account
from app.modules.finance.domain.repositories.accounts import AccountRepository, AccountUpdateData


@dataclass(slots=True)
class UpdateAccountCommand:
    user_id: int
    account_id: int
    name: str | None = None
    currency: str | None = None


class UpdateAccountUseCase:
    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    async def execute(self, command: UpdateAccountCommand) -> Account | None:
        if command.name is None and command.currency is None:
            return await self._repository.get_by_id(command.user_id, command.account_id)
        data = AccountUpdateData(name=command.name, currency=command.currency)
        return await self._repository.update(command.user_id, command.account_id, data)
