from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from app.modules.finance.domain.entities.category import Category
from app.modules.finance.domain.repositories.categories import CategoryRepository


@dataclass(slots=True)
class ListCategoriesQuery:
    user_id: int
    include_inactive: bool = False
    type: str | None = None


class ListCategoriesUseCase:
    def __init__(self, repository: CategoryRepository) -> None:
        self._repository = repository

    async def execute(self, query: ListCategoriesQuery) -> List[Category]:
        categories: Sequence[Category] = await self._repository.list_by_user(
            query.user_id,
            type_filter=query.type,
        )
        if query.include_inactive:
            return list(categories)
        return [category for category in categories if category.active]
