from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.category import Category
from app.models.finance.transaction import Transaction
from app.schemas.finance.category import CategoryCreate, CategoryUpdate


async def create_category(session: AsyncSession, *, user_id: int, data: CategoryCreate) -> Category:
    cat = Category(user_id=user_id, name=data.name, type=data.type)
    session.add(cat)
    await session.commit()
    await session.refresh(cat)
    return cat


async def get_category(session: AsyncSession, *, user_id: int, category_id: int) -> Category | None:
    res = await session.execute(select(Category).where(Category.id == category_id, Category.user_id == user_id))
    return res.scalars().first()


async def delete_category(session: AsyncSession, *, user_id: int, category_id: int) -> bool:
    res = await session.execute(select(Category).where(Category.id == category_id, Category.user_id == user_id))
    cat = res.scalars().first()
    if not cat:
        return False
    used = await session.execute(select(Transaction.id).where(Transaction.category_id == category_id).limit(1))
    if used.first():
        raise ValueError("category in use")
    await session.delete(cat)
    await session.commit()
    return True


async def deactivate_category(session: AsyncSession, *, user_id: int, category_id: int) -> Category | None:
    cat = await get_category(session, user_id=user_id, category_id=category_id)
    if not cat:
        return None
    cat.active = False
    session.add(cat)
    await session.commit()
    await session.refresh(cat)
    return cat


async def merge_categories(session: AsyncSession, *, user_id: int, src_category_id: int, dst_category_id: int) -> int:
    # reassign transactions from src to dst
    if src_category_id == dst_category_id:
        return 0
    dst = await get_category(session, user_id=user_id, category_id=dst_category_id)
    src = await get_category(session, user_id=user_id, category_id=src_category_id)
    if not src or not dst:
        raise ValueError("category not found")
    res = await session.execute(select(Transaction).where(Transaction.user_id == user_id, Transaction.category_id == src_category_id))
    txs = res.scalars().all()
    count = 0
    for tx in txs:
        tx.category_id = dst_category_id
        session.add(tx)
        count += 1
    await session.commit()
    return count


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
