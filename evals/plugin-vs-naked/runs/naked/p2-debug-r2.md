## Why it failed

The migration couldn't get a lock on `orders` because a `VACUUM (ANALYZE) orders` was already running on that table.

1. `ALTER TABLE orders ADD COLUMN ...` needs an **ACCESS EXCLUSIVE** lock on `orders`.
2. pid 88211 had been running `VACUUM (ANALYZE) orders` since **03:00:00**. VACUUM holds a SHARE UPDATE EXCLUSIVE lock, which blocks ACCESS EXCLUSIVE.
3. The ALTER waited about 15s (03:02:43 to 03:02:58), hit `lock_timeout`, and was cancelled. Alembic exited 1, and the deploy aborted before any pods were replaced.

The query text and the exact 03:00:00 start time suggest a **scheduled maintenance job**, not autovacuum. Autovacuum would show as `autovacuum: VACUUM ANALYZE public.orders`, and it cancels itself when it blocks a lock request. A manual or cron VACUUM doesn't do that. So your deploy most likely ran into a nightly vacuum.

The migration itself is fine. On Postgres 11+, `ADD COLUMN ... NOT NULL DEFAULT ''` only changes metadata and finishes almost instantly once it has the lock. The lock timeout did its job: without it, the ALTER would have sat in the lock queue and blocked every read and write on `orders` behind it.

## Current state

- **Pods:** still on the previous release ("no pods replaced").
- **Database:** should still be at revision `4b1a`, because Postgres DDL is transactional and the failed ALTER rolled back. Check with `alembic current` before retrying.

## What to do now

1. **Check whether the vacuum is still running:**
   ```sql
   SELECT pid, phase, heap_blks_scanned, heap_blks_total
   FROM pg_stat_progress_vacuum WHERE relid = 'orders'::regclass;
   ```
2. **Re-run the deploy after it finishes.** This is the simplest option.
3. **If you can't wait,** cancel it with `SELECT pg_cancel_backend(88211);` and re-run the deploy. On staging that's harmless: the vacuum's completed work is kept and it can be run again later.

## Preventing it next time

- **Avoid the overlap:** find the job that runs at 03:00 (cron, pg_cron or a maintenance script) and either move it or keep deploys out of that window.
- **Retry the migration:** keep the short `lock_timeout`, but have the migration step retry a few times with backoff instead of failing on the first timeout. This is the standard pattern for DDL on busy tables.
- **Check production:** if the same vacuum schedule runs there, a production deploy at that hour would fail the same way.
