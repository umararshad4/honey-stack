# Edge-case checklists

Run the data-type lists over each input, then the systemic list over the feature's architecture. Keep what applies.

## By data type
**Strings:** empty, whitespace-only, leading/trailing spaces; very long (1, 10^6, DB limit ±1); unicode (accents, CJK, RTL/bidi, combining marks); emoji incl. ZWJ `👨‍👩‍👧` (length vs grapheme mismatch); normalization NFC vs NFD; case-folding (Turkish ı, German ß); null bytes `\0`; control chars/newlines; injection (`'; DROP TABLE`, `<script>`, `{{7*7}}`, `../`, `${}`); homoglyphs; trimming that changes meaning.

**Numbers:** `0`, `-0`, negatives, `±1`; max/min signed int and overflow; float precision (`0.1+0.2 != 0.3`); rounding half-even vs half-up; `NaN`, `±Inf`; divide-by-zero; integer truncation; locale decimal separator; leading zeros; scientific notation.

**Collections:** empty; single; at-capacity and +1; huge; duplicates; all-identical; `null` elements inside; nested/cyclic; unsorted when sorted assumed; concurrent modification; unordered set/map iteration.

**Dates/time:** store UTC, render local; DST — the skipped hour (spring-forward, a local time that doesn't exist) and the repeated hour (fall-back, ambiguous); leap years (2000 yes, 1900 no) and Feb 29; leap seconds; epoch 1970 and the 2038 32-bit overflow; month/year rollover (Jan 31 + 1 month); midnight boundaries; `start > end`; far future/past; locale formats (MM/DD vs DD/MM); clock going backward (NTP).

**Money:** never float — integer minor units or decimal; one defined rounding mode; currency mismatch in arithmetic; conversion rounding order; negative/zero; very large totals; split-with-remainder (sum of parts must equal the whole — the penny test); min/max limits; non-2-decimal currencies (JPY=0).

**IDs/auth:** missing/null/empty; malformed; well-formed but nonexistent; another user's ID (IDOR — authorization, not just authentication); expired/revoked token; privilege level (user vs admin); case sensitivity; replayed; sequential-guessable; injection via the ID param.

## Systemic ("unthinkable")
- **Concurrency/races:** two writers on one row (lost update); check-then-act (balance check then withdraw); double-submit; deadlock/lock ordering → optimistic locking/version or `SELECT…FOR UPDATE`.
- **Idempotency/retries:** same request twice (dup charge/email); idempotency keys; at-least-once delivery → operations safe to repeat.
- **Ordering:** events out of order; stale update overwriting newer; read-after-write under eventual consistency.
- **Partial failure:** step 3 of 5 fails — rolled back or orphaned? saga/compensation; debit succeeds, credit fails.
- **Network:** timeout (did the op actually complete server-side? ambiguous); slow; offline; drop mid-response; truncated response; retry storms; circuit breaker.
- **Resource exhaustion:** disk full, OOM, pool/FD exhaustion, rate limit, zip-bomb/large payload.
- **Clock skew:** servers disagree; token expires before issued; cache TTL; cert windows.
- **Pagination:** empty first page; exactly page-size; last partial page; beyond end; cursor invalidated by insert/delete mid-scan (row skipped/duplicated); huge offset; changing sort key.
- **Caching:** stale read after write; thundering herd on expiry; cache/DB divergence; negative-result caching; key collisions.
- **Compatibility:** old client ↔ new server; a new enum an old reader doesn't know; added/removed field; migration mid-flight.
- **i18n/locale & accessibility:** pluralization, RTL, collation per locale; keyboard-only, screen-reader labels, focus order, contrast (flag a11y cases for `qa`, don't duplicate browser work).
- **Error-path/rollback:** failure path restores invariants; error message leaks no secrets; cleanup runs on exception.
