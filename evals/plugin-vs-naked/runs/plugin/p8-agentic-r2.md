The tests failed because `to_cents` turned prices into floats and then truncated them. I rewrote it to use exact decimal arithmetic. All 3 tests now pass.

## Cause

`to_cents` in `invoicing/money.py:6` was `int(float(amount) * 100)`.

- A float can't hold most decimal prices exactly. `float("19.99") * 100` gives `1998.9999999999998`.
- `int()` drops the fraction instead of rounding, so 19.99 became 1998 cents.

One bad function broke all three tests:

| Test | Expected | Got | Lost cents |
|---|---|---|---|
| `test_to_cents_exact` | 1999 | 1998 | 1 on 19.99 |
| `test_invoice_ca` | 7365 | 7359 | 1 per unit of 19.99 and 4.35, plus tax on that |
| `test_invoice_oregon` | 290 | 280 | 1 per unit of 0.29 |

## Change

I replaced the body of `to_cents` in `invoicing/money.py`:

```python
cents = Decimal(str(amount)) * 100
return int(cents.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
```

This does the conversion in `Decimal` and rounds half up. That matches `round_money` in the same file. I changed nothing else.

## Remaining risk

`tax_for` in `invoicing/tax.py:8` still multiplies by a float rate and uses Python's `round()`. That `round()` sends exact halves to the nearest even number. So a tax of exactly half a cent can round down. No current test covers that case, and I left it unchanged.
