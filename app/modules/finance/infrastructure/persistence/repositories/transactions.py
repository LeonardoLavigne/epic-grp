from __future__ import annotations

from decimal import Decimal
from typing import Sequence, Any
from typing_extensions import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result

if TYPE_CHECKING:
    from datetime import datetime
    from app.modules.finance.infrastructure.persistence.models.account import Account as AccountModel
    from app.modules.finance.infrastructure.persistence.models.category import Category as CategoryModel

from app.core.money import amount_to_cents, validate_amount_for_currency
from app.crud.errors import DomainConflict
from app.modules.finance.domain.entities.transaction import Transaction
from app.modules.finance.domain.repositories.transactions import (
    TransactionCreateData,
    TransactionRepository,
    TransactionUpdateData,
)
from app.modules.finance.infrastructure.persistence.models.transaction import (
    Transaction as TransactionModel,
)

# Import ORM models for type checking
from app.modules.finance.infrastructure.persistence.models.account import Account as AccountModel
from app.modules.finance.infrastructure.persistence.models.category import Category as CategoryModel
from app.modules.finance.domain.entities.account import Account as AccountEntity
from app.modules.finance.domain.entities.category import Category as CategoryEntity


def _to_entity(model: TransactionModel) -> Transaction:
    return Transaction(
        id=model.id,
        user_id=model.user_id,
        account_id=model.account_id,
        category_id=model.category_id,
        amount_cents=model.amount_cents,
        occurred_at=model.occurred_at,
        description=model.description,
        transfer_id=model.transfer_id,
        voided=bool(model.voided),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyTransactionRepository(TransactionRepository):
    """Implementação do contrato de transações usando SQLAlchemy assíncrono."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_account(
        self,
        user_id: int,
        account_id: int,
    ) -> AccountModel | None:
        result = await self._session.execute(
            select(AccountModel).where(
                AccountModel.id == account_id,
                AccountModel.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def _validate_category(
        self,
        user_id: int,
        category_id: int | None,
    ) -> CategoryModel | None:
        if category_id is None:
            return None
        result = await self._session.execute(
            select(CategoryModel).where(
                CategoryModel.id == category_id,
                CategoryModel.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def create(self, data: TransactionCreateData) -> Transaction:
        account: AccountModel | None = await self._get_account(data.user_id, data.account_id)
        if not account:
            raise ValueError("account not found or not owned by user")
        if getattr(account, "status", None) and str(account.status).upper() == "CLOSED":
            raise ValueError("account closed")

        category: CategoryModel | None = await self._validate_category(data.user_id, data.category_id)
        if data.category_id is not None and not category:
            raise ValueError("category not found or not owned by user")

        validate_amount_for_currency(data.amount, account.currency)
        cents = amount_to_cents(data.amount, account.currency)

        orm_model = TransactionModel(
            user_id=data.user_id,
            account_id=data.account_id,
            category_id=data.category_id,
            amount_cents=cents,
            occurred_at=data.occurred_at,
            description=data.description,
            transfer_id=data.transfer_id,
        )
        self._session.add(orm_model)
        await self._session.commit()
        await self._session.refresh(orm_model)
        return _to_entity(orm_model)

    async def list_by_user(
        self,
        user_id: int,
        *,
        include_voided: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Transaction]:
        stmt = select(TransactionModel).where(TransactionModel.user_id == user_id)
        if not include_voided:
            stmt = stmt.where(TransactionModel.voided.is_(False))
        stmt = stmt.order_by(TransactionModel.occurred_at.desc()).offset(skip).limit(limit)
        res = await self._session.execute(stmt)
        return [_to_entity(model) for model in res.scalars().all()]

    async def list_filtered(
        self,
        user_id: int,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        account_id: int | None = None,
        category_id: int | None = None,
        type_filter: str | None = None,
        include_voided: bool = False,
    ) -> Sequence[Transaction]:
        stmt = (
            select(TransactionModel)
            .join(AccountModel, TransactionModel.account_id == AccountModel.id)
            .join(CategoryModel, TransactionModel.category_id == CategoryModel.id, isouter=True)
            .where(TransactionModel.user_id == user_id)
        )
        if from_date is not None:
            stmt = stmt.where(TransactionModel.occurred_at >= from_date)
        if to_date is not None:
            stmt = stmt.where(TransactionModel.occurred_at <= to_date)
        if account_id is not None:
            stmt = stmt.where(TransactionModel.account_id == account_id)
        if category_id is not None:
            stmt = stmt.where(TransactionModel.category_id == category_id)
        if type_filter is not None:
            stmt = stmt.where(CategoryModel.type == type_filter)
        if not include_voided:
            stmt = stmt.where(TransactionModel.voided.is_(False))
        stmt = stmt.order_by(TransactionModel.occurred_at.desc())
        res = await self._session.execute(stmt)
        return [_to_entity(model) for model in res.scalars().all()]

    async def get_by_id(self, user_id: int, transaction_id: int) -> Transaction | None:
        res: Result = await self._session.execute(
            select(TransactionModel).where(
                TransactionModel.id == transaction_id,
                TransactionModel.user_id == user_id,
            )
        )
        model = res.scalars().first()
        return _to_entity(model) if model else None

    async def update(
        self,
        user_id: int,
        transaction_id: int,
        data: TransactionUpdateData,
    ) -> Transaction | None:
        res: Result = await self._session.execute(
            select(TransactionModel).where(
                TransactionModel.id == transaction_id,
                TransactionModel.user_id == user_id,
            )
        )
        model = res.scalars().first()
        if model is None:
            return None
        if model.transfer_id is not None:
            raise DomainConflict("transaction is part of a transfer; manage via /fin/transfers")

        if data.category_id is not None:
            category: CategoryModel | None = await self._validate_category(user_id, data.category_id)
            if data.category_id is not None and not category:
                raise ValueError("category not found or not owned by user")
            model.category_id = data.category_id
        if data.occurred_at is not None:
            model.occurred_at = data.occurred_at
        if data.description is not None:
            model.description = data.description

        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, user_id: int, transaction_id: int) -> bool:
        model: Result = await self._session.execute(
            select(TransactionModel).where(
                TransactionModel.id == transaction_id,
                TransactionModel.user_id == user_id,
            )
        )
        db_model = model.scalars().first()
        if db_model is None:
            return False
        if db_model.transfer_id is not None:
            raise DomainConflict("transaction is part of a transfer; manage via /fin/transfers")
        await self._session.delete(db_model)
        await self._session.commit()
        return True

    async def void(self, user_id: int, transaction_id: int) -> Transaction | None:
        res: Result = await self._session.execute(
            select(TransactionModel).where(TransactionModel.id == transaction_id)
        )
        model = res.scalars().first()
        if model is None or model.user_id != user_id:
            return None
        if model.transfer_id is not None:
            raise DomainConflict("transaction is part of a transfer; manage via /fin/transfers")
        model.voided = True
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update_amount(
        self,
        user_id: int,
        transaction_id: int,
        amount: Decimal,
    ) -> Transaction:
        res: Result = await self._session.execute(
            select(TransactionModel).where(
                TransactionModel.id == transaction_id,
                TransactionModel.user_id == user_id,
            )
        )
        model = res.scalars().first()
        if model is None:
            raise ValueError("transaction not found")
        if model.transfer_id is not None:
            raise DomainConflict("transaction is part of a transfer; manage via /fin/transfers")

        account: AccountModel | None = await self._get_account(user_id, model.account_id)
        if account is None:
            raise ValueError("account not found for transaction")
        validate_amount_for_currency(amount, account.currency)
        model.amount_cents = amount_to_cents(amount, account.currency)

        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)