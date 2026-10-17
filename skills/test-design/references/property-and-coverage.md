# Property-based testing & coverage

## Property-based testing (Hypothesis / fast-check / jqwik)
State a property true for *all* inputs; the framework generates hundreds and **shrinks** failures to a minimal counterexample. Beats example tests for large/combinatorial spaces, parsers/serializers, data-structure invariants, numeric/financial logic.

Pick a property from four reliable patterns:
- **Round-trip / inverse** (start here, highest value): `decode(encode(x)) == x`, `parse(render(x)) == x`.
- **Invariant**: always true after the operation — sort output is ordered and a permutation of input; balance never negative; `f(f(x)) == f(x)`.
- **Oracle / model-based**: compare against a trusted slow-but-obvious reference or the old version.
- **Metamorphic** (when no oracle): relate related inputs/outputs — `sin(x) == sin(x+2π)`; doubling all prices doubles the total; `search(q)` ⊇ `search(q + filter)`.

Pitfalls: heavy input filtering (>~90% discarded) means redesign the generator; seed/derandomize in CI; save every shrunk counterexample as a permanent regression example.

## Coverage done right
- **Line coverage is weak** — it proves a line executed, not that an assertion checked it. 100% with zero assertions is achievable and meaningless. Branch coverage is slightly better, still execution-only.
- **Mutation testing is the real signal** — it injects small faults (`<`→`<=`, `+`→`-`, `&&`→`||`, remove a statement, negate a condition), reruns tests; a mutant is **killed** if a test fails. A surviving mutant = a bug the suite misses. Mutation score = killed / (total − equivalent). Tools: Stryker (JS/TS/C#), PITest (JVM), mutmut (Python), Infection (PHP). Cost: scope to changed files in PR CI, full run nightly.
- **Targets**: line/branch coverage is a floor ("no PR drops changed-line coverage below ~80%"); mutation score (~70–80%+ on critical logic) is the quality bar. High coverage + low mutation score = tests that run code without asserting on it — flag it.
