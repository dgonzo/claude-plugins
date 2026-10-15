All 3 tests pass now. Before the fix, all 3 failed.

**What was wrong:** `to_cents` in `invoicing/money.py` changed the price into a float and then cut off the decimal part:

```python
return int(float(amount) * 100)
```

Floats can't store most decimal prices exactly. For example, `19.99 * 100` comes out as `1998.9999999999998`, and `int()` drops everything after the decimal point, so you get `1998`. That lost a cent on some prices: 19.99 became 1998 and 0.29 became 28. The two invoice tests failed for the same reason, because their subtotals were built from those wrong cent values (7359 instead of 7365 for CA, 280 instead of 290 for OR).

**What I changed:** I edited that one line in `invoicing/money.py:6`. It now does the conversion with `Decimal`, which the module already imports, and rounds half-up instead of truncating:

```python
return int((Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
```

Prices like "19.99" now convert exactly. If a price has more than two decimal places, it rounds to the nearest cent instead of always rounding down.

**A related risk I didn't change:** `tax_for` in `invoicing/tax.py` also uses float rates and Python's `round()`, which rounds exact halves to the nearest even number (2.5 becomes 2). If a tax amount ever lands on exactly half a cent, the result could be off by a cent. Nothing in the current tests hits that case. Switching it to `Decimal` with `ROUND_HALF_UP` would make it match `round_money`; I can do that if you want.
