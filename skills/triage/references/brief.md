# Triage briefs

The brief is the contract for the next agent. Describe observable behavior and named interfaces; keep transient paths and line numbers in an evidence section rather than making them the specification. Every acceptance criterion must be independently checkable. Do not fill missing facts with a plausible implementation.

## Ready item

```markdown
> AI-assisted triage; evidence and remaining uncertainties are listed below.

Source: <issue or PR URL>
Category: <bug | enhancement | question/feedback>
State: <ready-for-agent | ready-for-human>
Summary: <specific requested outcome>

Current behavior: <observed result, version and relevant conditions>
Desired behavior: <user-visible result, including failure states>
Evidence: <reproduction, artifact links, existing implementation and uncertainties>
Key interfaces: <domain types, inputs, outputs, invariants or configuration>
Acceptance criteria:
- [ ] <action and independently observable expected result>
- [ ] <negative/boundary case and expected result>
Verification: <real surface, available harness and commands, known prerequisites>
Out of scope: <explicit adjacent work excluded>
Ownership/dependencies: <owner, prerequisite issue or access/decision needed>
```

For a PR, `Current behavior` states what the candidate diff already does and what remains missing. Preserve the contributor's work. For an enhancement, evidence can establish intent and current behavior without claiming an existing bug.

Done when: a fresh agent can identify the outcome, boundary and proof without asking what "fix it" means.

## Incomplete or non-actionable item

```markdown
> AI-assisted triage; evidence and remaining uncertainties are listed below.

Source: <URL>
State: <needs-triage | needs-info | duplicate | rejected>
Established: <facts with evidence links>
Uncertain: <unverified facts, inaccessible evidence or possible related reports>
Next step: <one specific check, question or canonical link>
Reason: <why this state follows from the evidence or maintainer decision>
```

An answer may contain several indispensable questions; do not ask for a full report again when only one fact is missing. A duplicate note explains the matching symptom/cause and links the canonical item. A rejection cites an established decision, not model preference. If authorized to persist a rejected enhancement, use the repo's existing decision record location and link the source; otherwise keep the proposed record in the report.

Done when: the reporter knows what information or decision would change the state.
