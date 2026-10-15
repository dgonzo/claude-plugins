from .money import to_cents, round_money
from .tax import tax_for


def invoice_total_cents(lines, region):
    subtotal = sum(to_cents(price) * qty for price, qty in lines)
    tax = tax_for(subtotal, region)
    return subtotal + tax


def invoice_total(lines, region):
    return round_money(invoice_total_cents(lines, region) / 100)
