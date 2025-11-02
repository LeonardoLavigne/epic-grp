from decimal import Decimal, ROUND_DOWN


def currency_exponent(currency: str) -> int:
    cur = (currency or "").upper()
    # Minimal mapping; extend later if needed
    if cur == "EUR":
        return 2
    return 2


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
    return (Decimal(cents) / (Decimal(10) ** exp)).quantize(Decimal(1).scaleb(-exp))
