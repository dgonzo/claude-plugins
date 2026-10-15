from decimal import Decimal, ROUND_HALF_UP


def to_cents(amount):
    """Convert a decimal amount in dollars to integer cents."""
    return int(float(amount) * 100)


def round_money(amount):
    return Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
