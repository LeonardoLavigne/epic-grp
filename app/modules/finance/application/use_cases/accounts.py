from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from app.modules.finance.domain.entities.account import Account, AccountStatus
from app.modules.finance.domain.repositories.accounts import (
    AccountCreateData,
    AccountRepository,
    AccountUpdateData,
)


@dataclass(slots=True)
class ListAccountsQuery:
    user_id: int
    include_closed: bool = False
    name: str | None = None
    skip: int = 0
    limit: int = 100


@dataclass(slots=True)
class GetAccountQuery:
    user_id: int
    account_id: int


@dataclass(slots=True)
class CreateAccountCommand:
    user_id: int
    name: str
    currency: str


@dataclass(slots=True)
class UpdateAccountCommand:
    user_id: int
    account_id: int
    name: str | None = None
    currency: str | None = None


@dataclass(slots=True)
class CloseAccountCommand:
    user_id: int
    account_id: int


@dataclass(slots=True)
class DeleteAccountCommand:
    user_id: int
    account_id: int


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


class GetAccountUseCase:
    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    async def execute(self, query: GetAccountQuery) -> Account | None:
        return await self._repository.get_by_id(query.user_id, query.account_id)


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


class UpdateAccountUseCase:
    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    async def execute(self, command: UpdateAccountCommand) -> Account | None:
        if command.name is None and command.currency is None:
            return await self._repository.get_by_id(command.user_id, command.account_id)
        data = AccountUpdateData(name=command.name, currency=command.currency)
        return await self._repository.update(command.user_id, command.account_id, data)


class CloseAccountUseCase:
    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    async def execute(self, command: CloseAccountCommand) -> Account | None:
        return await self._repository.close(command.user_id, command.account_id)


class DeleteAccountUseCase:
    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    async def execute(self, command: DeleteAccountCommand) -> bool:
        return await self._repository.delete(command.user_id, command.account_id)