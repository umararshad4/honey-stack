# Safe / online migrations

## Expand–contract (parallel change)
1. **Expand**: add a new nullable column / new table / new index — backward compatible.
2. Backfill in batches + dual-write from the app.
3. Switch reads to the new shape.
4. **Contract**: drop the old column/table in a *later* deploy. Never rename in place on a live table.

## Dangerous ops (table rewrite / long ACCESS EXCLUSIVE lock)
Changing a column type; `SET NOT NULL` (full scan); adding a column with a volatile default (modern PG: a *constant* default is metadata-only). A migration waiting for `ACCESS EXCLUSIVE` blocks every query behind it.

Safe NOT NULL on a big table: add nullable → backfill in batches → `ADD CONSTRAINT … CHECK (col IS NOT NULL) NOT VALID` → `VALIDATE CONSTRAINT` (takes only `SHARE UPDATE EXCLUSIVE`, no full-table exclusive lock) → optionally `SET NOT NULL` (PG12+ uses the validated constraint to skip the scan).

## Always
- `CREATE INDEX CONCURRENTLY` on live tables (no write lock; runs outside a txn; can leave an INVALID index on failure → drop and retry).
- `SET lock_timeout = '2s'` so a blocked migration fails fast instead of queuing.
- Backfill in batches (1–10k rows/txn with a pause) to avoid long transactions, lock buildup and replication lag.

## Tools
Prisma Migrate, Drizzle Kit, Flyway, Liquibase, Alembic, Rails (+ `strong_migrations`), **Atlas** (`atlas migrate lint` flags unsafe changes). MySQL online DDL: gh-ost, pt-online-schema-change.

Every migration needs a tested down path or a forward-fix plan; destructive steps are a separate, later, reviewed migration. **Confirm with the user before running any migration against production** — and rehearse on a prod-sized copy first.
