The migration could not get a lock on the `orders` table because a `VACUUM` job was already running on it. Nothing was deployed. Staging still runs the previous version, so retrying is safe.

## What happened

| Time (UTC) | Event |
|---|---|
| 03:00:00 | `VACUUM (ANALYZE) orders` starts as process 88211 |
| 03:02:43 | Migration `7c2d` runs `ALTER TABLE orders ADD COLUMN ...` |
| 03:02:58 | `ALTER` gives up after about 15 seconds of waiting for the lock |
| 03:02:59 | Deploy aborts before any pods are replaced |

`ALTER TABLE` needs an exclusive lock on the table. `VACUUM` holds a lock that blocks it. The database's lock timeout cancelled the `ALTER` instead of letting it wait. That timeout worked as intended. A waiting `ALTER` would have blocked every other query on `orders` behind it.

The migration itself is fine. On Postgres 11 and later, adding a column with a constant default only changes metadata. It finishes almost instantly once it has the lock.

## What to do now

1. Check whether the vacuum is still running:
   ```sql
   SELECT pid, state, now() - query_start AS runtime, query
   FROM pg_stat_activity WHERE pid = 88211;
   ```
2. If it has finished, re-run the deploy for commit `9f3c1e2`.
3. If it is still running, wait for it to finish. Or cancel it with `SELECT pg_cancel_backend(88211);`. Cancelling is low-risk on staging because the vacuum can run again later.

## How to stop it happening again

- **Avoid the 03:00 slot.** The vacuum started exactly on the hour, so a scheduled job probably started it rather than autovacuum. Move that job or the deploy so they don't overlap.
- **Retry migrations that hit a lock timeout.** Wrap the migration step in a few retries with a short backoff. A lock conflict is usually gone within minutes.
- **Keep the lock timeout.** Don't raise it to get past this. A long wait on an exclusive lock stalls all traffic to the table.
