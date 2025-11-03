from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.finance.account import AccountCreate, AccountOut, AccountUpdate
from app.crud.finance.account import (
    create_account as _create_account,
    list_accounts as _list_accounts,
    update_account as _update_account,
    get_account as _get_account,
    delete_account as _delete_account,
    close_account as _close_account,
)

router = APIRouter(prefix="/accounts")


@router.get("", response_model=list[AccountOut])
async def list_accounts(
    include_closed: bool = False,
    name: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[AccountOut]:
    items = await _list_accounts(session, user_id=current_user.id, name=name)
    if not include_closed:
        items = [
            a for a in items if (getattr(a, "status", "ACTIVE") or "ACTIVE") != "CLOSED"
        ]
    return [AccountOut.from_orm(a) for a in items]


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountOut:
    account = await _create_account(session, user_id=current_user.id, data=data)
    return AccountOut.from_orm(account)


@router.post("/{account_id}/close", response_model=AccountOut)
async def close_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountOut:
    acc = await _close_account(session, user_id=current_user.id, account_id=account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountOut.from_orm(acc)


@router.patch("/{account_id}", response_model=AccountOut)
async def update_account(
    account_id: int,
    data: AccountUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountOut:
    acc = await _update_account(
        session, user_id=current_user.id, account_id=account_id, data=data
    )
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountOut.from_orm(acc)


@router.get("/{account_id}", response_model=AccountOut)
async def get_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountOut:
    acc = await _get_account(session, user_id=current_user.id, account_id=account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountOut.from_orm(acc)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        ok = await _delete_account(
            session, user_id=current_user.id, account_id=account_id
        )
    except ValueError:
        raise HTTPException(status_code=409, detail="Account in use")
    if not ok:
        raise HTTPException(status_code=404, detail="Account not found")
    return None
