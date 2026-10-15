## Summary

Price cache entries now expire after a configurable TTL. Before this change they never expired, so customers could see stale prices for up to a day after a price changed (SUP-881).

## Changes

- **`app/cache.py`**
  - `put()` now stores an `Entry` holding the price and a `fetched_at` timestamp, not just the bare price.
  - `get()` checks how old the entry is. If it is older than `self.ttl_seconds`, `get()` removes it from the store and returns `None`, the same as a cache miss. Callers still get either a price or `None`, so the interface is unchanged.
- **`app/settings.py`**
  - Adds `PRICE_CACHE_TTL_SECONDS`, which is read from the environment and defaults to `300` (5 minutes).

## Notes

- Expired entries are removed only when a `get()` reads them. Nothing sweeps the cache in the background, so a SKU that is never read again stays in memory.
- A price change can still take up to `PRICE_CACHE_TTL_SECONDS` to show up. To make prices update faster, lower the env var; this trades freshness for more upstream fetches.

## Testing

- [ ] `get()` returns the cached price before the TTL elapses
- [ ] `get()` returns `None` and evicts the entry after the TTL elapses (mock `time.time`)
- [ ] `PRICE_CACHE_TTL_SECONDS` override is picked up from the environment

Fixes SUP-881

🤖 Generated with [Claude Code](https://claude.com/claude-code)
