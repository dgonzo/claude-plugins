# Design: Rate Limiting for the Public REST API

## Summary
Add per-API-key rate limiting to the public REST API. Each key gets a token bucket kept in Redis, sized by the customer's plan. When a request is over the limit, the API returns `429 Too Many Requests` with a `Retry-After` header.

## Goals
- Protect backend capacity from bursts and abusive clients.
- Enforce plan-based usage tiers fairly and predictably.
- Give clients clear, machine-readable feedback when they are throttled.

## Non-Goals
- Per-endpoint or cost-weighted limits (possible later).
- Rate limiting for unauthenticated traffic (handled at the edge/WAF).
- Global or per-organization quotas (e.g. daily or monthly caps).

## Decisions
| Area | Decision |
|---|---|
| Algorithm | Token bucket, one bucket per API key |
| State store | Redis (shared by all API instances) |
| Limits | Set per plan: **Free 60 req/min**, **Pro 600 req/min** |
| Over-limit response | HTTP `429` with a `Retry-After` header (seconds) |

## Token Bucket Model
Each API key has a bucket defined by:
- **capacity**: the largest burst allowed. Defaults to the per-minute limit (60 or 600).
- **refill rate**: limit / 60 tokens per second (Free = 1/s, Pro = 10/s).

Each request uses 1 token. Tokens refill continuously based on elapsed time, so there is no fixed-window reset and no burst at window boundaries.

### Redis representation
- Key: `ratelimit:{api_key_id}`, a hash with fields `tokens` (float) and `ts` (last refill, ms).
- TTL: about 2× the time it takes to refill a full bucket, so idle keys expire on their own.
- The refill, check, and decrement run as **one Lua script** (`EVALSHA`), so they happen atomically across concurrent API instances. Time comes from Redis `TIME` to avoid clock skew between app servers.

Script logic (pseudocode):
```
now = redis TIME (ms)
tokens, ts = HMGET key tokens ts   (default: capacity, now)
tokens = min(capacity, tokens + (now - ts) * rate_per_ms)
if tokens >= 1:
    tokens -= 1; allowed = 1; retry_after_ms = 0
else:
    allowed = 0; retry_after_ms = ceil((1 - tokens) / rate_per_ms)
HSET key tokens tokens ts now; PEXPIRE key ttl
return allowed, tokens, retry_after_ms
```

## Request Flow
```
Client
  │
  ▼
[1] Auth middleware ── resolves API key → account + plan
  │                    (invalid key → 401, never reaches limiter)
  ▼
[2] Rate limit middleware
  │   a. Look up plan limits (in-process cache of plan config)
  │   b. Run Lua token-bucket script in Redis for ratelimit:{key_id}
  │   c. Allowed? ──no──► 429 + Retry-After + RateLimit headers → Client
  │        │
  │       yes
  ▼        ▼
[3] Set rate-limit headers on response
  │
  ▼
[4] Route handler → response → Client
```

1. **Authenticate.** The limiter runs *after* auth, so it always has a verified key ID and plan.
2. **Resolve limits.** Plan → (capacity, rate) comes from config, cached in memory and refreshed periodically.
3. **Consume a token.** A single Redis round trip runs the Lua script.
4. **Reject or continue.**
   - Rejected: return `429` with `Retry-After: <ceil(retry_after_ms/1000)>` and a JSON error body (`{"error": "rate_limited", "retry_after": N}`).
   - Allowed: pass the request to the handler.
5. **Headers on every response** (informational):
   - `RateLimit-Limit`: the plan's per-minute limit
   - `RateLimit-Remaining`: floor(tokens)
   - `RateLimit-Reset`: seconds until the bucket is full

## Configuration
Plan limits are stored in config (not code), so they can change without a deploy:
```yaml
rate_limits:
  free: { requests_per_minute: 60,  burst: 60 }
  pro:  { requests_per_minute: 600, burst: 600 }
```
A limit change takes effect on the next request. Existing buckets are clamped to the new capacity.

## Failure Handling
- **Redis unavailable or slow** (timeout ~50 ms): **fail open**. Allow the request, emit a metric, and log a warning. Availability of the API comes before strict enforcement. A local in-memory fallback limiter can be added if abuse during an outage becomes a concern.
- **Unknown plan**: fall back to the Free limits.

## Observability
- Counters: `ratelimit.allowed`, `ratelimit.rejected` (tagged by plan), `ratelimit.redis_errors`.
- Histogram: limiter latency.
- Alert when the rejection rate spikes or when Redis errors persist.

## Rollout
1. Deploy in **shadow mode**: compute decisions and emit metrics and headers, but never return 429.
2. Review which customers would be throttled. Contact any heavy Free users.
3. Turn on enforcement behind a feature flag, starting with Free and then Pro.
4. Publish the limits and headers in the public API docs.

## Open Questions
- Should burst capacity exceed the per-minute rate (e.g. Pro burst of 1000)?
- Do internal or partner keys need an exempt or custom plan?
- Do we need per-endpoint weighting for expensive endpoints later?
