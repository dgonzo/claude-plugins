I fixed `to_cents` and all 3 tests pass now. It used floating-point maths and then cut off the fraction, so it lost a cent on some prices.

## Cause

`invoicing/money.py` converted dollars to cents with `int(float(amount) * 100)`.

| Price | `float * 100` | `int()` result | Expected |
|---|---|---|---|
| 19.99 | 1998.9999999999998 | 1998 | 1999 |
| 0.29 | 28.999999999999996 | 28 | 29 |

The invoice tests failed for the same reason. The CA total came out at 7359 instead of 7365. The Oregon total came out at 280 instead of 290.

## Change

`to_cents` now does exact decimal maths and rounds half-up to whole cents:

```python
cents = Decimal(str(amount)) * 100
return int(cents.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
```

This uses the same `Decimal` approach as `round_money` in that file. `python3 -m unittest` now passes 3 of 3.

## Same problem in the tax code, not fixed

`invoicing/tax.py` has the same kind of bug. `tax_for` multiplies with floats and then calls Python's `round()`, which rounds halves to the nearest even number. For example, a CA subtotal of 200 cents gives 14.499999999999998, which rounds to 14 cents. Rounding the exact 14.5 half-up gives 15.

No test covers this case and the tests pass without a fix, so I left it alone. Changing it changes the tax on some invoices. Fixing it would mean storing the rates as `Decimal` and rounding with `ROUND_HALF_UP`.
