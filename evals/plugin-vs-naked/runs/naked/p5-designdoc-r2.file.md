# Design: Rate Limiting for the Public REST API

## Summary

Add per-API-key rate limiting to the public REST API to protect backend capacity and enforce plan entitlements. Each API key gets a token bucket whose state lives in Redis. Bucket size and refill rate come from the key's plan. When a bucket is empty, the API returns `429 Too Many Requests` with a `Retry-After` header.

## Goals

- Enforce fair, plan-based usage limits per API key.
- Make limits consistent across all API instances (shared state).
- Give clients clear, standard signals when they are throttled.

## Non-goals

- Per-endpoint or cost-weighted limits (every request costs 1 token for now).
- Abuse/DDoS protection for unauthenticated traffic. That stays at the edge/WAF.
- Monthly quotas or billing-based usage metering.

## Decisions

| Area | Decision |
|---|---|
| Algorithm | Token bucket, one bucket per API key |
| State | Redis, shared by all API instances |
| Limits | Configured per plan |
| Throttle response | HTTP 429 with `Retry-After` header |

### Plan limits

| Plan | Sustained rate | Bucket capacity (burst) | Refill rate |
|---|---|---|---|
| Free | 60 req/min | 60 tokens | 1 token/sec |
| Pro | 600 req/min | 600 tokens | 10 tokens/sec |

Limits live in plan configuration, not code, so new plans or changes need no deploy. Capacity defaults to one minute of sustained rate. That allows short bursts while holding the per-minute average.

## Request flow

```
Client ──► API gateway / middleware
             │
             1. Authenticate request → resolve API key
             │     (no/invalid key → 401, limiter not consulted)
             │
             2. Look up key's plan → (capacity, refill_rate)
             │     (cached in-process, short TTL)
             │
             3. Call Redis Lua script: take_token(key, capacity, refill_rate, now)
             │
             ├── allowed ──► 4a. Set X-RateLimit-* headers, forward to handler ──► 2xx/4xx/5xx
             │
             └── denied ───► 4b. Return 429 + Retry-After + X-RateLimit-* headers
```

1. **Authenticate.** The limiter runs after authentication so it can key on the API key. Unauthenticated requests are rejected before they reach it.
2. **Resolve limits.** Map the API key to its plan and read `capacity` and `refill_rate`. Cache this in-process for about 60 s to avoid an extra lookup per request.
3. **Take a token atomically.** One Lua script in Redis does read, refill, decrement and write in a single round trip, so concurrent requests on different instances cannot race:
   - Read `tokens` and `last_refill` from hash `ratelimit:{api_key}`.
   - `tokens = min(capacity, tokens + (now - last_refill) * refill_rate)`.
   - If `tokens >= 1`: decrement, save, return `allowed, remaining`.
   - Otherwise save the refilled state and return `denied, retry_after = ceil((1 - tokens) / refill_rate)`.
   - Set a TTL on the key (≈ time to refill fully) so idle keys expire.
   - Use Redis server time (`TIME`) for `now` so app-server clock skew doesn't matter.
4. **Respond.**
   - **Allowed:** pass the request to the handler.
   - **Denied:** return `429 Too Many Requests` with `Retry-After: <seconds>` and a JSON error body (`{"error": "rate_limited", "retry_after": N}`).
   - Both cases include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` so clients can pace themselves.

## Failure handling

- **Redis unavailable or slow** (timeout ~50 ms): **fail open**. Allow the request, log it, and emit a metric. A limiter outage should not become an API outage. Revisit if abuse during outages becomes a problem.
- **Plan lookup fails:** fall back to Free-plan limits.

## Observability

- Counters: requests allowed and denied, by plan and API key (top-N).
- Latency histogram for the Redis limiter call.
- Count of fail-open events, with an alert when it is non-zero for a sustained period.

## Rollout

1. Ship in **shadow mode**: run the limiter and record decisions and headers, but never return 429.
2. Review shadow data for keys that would be throttled and contact heavy free-tier users.
3. Turn on enforcement behind a feature flag, Free plan first, then Pro.
4. Publish limits and header semantics in the public API docs before enforcement.

## Open questions

- Should some expensive endpoints cost more than 1 token?
- Do enterprise/custom plans need per-key overrides?
- Should a Redis Cluster deployment hash-tag keys for locality, or is the single-key script enough? It is single-key, so it is cluster-safe as is.
