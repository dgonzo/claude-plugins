An index lets the database find matching rows without reading the whole table. In return, every write costs more, and the index takes disk and memory.

## How an index speeds up a read

Without an index, the database reads every row and checks each one. This is a full table scan.

A B-tree index is the most common type. It keeps the indexed column's values in sorted order. Each value points to its row. The database walks down the tree and reaches the match in a few steps.

```
Query: WHERE email = 'kim@x.com'

              ┌──────────────┐
              │ root: a … z  │
              └──────┬───────┘
          ┌──────────┴──────────┐
   ┌──────┴──────┐       ┌──────┴──────┐
   │   a … m     │       │   n … z     │
   └──────┬──────┘       └─────────────┘
   ┌──────┴──────┐
   │ kim@x.com   │ ──► row 48213
   └─────────────┘
```

| Table size | Full scan reads | B-tree reads |
|---|---|---|
| 1,000 rows | 1,000 rows | about 2 pages |
| 1,000,000 rows | 1,000,000 rows | about 3 to 4 pages |
| 1,000,000,000 rows | 1,000,000,000 rows | about 5 pages |

The values are already sorted, so an index also helps with:

- **Range filters** such as `WHERE created_at > '2026-01-01'`.
- **Sorting** with `ORDER BY` on the indexed column, so no sort step is needed.
- **Joins** on the indexed column.
- **Covering queries.** These read only columns stored in the index, so the database skips the table entirely.

## When an index makes things slower

| Situation | Why it is slower |
|---|---|
| Heavy writes | Each insert, update and delete must also update every index |
| Query matches many rows | Many random lookups cost more than one sequential scan |
| Small table | A scan of a few pages beats walking a tree |
| Many indexes on one table | Indexes compete for cache memory |
| Unused index | Write cost with no read benefit |
| Bloated index | Deleted entries leave pages half empty |

The "matches many rows" case catches people out most often. Say a query returns 30% of a table. The index makes the database jump to a different place on disk for each row. One sequential read of the whole table is often faster. The query planner normally sees this and chooses a scan. Stale table statistics can lead it to pick the index anyway.

## When an index exists but is not used

These do not slow the query. They just leave the index unused while writes still pay for it.

- **A function on the column.** `WHERE LOWER(email) = ?` cannot use a plain index on `email`. It needs an index on `LOWER(email)`.
- **Wrong column order.** An index on `(a, b)` does not help `WHERE b = ?` on its own.
- **A leading wildcard.** `LIKE '%son'` cannot use a B-tree index.

## Rule of thumb

Index columns that frequent queries use in `WHERE`, `JOIN` or `ORDER BY`. The column should narrow results to a small share of rows. Run `EXPLAIN` on the query to confirm the planner uses the index. Drop indexes that no query uses.
