An index lets the database jump to matching rows instead of reading the whole table. It slows down writes, and it can slow reads when a query matches a large share of the table.

## How an index speeds up a read

Most indexes are B-trees. A B-tree is a sorted, balanced tree of key values. Each leaf entry points to a row on disk.

```
            ┌──────────────┐
            │  root: 50    │
            └──────┬───────┘
         < 50      │      ≥ 50
     ┌─────────────┴─────────────┐
┌────┴─────┐                ┌────┴─────┐
│ 10 · 30  │                │ 70 · 90  │
└────┬─────┘                └────┬─────┘
     │ points to                 │ points to
 leaf pages ─► row locations  leaf pages ─► row locations
```

The tree for a 100-million-row table is about four levels deep. A lookup reads about four pages. A full table scan reads every page.

| Query shape | Without index | With B-tree index |
|---|---|---|
| `WHERE id = 42` | Read every row | Walk about 4 pages |
| `WHERE date BETWEEN a AND b` | Read every row | Find start, read leaves in order |
| `ORDER BY date LIMIT 10` | Sort the whole table | Read first 10 leaf entries |
| `JOIN ON a.id = b.a_id` | Scan or hash the table | Look up each key |

A covering index holds every column the query needs. The database then answers from the index alone and never touches the table.

## When an index makes things slower

| Situation | Cost |
|---|---|
| Every insert, update or delete | Each index on the table must also change |
| Query matches a large share of rows | Random reads per row cost more than one sequential scan |
| Low-cardinality column, such as a status flag | Index barely narrows the search |
| Many unused indexes | Extra disk, memory and write time for no read benefit |
| Bulk loads | Index upkeep per row slows the load |

The large-share case is the one people miss. Each index hit is a random disk read to fetch the row. Past roughly 5 to 20 percent of the table, one sequential scan is faster. The query planner knows this and often skips the index. Stale table statistics can make it pick the index anyway, and the query gets slower.

## When the database cannot use an index

These query shapes stop the planner from using an index on a column:

- A function wrapped around the column, as in `WHERE LOWER(email) = 'x'`. An index on the expression fixes it.
- A leading wildcard, as in `LIKE '%smith'`.
- A composite index on `(a, b)` filtered only on `b`. The index is sorted by `a` first.
- A type mismatch that forces a cast on the column.

To check what the planner chose, run `EXPLAIN ANALYZE`. Postgres and MySQL both support it.
