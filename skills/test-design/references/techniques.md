# Derivation techniques

Selector: ranges → BVA+EP · combinational rules → decision table · stateful → state-transition · many params → pairwise · dense interlocked logic → cause-effect.

**Equivalence partitioning (EP).** Split each input into classes treated identically; test one representative per class, and every *invalid* class separately (never fold two invalid classes together — they mask each other). Age `18–65` → `10` (low), `40` (valid), `80` (high), `"x"` (type).

**Boundary value analysis (BVA).** Bugs cluster at edges (`<` vs `<=`, off-by-one). Per boundary test on-point and off-point: `min-1, min, min+1, max-1, max, max+1`. Cheapest, highest yield. `18–65` → `17,18,19,64,65,66`.

**Decision table.** For combinations of conditions. Columns = rules; one test per column after deleting impossible/redundant ones. `discount = isMember AND cartOver100` → 4 rows, only (T,T) gives the discount.

**State-transition.** For stateful features. Cover every valid transition once, then probe illegal events per state (the bug-rich part). Order `Created→Paid→Shipped→Delivered`/`Cancelled`; illegal: ship an unpaid order, pay a cancelled one, cancel a delivered one — each must be rejected.

**Pairwise/combinatorial.** Many params × several values explodes; most defects need only one factor or a pair. Use a generator (PICT, allpairs, Hypothesis). 4 params × 3 values = 81 full → ~9 pairwise.

**Cause-effect graphing.** Map input causes → effects via AND/OR/NOT, derive a decision table. Only for dense interlocking logic; otherwise go straight to a decision table.
