# Query performance & N+1

## N+1
One query for N parents, then one per child. Detect: the same parametrized query running N times (test query-count assertions, APM span counts, slow query log). Fix with eager/batch loading:
- Prisma `include`/`select`; SQLAlchemy `selectinload`/`joinedload`; Django `select_related`/`prefetch_related`; ActiveRecord `includes`.
- GraphQL: **DataLoader** to batch + dedupe per-request field resolution.

## Finding slow queries
```sql
SELECT query, calls, total_exec_time, mean_exec_time, rows
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20;
```
Enable the slow log: `log_min_duration_statement = 500ms`.

## Patterns
- **Keyset/cursor pagination** instead of deep `OFFSET` (which scans and discards): `WHERE (created_at, id) < ($1,$2) ORDER BY created_at DESC, id DESC LIMIT 20` with a matching composite index and a unique tiebreaker.
- No `SELECT *` — fetch explicit columns (enables index-only scans, smaller payloads, survives schema change).
- Batch: multi-row `INSERT`, `COPY` for bulk, `= ANY($1)` for multi-key reads.

## Connection pooling
Postgres backends are heavy; cap connections below `max_connections`. Use **PgBouncer** (transaction mode is the sweet spot). **Serverless pitfall**: each function instance opens its own connection → exhaustion; use a pooler/proxy (PgBouncer, RDS Proxy, Supabase/Neon pooled endpoint, Prisma Accelerate). Transaction-mode pooling breaks prepared statements, `SET`, advisory locks, `LISTEN/NOTIFY` — configure the driver.
