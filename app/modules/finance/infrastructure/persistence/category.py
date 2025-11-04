from __future__ import annotations

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.domain.entities.category import Category, CategoryType
from app.modules.finance.domain.repositories.categories import (
    CategoryCreateData,
    CategoryUpdateData,
)
from app.modules.finance.infrastructure.persistence.repositories.categories import (
    SQLAlchemyCategoryRepository,
)
from app.modules.finance.interfaces.api.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
)


def _repository(session: AsyncSession) -> SQLAlchemyCategoryRepository:
    return SQLAlchemyCategoryRepository(session)


def _parse_type(value: str | None) -> CategoryType | None:
    if value is None:
        return None
    return CategoryType(value)


async def create_category(
    session: AsyncSession, *, user_id: int, data: CategoryCreate
) -> Category:
    repo = _repository(session)
    return await repo.create(
        CategoryCreateData(
            user_id=user_id,
            name=data.name,
            type=CategoryType(data.type),
        )
    )


async def get_category(
    session: AsyncSession, *, user_id: int, category_id: int
) -> Category | None:
    repo = _repository(session)
    return await repo.get_by_id(user_id, category_id)


async def delete_category(
    session: AsyncSession, *, user_id: int, category_id: int
) -> bool:
    repo = _repository(session)
    return await repo.delete(user_id, category_id)


async def deactivate_category(
    session: AsyncSession, *, user_id: int, category_id: int
) -> Category | None:
    repo = _repository(session)
    return await repo.deactivate(user_id, category_id)


async def merge_categories(
    session: AsyncSession,
    *,
    user_id: int,
    src_category_id: int,
    dst_category_id: int,
) -> int:
    repo = _repository(session)
    return await repo.merge(user_id, src_category_id, dst_category_id)


async def list_categories(
    session: AsyncSession,
    *,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    type: str | None = None,
) -> Sequence[Category]:
    repo = _repository(session)
    type_filter = _parse_type(type)
    return await repo.list_by_user(
        user_id,
        type_filter=type_filter,
        include_inactive=True,
        skip=skip,
        limit=limit,
    )


async def update_category(
    session: AsyncSession,
    *,
    user_id: int,
    category_id: int,
    data: CategoryUpdate,
) -> Category | None:
    repo = _repository(session)
    update_data = CategoryUpdateData(
        name=data.name,
        type=_parse_type(data.type),
    )
    return await repo.update(user_id, category_id, update_data)
