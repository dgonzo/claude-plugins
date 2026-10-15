An index lets the database find matching rows without reading every row. It costs extra work on every write and helps only when a query filters out most of the table.

## How an index speeds up a read

Without an index, the database reads every row and checks each one. This is a full table scan. Its cost grows with the size of the table.

Most indexes are B-trees. A B-tree keeps the indexed column's values sorted, and each value points to its row. The database walks from the root to a leaf in a few steps.

```
                 ┌───────────┐
                 │  50 | 100 │          root
                 └─┬───┬───┬─┘
         ┌─────────┘   │   └─────────┐
   ┌─────┴────┐  ┌─────┴────┐  ┌─────┴────┐
   │ 10 | 30  │  │ 70 | 90  │  │ 120 | 150│   inner pages
   └──┬───────┘  └──┬───────┘  └──┬───────┘
      ▼             ▼             ▼
   leaf pages: sorted keys, each pointing to a row
```

A table of 100 million rows needs about 4 page reads to find one key. A scan reads every page.

Sorted keys also help with these queries:

- Range filters such as `WHERE price BETWEEN 10 AND 20`
- `ORDER BY` on the indexed column, which skips the sort step
- `MIN` and `MAX`, read from the ends of the tree
- Joins, which can look up each matching row
- Covering queries. If the index holds every column the query needs, the database never opens the table.

## When an index makes things slower

| Situation | Why it is slower |
|---|---|
| Inserts, updates and deletes | Every index on the table must also change |
| Low-selectivity filter | Jumping from index to row costs more than a scan |
| Small table | A scan of a few pages is faster than a tree walk |
| Too many indexes | Writes slow down and memory fills with index pages |
| Unused or duplicate index | It costs writes and storage and helps no query |
| Random keys such as UUIDv4 | Inserts land on random pages and split them |
| Stale statistics | The planner picks the index when a scan would win |

Low selectivity needs a closer look. Say a filter matches 30% of rows. The index finds them, but each match needs a separate random read of the table. Reading the whole table in order is often faster. Most planners switch to a scan once a filter matches more than about 5 to 20% of rows.

## When the database ignores an index

A query can bypass an index that exists. The usual causes:

- A function wraps the column, as in `WHERE LOWER(email) = 'x'`. Fix it with an index on the expression.
- A pattern starts with a wildcard, as in `LIKE '%son'`.
- The filter skips the first column of a composite index. An index on `(a, b)` does not help `WHERE b = 1`.
- The column and the value have different types, which forces a cast.

## Rules of thumb

1. Index columns that appear in `WHERE`, `JOIN` and `ORDER BY` on large tables.
2. Put the most-filtered column first in a composite index.
3. Check the plan with `EXPLAIN` or `EXPLAIN ANALYZE` before and after adding an index.
4. Drop indexes that no query uses. PostgreSQL shows usage counts in `pg_stat_user_indexes`.
5. Write-heavy tables need fewer indexes than read-heavy ones.
