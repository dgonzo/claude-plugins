## Price cache entries now expire after 5 minutes by default

Customers saw old prices for up to a day after a price change. Cache entries never expired. This fixes support ticket SUP-881.

## Changes

| File | Change |
|---|---|
| `app/cache.py` | `put` stores the price with the time it was fetched. |
| `app/cache.py` | `get` treats an entry older than `ttl_seconds` as a miss and deletes it. |
| `app/settings.py` | Adds `PRICE_CACHE_TTL_SECONDS`. The default is 300. |

## Behaviour

- `get` still returns a price or `None`. Callers do not change.
- Expired entries are deleted only when they are read. The cache does not sweep them in the background.
- Set `PRICE_CACHE_TTL_SECONDS` to change the TTL for each environment without a deploy.

## Review notes

- The diff does not show the `Entry` definition or the `time` import.
- It does not show where `ttl_seconds` is set from `PRICE_CACHE_TTL_SECONDS`. Check that this wiring exists.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
