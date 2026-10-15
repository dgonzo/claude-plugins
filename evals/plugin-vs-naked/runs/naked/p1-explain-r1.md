An index is a separate data structure that keeps a copy of one or more columns in sorted order, with each entry pointing back to its row. The most common kind is a B-tree. It lets the database find rows without reading the whole table.

## How it speeds things up

**Without an index**, `WHERE email = 'x@y.com'` needs a full table scan. The database reads every row and checks each one, so the cost is O(n). With 100M rows, that's 100M checks and a lot of disk I/O.

**With a B-tree index**, the database walks a shallow tree from the root to a leaf. Each node holds hundreds of keys, so even a billion rows need only about 3–4 levels. That's a handful of page reads (O(log n)) instead of millions.

An index also helps with:
- **Range queries** (`WHERE created_at BETWEEN ...`): find the start point, then read the leaves in order.
- **ORDER BY / GROUP BY**: the data is already sorted, so the sort step can be skipped.
- **Joins**: an index on the join key lets the database look up matching rows directly.
- **Covering indexes**: if the index holds every column the query needs, the database never touches the table at all ("index-only scan").
- **Uniqueness checks**: duplicates are found with a quick lookup.

## When an index makes things slower

1. **Writes get more expensive.** Every `INSERT`, `UPDATE` (of an indexed column) and `DELETE` must also update every affected index. A table with 10 indexes does about 11 writes per insert, plus possible page splits and extra locking. Write-heavy tables pay heavily for indexes nobody uses.

2. **Low-selectivity queries.** If the filter matches a large share of the table, such as `WHERE status = 'active'` when 80% of rows are active, using the index means one random lookup per matching row. Reading the table sequentially is faster. The planner usually knows this and skips the index. It can still choose badly if its statistics are stale.

3. **Bad estimates and plan choices.** Outdated statistics or correlated columns can trick the optimizer into an index scan that's much slower than a sequential scan. Running `ANALYZE` or updating statistics often fixes it.

4. **Storage and memory pressure.** Indexes use disk and compete for buffer cache. Too many large indexes can push hot table data out of memory and slow everything down.

5. **Very small tables.** If the table fits in a page or two, a scan is already cheap and the index lookup only adds overhead.

## When an index exists but doesn't help

These cases don't slow anything down, but they're common surprises:
- **A function on the column**: `WHERE LOWER(email) = ...` can't use an index on `email`. You need an expression index.
- **Leading wildcards**: `LIKE '%foo'` can't use a B-tree.
- **Wrong column order in a composite index**: an index on `(a, b)` helps `WHERE a = ?` and `WHERE a = ? AND b = ?`, but not `WHERE b = ?` on its own.
- **Implicit type casts**: comparing a string column to a number can rule out the index.

## Rule of thumb

Index columns that appear often in `WHERE`, `JOIN` and `ORDER BY` and that filter down to a small fraction of rows. Avoid speculative indexes on write-heavy tables. Use `EXPLAIN` (or `EXPLAIN ANALYZE`) to see whether the planner actually uses an index. Most databases can also report unused indexes (for example, Postgres's `pg_stat_user_indexes`), and those are good candidates to drop.
