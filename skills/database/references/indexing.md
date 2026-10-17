# Indexing

## Types
- **B-tree** (default): equality, range, sort, prefix.
- **GIN**: multi-value — JSONB, arrays, full-text `tsvector`, `pg_trgm` for `LIKE '%x%'`.
- **GiST**: geometric/range/nearest-neighbor (PostGIS, `tstzrange`, exclusion constraints).
- **BRIN**: huge append-only, naturally-ordered (time-series) — tiny, great when physical order ≈ logical.
- Hash: equality-only, rarely beats B-tree.

## Rules
- **Composite order**: equality columns first, then the range/sort column; the left prefix must match the query (`(a,b)` serves `WHERE a=` and `WHERE a= AND b=`, not `b` alone — PG18 skip scan helps partly). Order the equality group by selectivity.
- **Covering**: `CREATE INDEX … (a,b) INCLUDE (c)` → index-only scan (needs a well-vacuumed table for the visibility map).
- **Partial**: `CREATE INDEX … WHERE status='active'` — smaller/faster for skewed predicates and soft-delete.
- **Cost**: every index adds write amplification and bloats on updates. Keep write-heavy tables lean; drop redundant/overlapping indexes.

## Reading EXPLAIN (ANALYZE, BUFFERS)
`ANALYZE` executes the query — don't run on mutating statements in prod without a transaction + rollback. Watch for: `Seq Scan` on a big table; estimated-vs-actual row divergence (stale stats → `ANALYZE`); high `Rows Removed by Filter` (missing index); nested-loop blowups; `BUFFERS` high `read` vs `hit` (cold/under-cached); `Sort`/`Hash` "external merge Disk" (`work_mem` too low). `auto_explain` captures prod plans.

```sql
-- unused indexes
SELECT relname, indexrelname, idx_scan FROM pg_stat_user_indexes WHERE idx_scan=0 ORDER BY pg_relation_size(indexrelid) DESC;
-- tables doing seq scans
SELECT relname, seq_scan, idx_scan FROM pg_stat_user_tables ORDER BY seq_scan DESC;
```
