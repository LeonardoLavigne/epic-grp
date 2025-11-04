from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from app.modules.finance.domain.entities.category import Category, CategoryType


@dataclass(slots=True)
class CategoryCreateData:
    user_id: int
    name: str
    type: CategoryType


@dataclass(slots=True)
class CategoryUpdateData:
    name: str | None = None
    type: CategoryType | None = None
    active: bool | None = None


class CategoryRepository(ABC):
    """Contrato de acesso às categorias financeiras."""

    @abstractmethod
    async def create(self, data: CategoryCreateData) -> Category:
        ...

    @abstractmethod
    async def list_by_user(
        self,
        user_id: int,
        *,
        type_filter: CategoryType | None = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Category]:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: int, category_id: int) -> Category | None:
        ...

    @abstractmethod
    async def update(
        self,
        user_id: int,
        category_id: int,
        data: CategoryUpdateData,
    ) -> Category | None:
        ...

    @abstractmethod
    async def delete(self, user_id: int, category_id: int) -> bool:
        ...

    @abstractmethod
    async def deactivate(self, user_id: int, category_id: int) -> Category | None:
        ...

    @abstractmethod
    async def merge(
        self,
        user_id: int,
        src_category_id: int,
        dst_category_id: int,
    ) -> int:
        ...