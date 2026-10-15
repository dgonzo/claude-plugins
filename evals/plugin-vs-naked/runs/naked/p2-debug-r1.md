# Why the staging deploy failed

The `orders` migration couldn't get a lock on the table, because a `VACUUM` was already running on it.

1. A `VACUUM (ANALYZE) orders` (pid 88211) started at exactly **03:00:00**. That exact time, and the fact that the query isn't labelled `autovacuum:`, suggest a scheduled job like a cron task rather than autovacuum.
2. At 03:02:43 the migration ran `ALTER TABLE orders ADD COLUMN ...`. That statement needs an `ACCESS EXCLUSIVE` lock, which can't be granted while VACUUM holds its `SHARE UPDATE EXCLUSIVE` lock.
3. After about 15s the session's `lock_timeout` cancelled the ALTER. Alembic exited 1, and the deploy aborted before replacing any pods.

This matters because autovacuum steps aside when another session needs a conflicting lock, but a manually started `VACUUM` doesn't. A scheduled vacuum on a large table will block DDL until it finishes.

Nothing else is wrong. The migration itself is fine: on Postgres 11+, adding a column with a constant default only updates metadata and finishes almost instantly once it has the lock. The lock timeout also did its job, because otherwise the waiting ALTER would have held up every other query on `orders` for as long as the vacuum ran.

## What to do now

1. **Check that nothing was partly applied.** Postgres DDL runs inside a transaction, so the migration should have rolled back:
   ```bash
   alembic current        # expect 4b1a
   ```
2. **Check whether the vacuum is still running:**
   ```sql
   SELECT pid, phase, heap_blks_scanned, heap_blks_total
   FROM pg_stat_progress_vacuum WHERE relid = 'orders'::regclass;
   ```
3. **Redeploy once it's done.** On staging, if you don't want to wait, cancelling it is safe. A cancelled vacuum loses no data; it can simply be run again later:
   ```sql
   SELECT pg_cancel_backend(88211);
   ```

## Stopping it from happening again

- **Keep deploys and maintenance apart.** Find the job that runs `VACUUM` at 03:00 and either move it or block deploys during that window. The same collision could happen in production.
- **Retry on lock timeout.** Keep a short `lock_timeout` but retry a few times with backoff, rather than failing the whole deploy on the first attempt. Many teams wrap DDL migrations this way:
  ```python
  op.execute("SET lock_timeout = '5s'")
  ```
  Then have the deploy step retry the migration about 3–5 times when it gets `LockNotAvailable`.
- **Optional pre-check.** Before migrating, have the deploy script check `pg_stat_activity` for a running `VACUUM` or long-running transaction on the tables being changed, and wait or warn if it finds one.

**In short:** this was a timing clash with a 03:00 vacuum job, not a bug in your migration. Confirm you're still on `4b1a`, wait for or cancel the vacuum, then redeploy.
