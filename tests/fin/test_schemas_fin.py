import datetime as dt
from decimal import Decimal

import pytest

from app.schemas.finance.account import AccountCreate
from app.schemas.finance.category import CategoryCreate
from app.schemas.finance.transaction import TransactionCreate
from app.core.money import amount_to_cents


def test_account_currency_upper_default():
    a = AccountCreate(name="Conta Corrente")
    assert a.currency == "EUR"
    a2 = AccountCreate(name="A", currency="eur")
    assert a2.currency == "EUR"


def test_category_type_allowed():
    ok = CategoryCreate(name="Salário", type="INCOME")
    assert ok.type == "INCOME"
    with pytest.raises(ValueError):
        CategoryCreate(name="X", type="FOO")


def test_transaction_amount_decimal_precision_ok_and_to_cents():
    t = TransactionCreate(
        account_id=1,
        amount=Decimal("10.50"),
        occurred_at=dt.datetime.now(dt.timezone.utc),
    )
    assert amount_to_cents(t.amount, "EUR") == 1050


def test_transaction_amount_decimal_precision_invalid():
    with pytest.raises(ValueError):
        TransactionCreate(
            account_id=1,
            amount=Decimal("10.555"),
            occurred_at=dt.datetime.now(dt.timezone.utc),
        )


def test_transaction_occurred_at_utc_normalized():
    # Provide a time with offset; expect it normalized to UTC
    when = dt.datetime(2025, 1, 1, 12, 0, tzinfo=dt.timezone(dt.timedelta(hours=1)))
    t = TransactionCreate(account_id=1, amount=Decimal("1.00"), occurred_at=when)
    assert t.occurred_at.tzinfo is dt.timezone.utc
    assert t.occurred_at.hour == 11  # converted from +01:00 to UTC

