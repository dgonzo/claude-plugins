The migration timed out waiting for a lock on the `orders` table. A `VACUUM (ANALYZE) orders` job held that lock. Nothing was changed. Rerun the deploy once the vacuum finishes.

## What happened

| Time (UTC) | Event |
|---|---|
| 03:00:00 | `VACUUM (ANALYZE) orders` starts. Process ID is 88211. |
| 03:02:43 | Migration 7c2d runs `ALTER TABLE orders ADD COLUMN customer_ref ...` |
| 03:02:58 | Postgres cancels the `ALTER` after about 15 seconds. It hit the lock timeout. |
| 03:02:59 | Deploy aborts. No pods were replaced. |

`ALTER TABLE` needs an exclusive lock on the table. The running vacuum holds a lock that blocks it. The migration waited, hit `lock_timeout` and was cancelled.

## Impact

- The failed migration rolled back. The schema is still at revision 4b1a.
- Staging is still running the old image.
- The migration itself is fine. On Postgres 11 or later, adding a column with a constant default is a fast metadata change. It only needs the lock briefly.

## What to do now

1. Check whether the vacuum is still running:
   ```sql
   SELECT pid, state, now() - query_start AS runtime, query
   FROM pg_stat_activity WHERE pid = 88211;
   ```
2. If it has finished, rerun the deploy for commit 9f3c1e2.
3. If it is still running on staging, you can cancel it with `SELECT pg_cancel_backend(88211);` and then redeploy.

## Stopping it from happening again

The vacuum is a manual or scheduled job, not autovacuum. Autovacuum would show as `autovacuum: VACUUM` in the log. It started exactly at 03:00, so it is probably a cron job.

| Fix | Effect |
|---|---|
| Move the vacuum job or the deploy window | Stops the two from overlapping |
| Retry the migration on `LockNotAvailable` | Recovers from short lock waits on its own |
| Keep a short `lock_timeout` | Keeps a waiting `ALTER` from blocking all other queries on `orders` |

Keep the short lock timeout. It worked as intended here. Without it, the waiting `ALTER` would have blocked every read and write on `orders` until the vacuum finished.
