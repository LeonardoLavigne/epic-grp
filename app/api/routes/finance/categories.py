from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.finance.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.crud.finance.category import (
    create_category as _create_category,
    list_categories as _list_categories,
    update_category as _update_category,
    get_category as _get_category,
    delete_category as _delete_category,
    deactivate_category as _deactivate_category,
    merge_categories as _merge_categories,
)

router = APIRouter(prefix="/categories")


@router.get("", response_model=list[CategoryOut])
async def list_categories(
    include_inactive: bool = False,
    type: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    type_filter: str | None = None
    if type is not None:
        typ = type.upper()
        if typ not in {"INCOME", "EXPENSE"}:
            raise HTTPException(status_code=422, detail="invalid type")
        type_filter = typ
    items = await _list_categories(session, user_id=current_user.id, type=type_filter)
    if not include_inactive:
        items = [c for c in items if bool(getattr(c, "active", True))]
    return items


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await _create_category(session, user_id=current_user.id, data=data)


@router.post("/{category_id}/deactivate", response_model=CategoryOut)
async def deactivate_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        cat = await _deactivate_category(
            session, user_id=current_user.id, category_id=category_id
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.post("/merge")
async def merge_categories(
    payload: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    src_val = payload.get("src_category_id")
    dst_val = payload.get("dst_category_id")
    if src_val is None or dst_val is None:
        raise HTTPException(status_code=422, detail="invalid payload")
    try:
        src = int(str(src_val))
        dst = int(str(dst_val))
    except Exception:
        raise HTTPException(status_code=422, detail="invalid payload")
    try:
        moved = await _merge_categories(
            session, user_id=current_user.id, src_category_id=src, dst_category_id=dst
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"moved": moved}


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    cat = await _update_category(
        session, user_id=current_user.id, category_id=category_id, data=data
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.get("/{category_id}", response_model=CategoryOut)
async def get_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    cat = await _get_category(session, user_id=current_user.id, category_id=category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        ok = await _delete_category(
            session, user_id=current_user.id, category_id=category_id
        )
    except ValueError:
        raise HTTPException(status_code=409, detail="Category in use")
    if not ok:
        raise HTTPException(status_code=404, detail="Category not found")
    return None
