## Expire price cache entries after a TTL

Fixes SUP-881.

### Problem

`PriceCache` entries never expired. Once a price was cached, it was served until the process restarted, so customers saw stale prices for up to a day after a price change.

### Changes

- **`app/cache.py`**
  - `put()` now stores an `Entry` holding the price and the time it was fetched (`fetched_at`), not the raw price.
  - `get()` checks how old the entry is. If it's older than `ttl_seconds`, `get()` removes it and returns `None`, which sends the caller back to fetch a fresh price. Fresh entries return the price as before.
- **`app/settings.py`**
  - Adds `PRICE_CACHE_TTL_SECONDS`, read from the environment. The default is `300` (5 minutes).

### Behavior notes

- A price can now be stale for at most `PRICE_CACHE_TTL_SECONDS`, not indefinitely.
- Expired entries are removed only when someone reads them. An entry that is never read again stays in memory, so memory use isn't capped, just as before this change.
- `_store` now holds `Entry` objects, not prices. Any code that reads `_store` directly instead of calling `get()` will need updating.
- Reviewers: please confirm that `PriceCache.ttl_seconds` is set from `PRICE_CACHE_TTL_SECONDS`. That wiring isn't visible in this diff.

### Testing

- [ ] `get()` returns the cached price before the TTL elapses
- [ ] `get()` returns `None` and evicts the entry after the TTL elapses
- [ ] `get()` returns `None` for a SKU that was never cached
- [ ] `PRICE_CACHE_TTL_SECONDS` overrides the default when set

🤖 Generated with [Claude Code](https://claude.com/claude-code)
