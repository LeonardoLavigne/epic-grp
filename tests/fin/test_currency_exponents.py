from decimal import Decimal
import pytest

from app.core.money import currency_exponent, validate_amount_for_currency, amount_to_cents


def test_currency_exponent_known_codes():
    assert currency_exponent("EUR") == 2
    assert currency_exponent("usd") == 2
    assert currency_exponent("JPY") == 0
    assert currency_exponent("KWD") == 3


def test_validate_amount_precision_by_currency():
    # JPY (0 decimals)
    validate_amount_for_currency(Decimal("100"), "JPY")
    with pytest.raises(ValueError):
        validate_amount_for_currency(Decimal("10.5"), "JPY")

    # KWD (3 decimals)
    validate_amount_for_currency(Decimal("1.234"), "KWD")
    with pytest.raises(ValueError):
        validate_amount_for_currency(Decimal("1.2345"), "KWD")


def test_amount_to_cents_varied_currencies():
    # EUR: 2 decimals
    assert amount_to_cents(Decimal("10.50"), "EUR") == 1050
    # JPY: 0 decimals
    assert amount_to_cents(Decimal("123"), "JPY") == 123
    # KWD: 3 decimals
    assert amount_to_cents(Decimal("1.234"), "KWD") == 1234

