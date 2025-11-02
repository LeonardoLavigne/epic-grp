from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.account import Account
from app.models.finance.category import Category
from app.models.finance.transaction import Transaction
from app.models.finance.transfer import Transfer
from app.core.money import currency_exponent, amount_to_cents, validate_amount_for_currency
from app.schemas.finance.transfer import TransferCreate


TRANSFER_IN_NAME = "Transfer In"
TRANSFER_OUT_NAME = "Transfer Out"


async def _get_account(session: AsyncSession, user_id: int, account_id: int) -> Account | None:
    res = await session.execute(select(Account).where(Account.id == account_id, Account.user_id == user_id))
    return res.scalars().first()


async def _get_or_create_transfer_category(session: AsyncSession, user_id: int, *, income: bool) -> Category:
    name = TRANSFER_IN_NAME if income else TRANSFER_OUT_NAME
    typ = "INCOME" if income else "EXPENSE"
    res = await session.execute(select(Category).where(Category.user_id == user_id, Category.name == name, Category.type == typ))
    cat = res.scalars().first()
    if cat:
        return cat
    cat = Category(user_id=user_id, name=name, type=typ)
    session.add(cat)
    await session.flush()
    return cat


async def create_transfer(session: AsyncSession, *, user_id: int, data: TransferCreate) -> tuple[Transfer, Transaction, Transaction]:
    if data.src_account_id == data.dst_account_id:
        raise ValueError("accounts must differ")
    src = await _get_account(session, user_id, data.src_account_id)
    dst = await _get_account(session, user_id, data.dst_account_id)
    if not src or not dst:
        raise ValueError("account not found")

    # Validate amounts by currency
    validate_amount_for_currency(data.src_amount, src.currency)

    # Determine dst_amount and rate
    if data.dst_amount is not None:
        validate_amount_for_currency(data.dst_amount, dst.currency)
        rate_value = (data.dst_amount / data.src_amount)
        dst_amount = data.dst_amount
    else:
        if data.fx_rate is None:
            raise ValueError("dst_amount or fx_rate required")
        rate_value = data.fx_rate
        exp = currency_exponent(dst.currency)
        quant = Decimal(1).scaleb(-exp)
        dst_amount = (data.src_amount * rate_value).quantize(quant, rounding=ROUND_HALF_UP)
        validate_amount_for_currency(dst_amount, dst.currency)

    # Convert to cents
    src_cents = amount_to_cents(data.src_amount, src.currency)
    dst_cents = amount_to_cents(dst_amount, dst.currency)

    # Create transfer record
    tr = Transfer(
        user_id=user_id,
        src_account_id=src.id,
        dst_account_id=dst.id,
        src_amount_cents=src_cents,
        dst_amount_cents=dst_cents,
        rate_base=src.currency,
        rate_quote=dst.currency,
        rate_value=rate_value,
        occurred_at=data.occurred_at,
    )
    session.add(tr)
    await session.flush()

    # Categories
    cat_out = await _get_or_create_transfer_category(session, user_id, income=False)
    cat_in = await _get_or_create_transfer_category(session, user_id, income=True)

    # Create two transactions
    tx_out = Transaction(
        user_id=user_id,
        account_id=src.id,
        category_id=cat_out.id,
        amount_cents=src_cents,
        occurred_at=data.occurred_at,
        description="Transfer Out",
        transfer_id=tr.id,
    )
    tx_in = Transaction(
        user_id=user_id,
        account_id=dst.id,
        category_id=cat_in.id,
        amount_cents=dst_cents,
        occurred_at=data.occurred_at,
        description="Transfer In",
        transfer_id=tr.id,
    )
    session.add_all([tx_out, tx_in])
    await session.commit()
    await session.refresh(tr)
    await session.refresh(tx_out)
    await session.refresh(tx_in)
    return tr, tx_out, tx_in

