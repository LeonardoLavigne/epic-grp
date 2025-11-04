from __future__ import annotations

from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.modules.finance.application.use_cases.accounts import (
    CloseAccountCommand,
    CloseAccountUseCase,
    CreateAccountCommand,
    CreateAccountUseCase,
    DeleteAccountCommand,
    DeleteAccountUseCase,
    GetAccountQuery,
    GetAccountUseCase,
    ListAccountsQuery,
    ListAccountsUseCase,
    UpdateAccountCommand,
    UpdateAccountUseCase,
)
from app.modules.finance.domain.entities.account import Account
from app.modules.finance.infrastructure.persistence.repositories.accounts import (
    SQLAlchemyAccountRepository,
)
from app.modules.finance.interfaces.api.schemas.account import (
    AccountCreate,
    AccountOut,
    AccountUpdate,
)

router = APIRouter(prefix="/accounts")


def _present(account: Account) -> AccountOut:
    if account.id is None:
        raise ValueError("Account ID cannot be None")
    return AccountOut(id=account.id, name=account.name, currency=account.currency)


def _present_many(accounts: Iterable[Account]) -> list[AccountOut]:
    return [_present(account) for account in accounts]


def _account_repository(session: AsyncSession) -> SQLAlchemyAccountRepository:
    return SQLAlchemyAccountRepository(session)


@router.get("", response_model=list[AccountOut])
async def list_accounts(
    include_closed: bool = False,
    name: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[AccountOut]:
    repository = _account_repository(session)
    use_case = ListAccountsUseCase(repository)
    accounts = await use_case.execute(
        ListAccountsQuery(
            user_id=current_user.id,
            include_closed=include_closed,
            name=name,
        )
    )
    return _present_many(accounts)


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountOut:
    repository = _account_repository(session)
    use_case = CreateAccountUseCase(repository)
    try:
        account = await use_case.execute(
            CreateAccountCommand(
                user_id=current_user.id,
                name=data.name,
                currency=data.currency,
            )
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return _present(account)


@router.post("/{account_id}/close", response_model=AccountOut)
async def close_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountOut:
    repository = _account_repository(session)
    use_case = CloseAccountUseCase(repository)
    account = await use_case.execute(
        CloseAccountCommand(user_id=current_user.id, account_id=account_id)
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return _present(account)


@router.patch("/{account_id}", response_model=AccountOut)
async def update_account(
    account_id: int,
    data: AccountUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountOut:
    repository = _account_repository(session)
    use_case = UpdateAccountUseCase(repository)
    account = await use_case.execute(
        UpdateAccountCommand(
            user_id=current_user.id,
            account_id=account_id,
            name=data.name,
            currency=data.currency,
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return _present(account)


@router.get("/{account_id}", response_model=AccountOut)
async def get_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountOut:
    repository = _account_repository(session)
    use_case = GetAccountUseCase(repository)
    account = await use_case.execute(
        GetAccountQuery(user_id=current_user.id, account_id=account_id)
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return _present(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    repository = _account_repository(session)
    use_case = DeleteAccountUseCase(repository)
    try:
        deleted = await use_case.execute(
            DeleteAccountCommand(user_id=current_user.id, account_id=account_id)
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")
    return None
