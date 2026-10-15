The migration could not get a lock on the `orders` table. A `VACUUM (ANALYZE) orders` started at 03:00:00 and was still running when the migration tried to alter the table. The migration waited 15 seconds and then hit Postgres's lock timeout.

Nothing was deployed. Staging still runs the old image, and no pods were replaced.

## Why the lock conflicted

| Time (UTC) | Event |
|---|---|
| 03:00:00 | `VACUUM (ANALYZE) orders` starts as pid 88211 |
| 03:02:43 | Migration runs `ALTER TABLE orders ADD COLUMN` |
| 03:02:58 | Lock timeout cancels the `ALTER` |
| 03:02:59 | Deploy aborts |

`ALTER TABLE` needs the strongest table lock, which conflicts with the lock `VACUUM` holds. The migration itself is fine. On Postgres 11 and later, adding a column with a constant default changes only metadata, so it runs in milliseconds once it has the lock.

The query text is a plain `VACUUM`. An autovacuum would show as `autovacuum: VACUUM ...`. So a scheduled job probably started it at 03:00, the same time as your deploy window.

## What to do now

1. Check whether the vacuum is still running: `SELECT pid, state, now() - query_start FROM pg_stat_activity WHERE pid = 88211;`
2. Run `alembic current` and confirm it shows `4b1a`. Postgres rolls back DDL inside a transaction, so it should.
3. If the vacuum has finished, rerun the deploy for `9f3c1e2`.
4. If it is still running and you cannot wait, cancel it with `SELECT pg_cancel_backend(88211);`. Cancelling a manual vacuum loses no data. It only stops the job early.

## How to stop it happening again

- Find the job that runs `VACUUM (ANALYZE) orders` at 03:00. Move it so it does not overlap the deploy window.
- Keep the lock timeout. Without it, the waiting `ALTER` would have blocked every read and write on `orders` until the vacuum finished.
- Optionally, make the migration step retry a few times on `LockNotAvailable`.

I worked from the log only. I have not checked your database, cron jobs or Postgres version.
