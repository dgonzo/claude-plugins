## Price cache entries now expire after a TTL

Cached prices now expire after a time-to-live (TTL) of 5 minutes by default. Before this change, cache entries never expired. Customers saw stale prices for up to a day after a price change. This fixes support ticket SUP-881.

## Changes

| File | Change |
|---|---|
| `app/cache.py` | `put` stores the price with its fetch time |
| `app/cache.py` | `get` evicts an expired entry and returns `None` |
| `app/settings.py` | New setting `PRICE_CACHE_TTL_SECONDS` with a default of 300 |

## Behaviour

- A cache hit within the TTL returns the price as before.
- An expired entry is removed on read. The caller gets `None` and fetches a fresh price.
- An entry is evicted only on read. No background sweep runs.

## Configuration

Set `PRICE_CACHE_TTL_SECONDS` in the environment to change the TTL. A lower value gives fresher prices but more fetches from the price source.

## Reviewer checks

- The diff does not show where `self.ttl_seconds` gets its value from `PRICE_CACHE_TTL_SECONDS`. Confirm that wiring.
- The diff does not show where `Entry` is defined or where `time` is imported. Confirm both.
- `get` now returns `entry.price` instead of the raw stored value. Any code that reads `_store` directly will now get an `Entry` object.

## Testing

- An entry read before the TTL returns its price.
- An entry read after the TTL returns `None` and is removed from the store.
- A missing SKU returns `None`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
