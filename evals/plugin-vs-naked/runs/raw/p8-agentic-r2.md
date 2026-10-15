All 3 tests pass now. The bug was in how prices were converted to cents.

**What was wrong:** `to_cents` in `invoicing/money.py` did `int(float(amount) * 100)`. Floats can't store most decimal prices exactly, so `float("19.99") * 100` comes out as `1998.9999999999998`. Then `int()` cuts off the decimals instead of rounding, so you get 1998 instead of 1999. Most prices lose a cent this way:
- `"19.99"` → 1998, which caused the direct `to_cents` test failure.
- `"0.29"` → 28, so 10 of them came to 280 instead of 290 (the Oregon test).
- For the California invoice, the subtotal was 3 cents short, and tax on that lower subtotal pushed the total to 7359 instead of 7365.

**What I changed:** `to_cents` now does the conversion with `Decimal` and rounds half-up to a whole cent:

```python
cents = (Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
return int(cents)
```

That's the only change, and no tests were modified.

**A similar risk I left alone:** `tax_for` in `invoicing/tax.py` still multiplies cents by a float rate and uses Python's `round()`. `round()` rounds exact halves to the nearest even number, and float error can tip borderline amounts the wrong way, so tax could occasionally be a cent off on a half-cent amount. None of the current tests hit this. If you want it fixed, I can switch it to `Decimal` with `ROUND_HALF_UP`, the same as `round_money`.
