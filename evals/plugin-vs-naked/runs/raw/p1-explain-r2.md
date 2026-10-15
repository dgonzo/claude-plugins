## How an index speeds up a query

Without an index, a query like `WHERE email = 'a@b.com'` has to do a **full table scan**: read every row and check it. That costs O(n).

An index is a separate data structure, usually a **B-tree** (or B+tree), that stores the indexed column's values in sorted order, each with a pointer to its row. Because it's sorted and balanced, the database can:

- **Find exact matches** in O(log n) by walking the tree. With millions of rows, that's about 3–4 page reads instead of thousands.
- **Handle range queries** (`BETWEEN`, `<`, `>`, `LIKE 'abc%'`) by finding the start point and then reading neighboring entries in order.
- **Skip sorting** for `ORDER BY` on the indexed column, because the data is already in order.
- **Speed up joins**, since looking up matching rows in the other table becomes cheap.
- **Answer some queries from the index alone** (a "covering index"). If every column the query needs is in the index, the database never reads the table.

Other index types do other jobs. Hash indexes are fast for equality but useless for ranges. GIN and inverted indexes handle full-text search and arrays. GiST and R-tree indexes handle geospatial data. BRIN indexes work well for huge tables that are naturally ordered, such as by timestamp.

## When an index makes things slower (or doesn't help)

**1. Writes get more expensive.**
Every `INSERT`, `UPDATE` (of an indexed column) and `DELETE` must also update every index on the table. A table with 8 indexes does about 9 writes per insert. Write-heavy workloads such as logging, event ingestion and bulk loads can suffer badly. That's why people often drop indexes before a bulk load and rebuild them afterwards.

**2. Low selectivity.**
If a query returns a large share of the table (say more than 5–20%), using the index is slower than a sequential scan. Each match means a jump to a random page in the table, and random I/O is much slower than reading straight through. An index on a column like `is_active` or `gender` rarely helps. Good query planners notice this and ignore the index, but the index still costs you on every write.

**3. Storage and memory pressure.**
Indexes take disk space and compete for the buffer cache. Too many indexes can push hot table data out of memory, which slows down everything.

**4. Queries that can't use the index.** In these cases you pay the cost of keeping the index without getting any benefit:
- Wrapping the column in a function: `WHERE LOWER(email) = ...` or `WHERE YEAR(created_at) = 2026` (unless you build an expression index)
- A leading wildcard: `LIKE '%abc'`
- Implicit type casts, such as comparing a string column to a number
- Multi-column indexes used out of order: an index on `(a, b)` helps `WHERE a = ?` and `WHERE a = ? AND b = ?`, but not `WHERE b = ?` alone
- `OR` conditions across different columns, in some databases

**5. Small tables.**
If the whole table fits in a few pages, scanning it is already as fast as walking an index.

**6. Planner mistakes.**
Stale statistics can make the optimizer pick an index when a scan would be faster, or the reverse. Running `ANALYZE` or updating statistics usually fixes this.

**7. Index bloat and fragmentation.**
Heavy updates and deletes can leave indexes fragmented or bloated, as happens in Postgres. Lookups then touch more pages until you rebuild or reindex.

**8. Lock and contention hotspots.**
An index on a value that always increases, like an auto-increment ID or a timestamp, sends every insert to the same rightmost page. Under very high concurrency, that page becomes a contention point.

## Rules of thumb

- Index columns that appear often in `WHERE`, `JOIN` and `ORDER BY` and that are highly selective.
- In composite indexes, put equality columns first, then range columns.
- Use `EXPLAIN` / `EXPLAIN ANALYZE` to check that an index is actually used, rather than guessing.
- Periodically find and drop unused indexes. Postgres tracks this in `pg_stat_user_indexes` and MySQL in `sys.schema_unused_indexes`.
- For read-heavy tables, more indexes are usually fine. For write-heavy tables, keep them few.
