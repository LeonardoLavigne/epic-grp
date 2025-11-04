from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.domain.entities.category import Category, CategoryType
from app.modules.finance.domain.repositories.categories import (
    CategoryCreateData,
    CategoryRepository,
    CategoryUpdateData,
)
from app.modules.finance.infrastructure.persistence.models.category import (
    Category as CategoryModel,
)
from app.modules.finance.infrastructure.persistence.models.transaction import (
    Transaction as TransactionModel,
)

_SYSTEM_CATEGORY_NAMES = {
    (CategoryType.INCOME, "Transfer In"),
    (CategoryType.EXPENSE, "Transfer Out"),
}


def _to_entity(model: CategoryModel) -> Category:
    return Category(
        id=model.id,
        user_id=model.user_id,
        name=model.name,
        type=CategoryType(model.type),
        active=bool(model.active),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyCategoryRepository(CategoryRepository):
    """Implementação de CategoryRepository usando SQLAlchemy assíncrono."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: CategoryCreateData) -> Category:
        model = CategoryModel(
            user_id=data.user_id,
            name=data.name,
            type=data.type.value,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def list_by_user(
        self,
        user_id: int,
        *,
        type_filter: CategoryType | None = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Category]:
        stmt = select(CategoryModel).where(CategoryModel.user_id == user_id)
        if type_filter is not None:
            stmt = stmt.where(CategoryModel.type == type_filter.value)
        stmt = stmt.offset(skip).limit(limit)
        res = await self._session.execute(stmt)
        models = res.scalars().all()
        items = [_to_entity(model) for model in models]
        if not include_inactive:
            items = [item for item in items if item.active]
        return items

    async def get_by_id(self, user_id: int, category_id: int) -> Category | None:
        res = await self._session.execute(
            select(CategoryModel).where(
                CategoryModel.id == category_id,
                CategoryModel.user_id == user_id,
            )
        )
        model = res.scalars().first()
        return _to_entity(model) if model else None

    async def update(
        self,
        user_id: int,
        category_id: int,
        data: CategoryUpdateData,
    ) -> Category | None:
        res = await self._session.execute(
            select(CategoryModel).where(
                CategoryModel.id == category_id,
                CategoryModel.user_id == user_id,
            )
        )
        model = res.scalars().first()
        if not model:
            return None
        if data.name is not None:
            model.name = data.name
        if data.type is not None:
            model.type = data.type.value
        if data.active is not None:
            model.active = data.active
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, user_id: int, category_id: int) -> bool:
        res = await self._session.execute(
            select(CategoryModel).where(
                CategoryModel.id == category_id,
                CategoryModel.user_id == user_id,
            )
        )
        model = res.scalars().first()
        if not model:
            return False
        if (CategoryType(model.type), model.name) in _SYSTEM_CATEGORY_NAMES:
            raise ValueError("cannot delete system category used by transfers")
        used = await self._session.execute(
            select(TransactionModel.id).where(
                TransactionModel.category_id == category_id,
            ).limit(1)
        )
        if used.first():
            raise ValueError("category in use")
        await self._session.delete(model)
        await self._session.commit()
        return True

    async def deactivate(self, user_id: int, category_id: int) -> Category | None:
        res = await self._session.execute(
            select(CategoryModel).where(
                CategoryModel.id == category_id,
                CategoryModel.user_id == user_id,
            )
        )
        model = res.scalars().first()
        if not model:
            return None
        if (CategoryType(model.type), model.name) in _SYSTEM_CATEGORY_NAMES:
            raise ValueError("cannot deactivate system category used by transfers")
        model.active = False
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def merge(
        self,
        user_id: int,
        src_category_id: int,
        dst_category_id: int,
    ) -> int:
        if src_category_id == dst_category_id:
            return 0
        src = await self._session.execute(
            select(CategoryModel).where(
                CategoryModel.id == src_category_id,
                CategoryModel.user_id == user_id,
            )
        )
        dst = await self._session.execute(
            select(CategoryModel).where(
                CategoryModel.id == dst_category_id,
                CategoryModel.user_id == user_id,
            )
        )
        src_model = src.scalars().first()
        dst_model = dst.scalars().first()
        if not src_model or not dst_model:
            raise ValueError("category not found")
        src_key = (CategoryType(src_model.type), src_model.name)
        dst_key = (CategoryType(dst_model.type), dst_model.name)
        if src_key in _SYSTEM_CATEGORY_NAMES or dst_key in _SYSTEM_CATEGORY_NAMES:
            raise ValueError("cannot merge system category used by transfers")
        tx_res = await self._session.execute(
            select(TransactionModel).where(
                TransactionModel.user_id == user_id,
                TransactionModel.category_id == src_category_id,
            )
        )
        tx_models = tx_res.scalars().all()
        for tx in tx_models:
            tx.category_id = dst_category_id
            self._session.add(tx)
        await self._session.commit()
        return len(tx_models)