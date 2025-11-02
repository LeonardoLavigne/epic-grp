from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.category import Category
from app.schemas.finance.category import CategoryCreate, CategoryUpdate


async def create_category(session: AsyncSession, *, user_id: int, data: CategoryCreate) -> Category:
    cat = Category(user_id=user_id, name=data.name, type=data.type)
    session.add(cat)
    await session.commit()
    await session.refresh(cat)
    return cat


async def list_categories(session: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100) -> Sequence[Category]:
    res = await session.execute(
        select(Category).where(Category.user_id == user_id).offset(skip).limit(limit)
    )
    return res.scalars().all()


async def update_category(session: AsyncSession, *, user_id: int, category_id: int, data: CategoryUpdate) -> Category | None:
    res = await session.execute(select(Category).where(Category.id == category_id, Category.user_id == user_id))
    cat = res.scalars().first()
    if not cat:
        return None
    if data.name is not None:
        cat.name = data.name
    if data.type is not None:
        cat.type = data.type
    session.add(cat)
    await session.commit()
    await session.refresh(cat)
    return cat

