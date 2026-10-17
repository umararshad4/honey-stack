# Transactions & concurrency

## Isolation levels (Postgres) and what each allows
- `READ COMMITTED` (default): no dirty reads; allows non-repeatable reads, phantoms, lost updates, read skew.
- `REPEATABLE READ` (snapshot): no dirty/non-repeatable/phantom reads; **allows write skew**; serialization failures possible → retry.
- `SERIALIZABLE` (SSI): prevents all of the above; may abort with `could not serialize access` (SQLSTATE `40001`) → **retry loop required**.

## Locking
- **Optimistic** (low contention): version column; `UPDATE … WHERE id=$1 AND version=$2`; 0 rows → someone else won → retry.
- **Pessimistic** (high contention / money): `SELECT … FOR UPDATE` (row lock); `FOR NO KEY UPDATE`/`FOR SHARE`; `SKIP LOCKED` for queue/worker patterns; `NOWAIT` to fail fast.
- **Deadlocks** (two txns lock in opposite order): lock in a consistent order, keep transactions short, retry on `40P01`. Postgres auto-aborts one victim.

## Idempotency
For retried operations (payments, webhooks, at-least-once queues): idempotency key + unique constraint + `INSERT … ON CONFLICT DO NOTHING`, or an outbox table. Make retries safe by construction.
