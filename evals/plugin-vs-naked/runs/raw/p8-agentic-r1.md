All 3 tests pass now.

**What was wrong:** `to_cents` in `invoicing/money.py` turned dollar strings into cents with `int(float(amount) * 100)`. That has two problems:

1. **Floats can't store most decimal amounts exactly.** `float("19.99") * 100` comes out as `1998.9999999999998`, not `1999`.
2. **`int()` cuts off the decimal part instead of rounding.** So that tiny error became a whole cent lost: 19.99 → 1998, and 0.29 → 28.

Both invoice tests failed for the same reason. A cent lost per unit gets multiplied by the quantity, and in California the tax is then worked out on the smaller subtotal. That's why Oregon came out at 280 instead of 290 (10 × 28), and California at 7359 instead of 7365.

**What I changed:** I changed one line in `to_cents` so it uses `Decimal` and rounds half-up to the nearest cent:

```python
cents = (Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
return int(cents)
```

This is exact for amounts written as strings, and it matches the `Decimal`/`ROUND_HALF_UP` approach that `round_money` in the same file already uses. I didn't touch the tests or any other file.

**Similar risk I left alone:** `tax_for` in `invoicing/tax.py` still multiplies with a float rate and calls Python's `round()`. That function rounds an exact half-cent to the nearest even number rather than always up, so tax amounts that land on a half-cent could be off by a cent. No current test covers this. If you want the whole codebase consistent, I can switch it to `Decimal` with half-up rounding too.
