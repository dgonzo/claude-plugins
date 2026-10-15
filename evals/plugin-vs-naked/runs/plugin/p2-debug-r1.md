A database lock timeout killed the migration. A `VACUUM (ANALYZE) orders` job had been running on the `orders` table since 03:00. The `ALTER TABLE` could not get its lock within the timeout. Nothing reached staging. No pods were replaced, and Postgres rolled back the migration's transaction.

## What happened

| Time (UTC) | Event |
|---|---|
| 03:00:00 | `VACUUM (ANALYZE) orders` starts as process 88211 |
| 03:02:43 | Migration 4b1a to 7c2d starts `ALTER TABLE orders ADD COLUMN` |
| 03:02:58 | `lock_timeout` fires after about 15 seconds |
| 03:02:59 | Deploy aborts. Rollback has nothing to undo. |

`ALTER TABLE` needs an `ACCESS EXCLUSIVE` lock. `VACUUM` holds a `SHARE UPDATE EXCLUSIVE` lock, and the two conflict. The vacuum started at exactly 03:00:00, and the query text has no `autovacuum:` prefix. A scheduled job most likely started it, not autovacuum.

The migration itself is fine. On Postgres 11 or later, adding a column with a constant default changes only the catalog. It does not rewrite the table. I assumed your version is 11 or later. I did not check it.

## What to do now

1. Check whether the vacuum is still running:
   ```sql
   SELECT pid, state, now() - query_start AS runtime, query
   FROM pg_stat_activity WHERE pid = 88211;
   ```
2. If it is still running, wait for it to finish. On staging you can also stop it with `SELECT pg_cancel_backend(88211);`. Stopping a vacuum is safe. It restarts on the next run.
3. Confirm the schema did not change. `alembic current` should show `4b1a`.
4. Re-run the deploy for commit `9f3c1e2`.

## Preventing a repeat

1. Find the job that runs `VACUUM (ANALYZE) orders` at 03:00. Check cron, `pg_cron` or your ops scheduler.
2. If it is scheduled, move the vacuum or the deploy window so they do not overlap.
3. Make the migration step retry on `LockNotAvailable`. Three tries 30 seconds apart would have covered this case. Keep `lock_timeout` short. A short timeout stops a blocked `ALTER` from queueing behind the vacuum and blocking every other query on `orders`.

Production will have the same risk if a vacuum runs there during a deploy. Check that schedule before you promote this release.
