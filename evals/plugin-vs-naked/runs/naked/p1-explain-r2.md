## How an index speeds up a query

Without an index, a query like `WHERE email = 'x@y.com'` makes the database read every row in the table (a **full table scan**), which costs O(n).

An index is a separate data structure, usually a **B-tree** (B+tree in most engines), that keeps the indexed column's values sorted, and each value points back to its row. Because the tree is wide and shallow (often hundreds of keys per node), finding a value takes only a few page reads, even with hundreds of millions of rows. That's O(log n).

Because the values are sorted, an index helps with more than exact matches:

- **Range queries:** `WHERE created_at BETWEEN ...` finds the start point, then walks the leaf pages in order.
- **ORDER BY / GROUP BY:** rows already come out in order, so no separate sort step is needed.
- **Joins:** a nested-loop join can look up each matching row instead of scanning the inner table.
- **MIN/MAX:** it just reads one end of the tree.
- **Covering indexes:** if the index contains every column the query needs (`INCLUDE` columns or a composite index), the database never touches the table at all ("index-only scan").

Other index types use the same idea for different jobs. **Hash** indexes are fast for equality but can't handle ranges. **GIN** indexes handle arrays, JSONB and full-text search. **BRIN** indexes are tiny summaries for huge, naturally ordered tables. **Bitmap** indexes suit low-cardinality columns in analytics databases.

## When an index makes things slower

**1. Writes.** Every INSERT, UPDATE of an indexed column, and DELETE must also update every index on the table. A table with 10 indexes does roughly 11 writes per insert. Page splits, extra WAL/redo log volume and lock contention add more cost. Write-heavy tables pay the most.

**2. Low selectivity.** If a filter matches a large share of the table (e.g. `WHERE status = 'active'` when 80% of rows are active), using the index means many **random** reads: one index lookup, then a jump to the table, for each row. A sequential scan reads pages in order and is often faster. Optimizers usually switch to a scan somewhere around 5–20% of rows, depending on the engine and storage. If the optimizer picks the index anyway, usually because of stale statistics, the query gets slower.

**3. Storage and memory.** Indexes take disk space and compete for the buffer cache. Too many indexes can push hot data out of memory, which slows down *other* queries.

**4. Wrong index or bad plan.** The optimizer may choose a worse index based on bad estimates. Extra indexes also give the planner more options to consider, and occasionally more ways to choose badly.

**5. Bulk loads.** Loading millions of rows into an indexed table is much slower than loading first and building the index afterward.

**6. Maintenance.** Indexes can bloat or fragment over time (especially in Postgres with heavy updates), which means more pages to read. In Postgres, an update to an indexed column also prevents HOT updates.

## When an index exists but isn't used

These cases don't make things slower, but the index adds write cost without helping any reads:

- A function on the column: `WHERE LOWER(email) = ...` won't use a plain index on `email`. Use an expression index.
- A leading wildcard: `LIKE '%foo'`.
- Implicit type casts, e.g. comparing a varchar column to a number.
- Composite indexes where the query skips the leading column. An index on `(a, b)` helps `WHERE a = ?` and `WHERE a = ? AND b = ?`, but generally not `WHERE b = ?`.
- `OR` conditions spread across different columns (sometimes).

## Rule of thumb

Index columns that appear in selective `WHERE` clauses, join keys, and `ORDER BY` clauses of frequent queries. Check with `EXPLAIN ANALYZE` that the index is actually used, and drop indexes that are never used (in Postgres, `pg_stat_user_indexes` shows usage). Every index is a trade: faster reads in exchange for slower writes and more storage.
