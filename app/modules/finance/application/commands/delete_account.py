from __future__ import annotations

from dataclasses import dataclass

from app.modules.finance.domain.repositories.accounts import AccountRepository


@dataclass(slots=True)
class DeleteAccountCommand:
    user_id: int
    account_id: int


class DeleteAccountUseCase:
    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    async def execute(self, command: DeleteAccountCommand) -> bool:
        return await self._repository.delete(command.user_id, command.account_id)
