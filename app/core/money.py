from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

# Minimal ISO 4217 exponent mapping for common currencies.
# Extend as needed; defaults to 2 when unknown (KISS/YAGNI).
ISO_4217_EXPONENTS: dict[str, int] = {
    "EUR": 2,
    "USD": 2,
    "GBP": 2,
    "BRL": 2,
    "JPY": 0,
    "CLP": 0,
    "KWD": 3,
    "BHD": 3,
}


def currency_exponent(currency: str) -> int:
    """Return the number of decimal places for a currency (ISO 4217).

    Defaults to 2 when currency code is unknown.
    """
    cur = (currency or "").upper()
    return ISO_4217_EXPONENTS.get(cur, 2)


def validate_amount_for_currency(amount: Decimal, currency: str) -> Decimal:
    exp = currency_exponent(currency)
    quant = Decimal(1).scaleb(-exp)  # e.g., 0.01
    q = amount.quantize(quant, rounding=ROUND_DOWN)
    if q != amount:
        raise ValueError(f"amount has more than {exp} decimal places for {currency}")
    return amount


def amount_to_cents(amount: Decimal, currency: str) -> int:
    exp = currency_exponent(currency)
    validate_amount_for_currency(amount, currency)
    cents = (amount * (Decimal(10) ** exp)).to_integral_value()
    return int(cents)


def cents_to_amount(cents: int, currency: str) -> Decimal:
    exp = currency_exponent(currency)
    return (Decimal(cents) / (Decimal(10) ** exp)).quantize(
        Decimal(1).scaleb(-exp), rounding=ROUND_HALF_UP
    )


def quantize_amount(amount: Decimal, currency: str) -> Decimal:
    """Quantize a Decimal to the currency exponent using ROUND_HALF_UP.

    Useful when apresentation must enforce the number of decimal places for
    report_currency regardless of intermediate precision.
    """
    exp = currency_exponent(currency)
    return amount.quantize(Decimal(1).scaleb(-exp), rounding=ROUND_HALF_UP)
