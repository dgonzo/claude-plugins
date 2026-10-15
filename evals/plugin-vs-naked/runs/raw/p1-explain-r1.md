An index is a separate data structure that keeps a column's values in sorted or hashed order, and each entry points to the row it came from. The database stores and maintains it next to the table.

## How it speeds up a query

**Without an index**, a query like `WHERE email = 'a@b.com'` needs a **full table scan**. The database reads every row and checks it, which is O(n) work. With 100M rows, that means reading the whole table from disk.

**With a B-tree index** (the default in most databases), values are kept sorted in a shallow, wide tree. Each node holds hundreds of keys, so even a billion rows need only about 3–5 levels. A lookup reads a handful of pages instead of millions, which is O(log n).

A sorted index also helps beyond exact matches:
- **Range queries**: `WHERE created_at BETWEEN x AND y` finds the start point and reads forward.
- **ORDER BY / LIMIT**: rows already come out in order, so no sort step is needed.
- **Joins**: lookups into the inner table are fast (nested-loop joins).
- **MIN/MAX**: the answer is at one end of the tree.
- **Covering indexes**: if the index holds every column the query needs, the database never touches the table ("index-only scan").

**Composite indexes** `(a, b, c)` follow the leftmost-prefix rule. They help filters on `a`, on `a, b`, or on `a, b, c`, but generally not a filter on `b` alone. It works like a phone book sorted by last name, then first name.

## When an index makes things slower (or doesn't help)

**1. Writes get more expensive.** Every `INSERT`, `UPDATE` (of an indexed column) and `DELETE` must also update every index on the table. Ten indexes means roughly ten extra structures to change, with possible page splits, more locking, and more write-ahead log volume. Write-heavy tables pay for this constantly.

**2. Low-selectivity queries.** If a query matches a large share of the table (say 20%+, like `WHERE status = 'active'` when most rows are active), using the index is slower than scanning. Each index hit can mean a random read to fetch its row. Reading the table sequentially is much cheaper per row than jumping around randomly, so the optimizer usually picks a scan, and forcing the index hurts.

**3. Storage and memory pressure.** Indexes take disk space and compete for the buffer cache. Too many indexes can push hot data out of memory, which slows unrelated queries.

**4. The index can't be used for the query as written:**
- Functions on the column: `WHERE LOWER(email) = ...` won't use a plain index on `email` (you'd need an expression index).
- Leading wildcards: `LIKE '%foo'`.
- Implicit type casts, e.g. comparing a string column to a number.
- `OR` conditions across different columns (sometimes).
- Not following the leftmost prefix of a composite index.

**5. Small tables.** For a few hundred rows, a scan fits in a page or two, and the index lookup only adds overhead.

**6. Planner mistakes.** Out-of-date statistics can lead the optimizer to choose an index when a scan would be better, or the other way around.

**7. Bloat and fragmentation.** Heavy update/delete churn can leave indexes bloated. They grow larger and slower until rebuilt (`REINDEX`, `VACUUM`, etc.).

## Rule of thumb

Index columns that are used often in `WHERE`, `JOIN` and `ORDER BY` clauses and that are **selective** (they narrow the result to a small fraction of rows). Avoid indexing everything on write-heavy tables. Check what the database actually does with `EXPLAIN` / `EXPLAIN ANALYZE` instead of guessing, and drop indexes that monitoring shows are never used (e.g. `pg_stat_user_indexes` in Postgres).
