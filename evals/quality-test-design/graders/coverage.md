---
type: llm
---
PASS if the list goes well beyond happy-path and boundary amounts to include at least THREE of these hard/systemic cases: concurrent transfers that together overdraw the account (race / lost update), idempotency or double-submit / retry safety, partial-failure rollback (debit succeeds but credit fails), money precision/rounding or float avoidance, and same-account or closed/nonexistent-account handling.
FAIL if it only lists obvious cases (valid transfer, zero, negative, insufficient funds) and misses the concurrency / idempotency / partial-failure class entirely.
