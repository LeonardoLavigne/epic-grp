from __future__ import annotations

from dataclasses import dataclass

from app.modules.finance.domain.entities.account import Account
from app.modules.finance.domain.repositories.accounts import AccountCreateData, AccountRepository


@dataclass(slots=True)
class CreateAccountCommand:
    user_id: int
    name: str
    currency: str


class CreateAccountUseCase:
    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    async def execute(self, command: CreateAccountCommand) -> Account:
        data = AccountCreateData(
            user_id=command.user_id,
            name=command.name,
            currency=command.currency,
        )
        return await self._repository.create(data)
