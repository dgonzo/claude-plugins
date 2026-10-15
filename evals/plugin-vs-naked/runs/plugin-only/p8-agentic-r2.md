All 3 tests pass now. The bug was in `to_cents` in `invoicing/money.py`. It lost a cent on some prices.

**Cause.** `to_cents` ran `int(float(amount) * 100)`. Most decimal prices have no exact binary float value. So `float("19.99") * 100` gives `1998.9999999999998`. Then `int()` cuts off the fraction, which leaves `1998`. Each wrong price threw off the invoice totals that used it.

| Input | Expected cents | Old result |
|---|---|---|
| `"19.99"` | 1999 | 1998 |
| `"0.29"` | 29 | 28 |

**Fix.** `to_cents` now does the maths in `Decimal`, which is exact. It rounds half-up to a whole cent, so input with more than 2 decimal places still rounds correctly:

```python
cents = Decimal(str(amount)) * 100
return int(cents.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
```

**Not changed.** `invoicing/tax.py` has a similar risk. It works out tax with float rates and Python's `round()`. That function rounds an exact half-cent to the even number rather than up. The tests don't hit this case, but some totals could be off by one cent. Moving tax to `Decimal` with half-up rounding would fix it. I can make that change if you want it.
