I fixed the bug and all 3 tests now pass.

**What was wrong:** `to_cents` in `invoicing/money.py` converted dollar strings to cents with `int(float(amount) * 100)`. Many decimal prices can't be stored exactly as a float, so the product lands just under the whole number. `int()` then cuts off the fraction instead of rounding:

- `"19.99"` → `1998.9999999999998` → **1998** (should be 1999)
- `"0.29"` → `28.999999999999996` → **28** (should be 29)

All three failures came from this one bug. The Oregon total was 280 instead of 290 (10 × 28¢), and the California total was 7359 instead of 7365 because its subtotal was already a few cents low before tax was added.

**What I changed:** one line in `invoicing/money.py:6`. It now converts the string with `Decimal`, which keeps the value exact, and rounds half-up to whole cents. It no longer goes through `float` at all:

```python
cents = Decimal(str(amount)) * 100
return int(cents.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
```

I didn't change any tests.

**A related issue I left alone:** `tax_for` in `invoicing/tax.py` also uses float rates and Python's `round()`. `round()` rounds exact halves to the nearest even number, so a tax of 12.5¢ becomes 12¢, not 13¢. That's different from the half-up rounding used in `money.py`. It doesn't affect the current tests, but if you want consistent half-up rounding, `tax_for` could use `Decimal` rates too.
