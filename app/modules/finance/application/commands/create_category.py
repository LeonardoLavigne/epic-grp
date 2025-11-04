from __future__ import annotations

from dataclasses import dataclass

from app.modules.finance.domain.entities.category import Category
from app.modules.finance.domain.repositories.categories import CategoryCreateData, CategoryRepository


@dataclass(slots=True)
class CreateCategoryCommand:
    user_id: int
    name: str
    type: str


class CreateCategoryUseCase:
    def __init__(self, repository: CategoryRepository) -> None:
        self._repository = repository

    async def execute(self, command: CreateCategoryCommand) -> Category:
        data = CategoryCreateData(
            user_id=command.user_id,
            name=command.name,
            type=command.type,
        )
        return await self._repository.create(data)
