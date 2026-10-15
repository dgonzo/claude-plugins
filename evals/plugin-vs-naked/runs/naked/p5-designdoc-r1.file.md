# Design: Rate Limiting for the Public REST API

## Goal

Protect the public REST API from abuse and uneven load by limiting how many requests each API key can make. Limits depend on the customer's plan.

## Decisions

| Area | Decision |
|---|---|
| Algorithm | Token bucket, one bucket per API key |
| State | Redis |
| Limits | Set per plan: **free** = 60 req/min, **pro** = 600 req/min |
| Rejection | HTTP `429 Too Many Requests` with a `Retry-After` header |

## Token bucket model

Each API key has a bucket with:

- **capacity**: the plan's per-minute limit (60 or 600). This is also the largest burst allowed.
- **refill rate**: capacity / 60 tokens per second (1/s for free, 10/s for pro).

Each request uses one token. If the bucket has fewer than one token, the request is rejected.

## Configuration

Plan limits are stored in configuration, not in code, so we can change them without a deploy:

```yaml
rate_limits:
  free: { capacity: 60,  refill_per_sec: 1 }
  pro:  { capacity: 600, refill_per_sec: 10 }
```

The plan for an API key comes from the existing key lookup done during authentication. If the lookup returns an unknown plan, the key gets the free limits.

## Redis state

- Key: `ratelimit:{api_key_id}`
- Hash fields: `tokens` (float) and `ts` (time of the last refill, in ms)
- TTL: the time a bucket takes to refill from empty (60 s), plus some slack. Buckets for idle keys expire on their own, and an expired bucket counts as full.

The refill-and-take step runs as **one Lua script** (`EVALSHA`), so it is atomic across all API instances and takes one round trip. The script uses Redis server time (`TIME`), so clock drift between app hosts doesn't matter.

Script logic:

```
now      = redis TIME (ms)
tokens, ts = HGET key (default: capacity, now)
tokens   = min(capacity, tokens + (now - ts) / 1000 * refill_rate)
if tokens >= 1:
    tokens -= 1; allowed = 1; retry_after = 0
else:
    allowed = 0; retry_after = ceil((1 - tokens) / refill_rate)
HSET key tokens, now; PEXPIRE key ttl
return allowed, tokens, retry_after
```

## Request flow

```
Client
  │
  ▼
API gateway / HTTP server
  │
  ▼
1. Authentication middleware ── invalid key ──► 401
  │  (resolves api_key_id + plan)
  ▼
2. Rate limit middleware
  │  a. Look up plan limits from config
  │  b. Run the Lua token bucket script in Redis
  │
  ├── allowed = 0 ──► 429 Too Many Requests
  │                    Retry-After: <seconds>
  │                    X-RateLimit-Limit / X-RateLimit-Remaining
  │
  ▼ allowed = 1
3. Add X-RateLimit-* headers to the response
  │
  ▼
4. Route handler ──► response to client
```

Steps in order:

1. The request arrives, and authentication resolves the API key and its plan. Unauthenticated requests are rejected before the limiter runs, so they never create buckets.
2. The rate limit middleware gets the plan's capacity and refill rate from config.
3. The middleware runs the Lua script with the key ID, capacity, and refill rate.
4. **Allowed**: the request goes on to the handler. The response includes `X-RateLimit-Limit` and `X-RateLimit-Remaining`.
5. **Rejected**: the middleware returns `429` straight away with:
   - `Retry-After: <seconds>`: whole seconds, rounded up, until one token is available
   - the same `X-RateLimit-*` headers
   - a JSON error body: `{"error": "rate_limited", "retry_after": N}`

## Failure handling

- **Redis unavailable or slow** (timeout ~50 ms): **fail open**. Let the request through, log the error, and increment a `ratelimit.redis_errors` metric. Rate limiting protects the API, but it should not cause an outage of its own.
- **Plan changes** (for example, upgrade from free to pro): take effect on the next request, because limits are read for each request. The current token count stays the same and is capped at the new capacity.

## Observability

- Counters: `ratelimit.allowed`, `ratelimit.rejected` (tagged by plan), `ratelimit.redis_errors`
- Histogram: latency of the limiter call
- Alert when the rejection rate for a single key spikes, or when Redis errors stay high

## Out of scope

- Per-endpoint limits or endpoints that cost more than one token
- Limits by IP address for unauthenticated traffic
- Quotas over longer windows (daily or monthly)
