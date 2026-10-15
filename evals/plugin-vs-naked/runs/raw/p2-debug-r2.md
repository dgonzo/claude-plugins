## Why it failed

The migration couldn't get a lock on the `orders` table because a `VACUUM` was running on it.

1. A `VACUUM (ANALYZE) orders` started at **03:00:00** (pid 88211) and was still running when the deploy started at 03:02.
2. `ALTER TABLE orders ADD COLUMN ...` needs an `ACCESS EXCLUSIVE` lock. The VACUUM holds a `SHARE UPDATE EXCLUSIVE` lock, and those two conflict.
3. The ALTER waited about 15 seconds (03:02:43 → 03:02:58) until it hit your `lock_timeout`. Postgres then cancelled it, alembic exited 1, and the deploy aborted.

The migration itself is fine. This was a timing collision. The 03:00:00 start and the explicit `VACUUM (ANALYZE)` command suggest a scheduled maintenance job, not autovacuum. Autovacuum normally cancels itself when something else needs a conflicting lock. A manual VACUUM doesn't, so it blocks the ALTER.

**Nothing was changed.** Alembic runs the upgrade in a transaction, so it rolled back, and no pods were replaced. Staging should still be on revision `4b1a` with the old image.

## What to do now

1. **Check whether the VACUUM is still running:**
   ```sql
   SELECT pid, state, now() - query_start AS runtime, query
   FROM pg_stat_activity WHERE pid = 88211;
   -- progress, if it's still going:
   SELECT * FROM pg_stat_progress_vacuum WHERE pid = 88211;
   ```
2. **Confirm the database state:** `alembic current` should show `4b1a`.
3. **Re-run the deploy** once the VACUUM has finished. On staging, if you don't want to wait, you can stop it with `SELECT pg_cancel_backend(88211);`. Cancelling a VACUUM is safe and it can be re-run later.

## How to stop it happening again

- **Separate deploys from maintenance.** Find what runs at 03:00 (cron, pg_cron, a k8s CronJob) and either move it or keep deploys out of that window.
- **Keep the short `lock_timeout`, and add retries.** The timeout did its job. Without it, the waiting ALTER would have sat in the lock queue and blocked every read and write on `orders` behind it, which on a busy table looks like an outage. A better fix is to retry the migration a few times with a backoff, or have the pipeline check `pg_locks` for conflicting sessions on the target tables before running migrations.
- **Check your Postgres version.** On PG 11+, `ADD COLUMN ... NOT NULL DEFAULT ''` only changes metadata and finishes almost instantly once it has the lock. On PG 10 or older it rewrites the whole table, which would be a much bigger problem in production.
