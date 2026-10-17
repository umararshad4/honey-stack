---
type: llm
---

PASS if the reply plans to reproduce the failure reliably (a loop or repeated runs) and to test specific hypotheses about why `currency` is missing before proposing a fix.
FAIL if it jumps straight to a code fix (for example `.get('currency', default)`) without first reproducing the failure or testing hypotheses.
