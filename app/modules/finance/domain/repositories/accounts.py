from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from app.modules.finance.domain.entities.account import Account


@dataclass(slots=True)
class AccountCreateData:
    user_id: int
    name: str
    currency: str


@dataclass(slots=True)
class AccountUpdateData:
    name: str | None = None
    currency: str | None = None


class AccountRepository(ABC):
    """Contrato de acesso a contas financeiras."""

    @abstractmethod
    async def create(self, data: AccountCreateData) -> Account:
        ...

    @abstractmethod
    async def list_by_user(
        self,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
        name: str | None = None,
    ) -> Sequence[Account]:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: int, account_id: int) -> Account | None:
        ...

    @abstractmethod
    async def update(
        self,
        user_id: int,
        account_id: int,
        data: AccountUpdateData,
    ) -> Account | None:
        ...

    @abstractmethod
    async def close(self, user_id: int, account_id: int) -> Account | None:
        ...

    @abstractmethod
    async def delete(self, user_id: int, account_id: int) -> bool:
        ...