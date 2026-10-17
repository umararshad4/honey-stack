---
type: llm
---
PASS if the response insists on reliably reproducing the intermittent failure first (e.g. running the test in a loop until it fails) AND forming specific hypotheses about why `currency` is sometimes missing (e.g. test ordering/shared state, a race, non-deterministic fixture data) before proposing a fix.
FAIL if it jumps straight to a code patch (like `.get('currency')` or a try/except) without first reproducing the flake or investigating why it is intermittent.
