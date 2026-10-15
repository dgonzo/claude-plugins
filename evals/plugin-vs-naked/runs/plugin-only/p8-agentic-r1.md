All 3 tests pass now. The bug was in `to_cents` in `invoicing/money.py`. It converted dollars to cents with floating-point maths, which sometimes lost a cent.

## What was wrong

`to_cents` ran `int(float(amount) * 100)`. Many decimal amounts have no exact binary float value. For example, `19.99 * 100` comes out as `1998.9999999999998`. Then `int()` cuts off the fraction instead of rounding, so the result was 1998.

| Input | Old result | Expected |
|---|---|---|
| `"19.99"` | 1998 | 1999 |
| `"0.29"` | 28 | 29 |

The two invoice tests failed for the same reason. The subtotals were short by a cent per unit:
- **CA (California) invoice:** 7359 instead of 7365.
- **OR (Oregon) invoice:** 280 instead of 290.

## What I changed

`to_cents` now works in `Decimal` and rounds half-up to a whole cent:

```python
cents = Decimal(str(amount)) * 100
return int(cents.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
```

This matches how `round_money` in the same file already works. No other files changed.

## A related risk I left alone

`tax_for` in `invoicing/tax.py` still uses float rates and Python's `round()`. `round()` sends exact halves to the nearest even number, so a tax of exactly 12.5 cents becomes 12, not 13. The current tests never produce an exact half, so they don't catch this. If you want tax to round half-up as well, I can switch it to `Decimal` too.
