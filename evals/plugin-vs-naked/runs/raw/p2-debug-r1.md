## Why it failed

The migration couldn't get a lock on `orders` because a `VACUUM (ANALYZE) orders` was already running on it.

1. **03:00:00:** `VACUUM (ANALYZE) orders` starts (pid 88211). VACUUM holds a `SHARE UPDATE EXCLUSIVE` lock on the table.
2. **03:02:43:** The migration runs `ALTER TABLE orders ADD COLUMN ...`. That statement needs an `ACCESS EXCLUSIVE` lock, which conflicts with VACUUM's lock, so it has to wait.
3. **03:02:58:** After about 15 seconds the `lock_timeout` setting cancels the wait, and Alembic exits 1.
4. The deploy stops before replacing any pods, so the rollback has nothing to undo.

**The migration itself is fine.** On PostgreSQL 11+, adding a column with a constant default (`NOT NULL DEFAULT ''`) only changes table metadata and finishes almost instantly. It just never got the lock.

**This is most likely a scheduled job, not autovacuum.** The query text is the manual `VACUUM (ANALYZE) orders` syntax, and it started exactly at 03:00:00, which suggests a cron or maintenance job. Autovacuum would show up as `autovacuum: VACUUM ANALYZE public.orders`. It would also usually cancel itself to let your ALTER through, which a manual VACUUM won't do.

**The timeout helped you.** Without `lock_timeout`, the ALTER would have waited in the lock queue. Every query on `orders` that arrived after it, including plain SELECTs, would then have queued behind it and stalled until the VACUUM finished. Keep the timeout.

## What to do now

1. **Confirm nothing was half-applied.** Postgres DDL runs in a transaction, so the change should have rolled back:
   ```sql
   SELECT version_num FROM alembic_version;   -- expect 4b1a
   SELECT column_name FROM information_schema.columns
   WHERE table_name = 'orders' AND column_name = 'customer_ref';  -- expect 0 rows
   ```
2. **Check whether the VACUUM is still running:**
   ```sql
   SELECT pid, state, now() - query_start AS runtime, query
   FROM pg_stat_activity WHERE pid = 88211;
   ```
3. **Re-run the deploy** once that query returns nothing. Nothing in the code needs to change.
   - If the VACUUM is taking unusually long and you need the deploy out now, you can stop it with `SELECT pg_cancel_backend(88211);`. Cancelling a VACUUM is safe; the work just gets redone on the next run. Since this is staging, that's low-risk.

## Preventing it next time

- **Find who schedules the 03:00 VACUUM** (cron, pg_cron, or an ops script) and keep it from overlapping your deploy window. Either move the job or move the deploys.
- **Add retries to the migration step** instead of raising `lock_timeout`. For example, retry 3–5 times with a backoff of 30–60 seconds. Short timeout plus retry is the standard safe pattern for migrations.
- **Optionally, run a pre-deploy check** that looks for long-running queries or locks on the tables a migration touches, and waits or warns before it starts.

If you show me where the deploy pipeline and the VACUUM job are defined, I can help add the retry or change the schedule.
