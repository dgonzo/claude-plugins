# Design: Rate Limiting for the Public REST API

## Summary
Add per-API-key rate limiting to the public REST API to protect backend capacity and enforce plan entitlements. Each key gets a token bucket. Bucket state lives in Redis. Limits come from the customer's plan. A request over the limit gets `HTTP 429 Too Many Requests` with a `Retry-After` header.

## Goals
- Make clients follow their plan limits, the same way on every API instance.
- Keep the added latency low: one Redis round trip per request.
- Tell clients clearly when they are limited and when they can retry.

## Non-Goals
- Per-endpoint or per-IP limits. These may come in a later version.
- Billing or quota tracking over long periods (daily or monthly).
- DDoS protection. That stays at the edge (CDN/WAF).

## Decisions
| Area | Decision |
|---|---|
| Algorithm | Token bucket per API key |
| State store | Redis (shared by all API instances) |
| Limits | Set per plan: **Free 60 req/min**, **Pro 600 req/min** |
| Over-limit response | `429 Too Many Requests` + `Retry-After` header (seconds) |

## Token Bucket Model
Each API key has a bucket with:
- **capacity** = the plan's per-minute limit (60 or 600). This also sets the largest allowed burst.
- **refill rate** = capacity / 60 tokens per second (Free: 1/s, Pro: 10/s).
- Each request uses **1 token**.

Refill is computed lazily when a request arrives, so no background job is needed:
```
elapsed = now - last_refill
tokens  = min(capacity, tokens + elapsed * refill_rate)
```

### Redis Representation
- Key: `ratelimit:{api_key_id}` as a hash with fields `tokens` and `ts` (last refill time, in ms).
- TTL: reset on every write to slightly more than the time needed to refill a full bucket (e.g. 120s). Idle keys then expire, and a missing key means a full bucket.
- The check runs as one **Lua script** (`EVALSHA`), so read-refill-consume-write is atomic across instances. The time comes from Redis (`TIME`), so instance clock drift does not affect it.
- The script returns `allowed`, `tokens_remaining`, and `retry_after_ms`.

## Plan Configuration
Plan limits are kept in config, not in code:
```yaml
rate_limits:
  free: { requests_per_minute: 60 }
  pro:  { requests_per_minute: 600 }
```
The API key → plan lookup reuses the existing auth step. Its result is cached in-process for a short time (e.g. 60s), so the limiter adds no extra database call. When a customer changes plan, the new limit applies once that cache entry expires.

## Request Flow
```
Client
  │
  ▼
[1] Auth middleware ── invalid/missing key ──► 401 (no rate limiting applied)
  │  resolves api_key_id + plan
  ▼
[2] Rate limit middleware
  │  look up plan limits (capacity, refill_rate)
  │  EVALSHA token_bucket.lua ratelimit:{api_key_id} capacity refill_rate cost=1
  │
  ├── allowed = false ──► 429 Too Many Requests
  │                        Retry-After: ceil(retry_after_ms / 1000)
  │                        X-RateLimit-Limit / -Remaining: 0 / -Reset
  │                        JSON error body { "error": "rate_limited", ... }
  │
  └── allowed = true
        │  set X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        ▼
[3] Route handler ──► normal response (2xx/4xx/5xx)
```

Step by step:
1. **Authenticate.** The limiter runs after auth, so it always has a trusted `api_key_id` and plan. Unauthenticated requests are rejected before they reach it.
2. **Resolve limits** from the plan config.
3. **Run the Lua script** against the key's bucket in Redis. The script refills tokens based on elapsed time and then tries to take one token.
4. **If denied**, return 429 right away. `Retry-After` is the time until one token is available, `(1 - tokens) / refill_rate`, rounded up to whole seconds and never less than 1.
5. **If allowed**, add informational rate-limit headers and pass the request to the handler.

## Failure Handling
- **Redis unavailable or timing out** (timeout budget about 50ms): **fail open**. Allow the request, log the event, and emit a metric. Availability is more important than strict enforcement during a short Redis outage. A circuit breaker stops repeated slow calls while Redis is down.
- **Unknown plan:** use the Free limits.

## Observability
- Metrics: allowed vs. limited count per plan, limiter latency, Redis errors and fail-open count.
- Logs: one log line for each 429, with `api_key_id` and plan. These logs are sampled.
- Alerts: alert on a fail-open rate above threshold and on a sharp rise in the 429 rate.

## Rollout
1. Deploy in **shadow mode**. Compute and log decisions, but never return 429.
2. Check the shadow data and tell customers whose traffic would be limited.
3. Turn on enforcement behind a feature flag, starting with the Free plan and then Pro.
4. Document the limits and headers in the public API docs.

## Open Questions
- Should some endpoints cost more than 1 token (e.g. bulk or export endpoints)?
- Do enterprise or custom plans need per-customer limit overrides?
