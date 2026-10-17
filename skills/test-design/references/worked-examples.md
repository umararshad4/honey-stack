# Worked examples

## transfer(fromId, toId, amount, idemKey)
Invariants: debit == credit; total money conserved; `from.balance` never negative; atomic (both or neither); idempotent per key.

- **Happy/EP:** valid transfer within balance (both updated, total conserved); exact-whole-balance (→0).
- **BVA on amount:** `0` (reject), negative (reject), `1`, `balance` (ok), `balance+1` (insufficient funds), overflow of total, sub-cent precision (reject or defined rounding).
- **Money:** two currencies (reject or convert — define); integer minor units (not float); conservation (sum of parts = whole).
- **IDs/auth:** `fromId == toId` (define: no-op or reject); nonexistent from/to; caller not authorized on `from` (IDOR); frozen/closed account.
- **State:** transfer from/to a closed account; account closed mid-transfer.
- **Idempotency:** same `idemKey` twice → exactly one transfer; retry after a client timeout where the server committed → no double debit.
- **Concurrency (the nasty ones):** two concurrent transfers from one account that each pass the balance check but together overdraw → must not go negative; A→B and B→A concurrently (deadlock/lock ordering); no dirty read of balance mid-transfer.
- **Partial failure:** credit fails after debit succeeds → full rollback, `from` restored, no orphaned money; crash between debit and credit → recovery keeps the invariant.
- **Property-based:** after any sequence of valid+invalid transfers, `sum(all balances) == initial total` and no balance < 0; transfer X then X back returns to start.

Levels: validation/BVA/self-transfer → unit (mocked repo). Rollback, idempotency, concurrency, conservation → **integration with a real transactional DB** (mocks can't exercise locking or atomicity). No E2E unless there's a UI journey.

## Paginated search
Empty result; exactly page-size; last partial page; page beyond end (empty vs error); invalid/huge/negative page or offset; **cursor invalidated by insert/delete between pages** (row skipped or duplicated — the classic offset-pagination bug → cursor-based fix); changing sort key mid-scan; duplicate sort-key values (unstable order); very large page size; unicode/injection in the query; default sort; total-count accuracy vs performance. Property: concatenating all pages = the full ordered result set, no gaps or dupes. Level: integration with a real data store (pagination bugs live at the query boundary).
