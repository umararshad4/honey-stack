# Bounded model-checking recipe

Use the project's existing checker and pinned tool version when present. For TLC, locate Java and the official `tla2tools.jar`; record their versions and the jar's release provenance. If absent, use the host's approved tool-install path or report the prerequisite. Do not install a global Java runtime just to render a diagram.

Write `Flow.tla` and `Flow.cfg` in the same scratch directory. Model named actions separately in `Next`, so the trace explains what happened. Keep bounds small enough to explore fully, then increase them deliberately. A timed-out, cancelled or out-of-memory search is incomplete, even if no violation was found yet.

Example invocation, after resolving the actual jar path:

```sh
java -cp /resolved/path/tla2tools.jar tlc2.TLC -config Flow.cfg Flow.tla > check.log 2>&1
```

Read the exit code and the complete summary in `check.log`. Record distinct states, search depth, runtime, configured constants and any fairness constraints. A syntax error is not a counterexample. Preserve the model, config and log as evidence; link them from the report.

Try a known-bad variant of the model or an intentionally false invariant: the checker must detect it. Keep that control separate from the model used for the final result. Do not substitute a Python simulation or static source grep for an unavailable TLC run.

## Report

```text
Property: <invariant in domain terms>
Code mapping: <actual transitions inspected>
Assumptions / bounds: <actors, retries, values, atomicity, fairness>
Checker: <tool/version, exact command, exit code>
Result: violation | no violation within bounds | incomplete | unverified
Coverage: <states/depth or equivalent from checker output>
Counterexample: <action path, or none returned>
Real-code reproduction: confirmed | not reproduced | not attempted
Artifacts: <model, config, log, diagram>
```
