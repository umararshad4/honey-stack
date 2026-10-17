# Schema design

Postgres 18 adds native `uuidv7()`, B-tree skip scan, OR-condition index use, async I/O. `uuidv7()`/skip scan don't exist pre-18 — branch advice on version.

## Primary keys
- `bigint GENERATED ALWAYS AS IDENTITY` — default for internal tables. 8 bytes, monotonic → tight B-tree, no page splits. Downside: enumerable, leaks counts.
- **UUIDv7** — exposed/client-generated/sharded IDs. Time-ordered → near-sequential insert locality (UUIDv4 fragments the index with random page writes + WAL bloat). Store as native `uuid` (16 bytes), never `varchar` (37 bytes, slow compares).
- ULID overlaps v7; prefer v7 when you can store native `uuid`.

## Constraints (invariants the app can't bypass)
`FOREIGN KEY` + **index the FK column** (Postgres does NOT auto-index FKs → slow cascades, lock escalation). `UNIQUE`, `CHECK`, `EXCLUDE`. Name them for stable migration references.

## JSONB vs columns
Columns for anything filtered/joined/aggregated/constrained. JSONB only for schemaless/sparse/rarely-queried blobs — don't rebuild a schema in JSONB (you lose types, NOT NULL, FKs, good plans). Query inside JSONB → GIN index (`jsonb_path_ops` for `@>` containment) or an expression index on the extracted field.

## Soft vs hard delete
Soft (`deleted_at timestamptz`) for audit/recovery/undo: every query needs `WHERE deleted_at IS NULL` (partial index on it), unique constraints must include the deleted dimension, data grows unbounded. Hard delete (or archive table) for GDPR deletion or volume.
