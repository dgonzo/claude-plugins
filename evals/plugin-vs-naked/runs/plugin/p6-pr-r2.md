Price cache entries now expire after a set time-to-live (TTL). The default is 300 seconds. Customers no longer see stale prices for up to a day after a price change. This fixes the stale-price support ticket, SUP-881.

## Cause

`PriceCache` stored prices with no timestamp. Entries never expired. A price change reached customers only when the process restarted.

## Change

| File | Change |
|---|---|
| `app/cache.py` | `put` stores the price with its fetch time |
| `app/cache.py` | `get` drops entries older than the TTL and returns `None` |
| `app/settings.py` | Adds `PRICE_CACHE_TTL_SECONDS`, default 300 |

An expired entry counts as a cache miss. The caller then fetches a fresh price.

## Configuration

Set `PRICE_CACHE_TTL_SECONDS` to change the TTL. A lower value gives fresher prices but more upstream fetches.

## Reviewer notes

- This diff adds no tests. Expiry needs one test for a fresh entry and one for an expired entry.
- Expired entries leave the cache only when someone reads them. SKUs (stock keeping units) that nobody reads again stay in memory.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
