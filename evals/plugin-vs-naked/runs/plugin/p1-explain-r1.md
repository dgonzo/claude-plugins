An index lets the database find matching rows without scanning the whole table. Every write must also update the index, and some reads cost more through an index than a full scan.

## How an index speeds up a read

Most databases store an index as a B-tree. That is a sorted, balanced tree of key values. Each leaf entry points to a row on disk.

```
            ┌───────────────┐
            │  root: 50     │
            └──────┬────────┘
          < 50     │     ≥ 50
     ┌─────────────┴─────────────┐
┌────▼──────┐              ┌─────▼─────┐
│ 10 · 30   │              │ 70 · 90   │
└────┬──────┘              └─────┬─────┘
     │ points to                 │ points to
┌────▼──────────┐          ┌─────▼──────────┐
│ leaf: key→row │          │ leaf: key→row  │
└───────────────┘          └────────────────┘
```

Without an index, `WHERE email = 'x'` reads every row. That is O(n). With an index, the database walks root to leaf in O(log n) steps. A table of 100 million rows needs about 4 page reads instead of millions.

Sorted leaves also help with these query shapes:

| Query shape | Why the index helps |
|---|---|
| Equality, `WHERE id = 7` | One tree walk |
| Range, `WHERE date BETWEEN a AND b` | Walk once, then read adjacent leaves |
| `ORDER BY` on the indexed column | Rows come out pre-sorted |
| Join on the indexed column | Fast lookup per outer row |
| Covering index | Answer comes from the index alone, with no table read |

## When an index makes things slower

| Situation | Cost |
|---|---|
| Heavy `INSERT`, `UPDATE`, `DELETE` | Each index is one more structure to write |
| Low selectivity, e.g. `status = 'active'` on 90% of rows | Random row lookups cost more than one sequential scan |
| Many indexes on one table | More disk, more memory, slower writes |
| Function on the column, e.g. `LOWER(email)` | Plain index unused. Needs an expression index |
| Leading wildcard, `LIKE '%abc'` | B-tree order does not apply |
| Composite index, wrong column order | Index on `(a, b)` does not serve `WHERE b = ?` |
| Small table | A full scan of a few pages beats a tree walk |
| Bloated or stale index | Extra pages to read. Planner statistics mislead |

The low-selectivity case surprises people most. A sequential scan reads pages in order, which disks and caches handle well. An index scan jumps to a random page for each match. Past roughly 5 to 20 percent of rows, the scan wins. The exact point depends on the engine and hardware. Query planners estimate this and often ignore the index.

## Practical rule

1. Index columns that appear in selective `WHERE`, `JOIN` and `ORDER BY` clauses.
2. Run `EXPLAIN ANALYZE` to check that the planner uses the index.
3. If a table takes many writes and few reads, keep its indexes few.
4. Drop indexes that usage statistics show nobody reads. In PostgreSQL that view is `pg_stat_user_indexes`.
