## Summary

Price cache entries never expired, so customers could see a stale price for up to a day after it changed (SUP-881). This PR adds a TTL to `PriceCache` entries so old prices get dropped and fetched again.

## Changes

- **`app/cache.py`**
  - `put()` now stores an `Entry` holding the price and the time it was fetched (`fetched_at`). Before, it stored only the raw price.
  - `get()` checks how old the entry is. If it's older than `self.ttl_seconds`, it removes the entry from the store and returns `None`, which the caller treats as a cache miss. Fresh entries return `entry.price`, so callers get the same return type as before.
- **`app/settings.py`**
  - Adds `PRICE_CACHE_TTL_SECONDS`, read from the environment. The default is `300` (5 minutes).

## Notes for reviewers

- Expired entries are only removed when `get()` reads them. Nothing sweeps the cache in the background, so SKUs that are never read again stay in memory. Memory use is no worse than before, but this doesn't fix it either.
- The cache now stores `Entry` objects instead of raw prices. Any code that reads `_store` directly will now get an `Entry`, not a price.
- Check that `PriceCache.ttl_seconds` is set from `PRICE_CACHE_TTL_SECONDS` where the cache is created. That wiring isn't shown in this diff.

## Testing

- [ ] `get()` returns the price for an entry younger than the TTL
- [ ] `get()` returns `None` and removes the entry once the TTL has passed (mock `time.time`)
- [ ] `get()` returns `None` for a SKU that isn't in the cache
- [ ] `PRICE_CACHE_TTL_SECONDS` overrides the default when it's set

Fixes SUP-881

🤖 Generated with [Claude Code](https://claude.com/claude-code)
