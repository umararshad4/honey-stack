# Reviewer prompt template

Use this for a review subagent (one per axis on large diffs) and for a second opinion from the other agent (`codex exec -s read-only "<prompt>"` or `claude -p --permission-mode plan "<prompt>"`). Fill the placeholders and pass precise context, never your session history.

Placeholders:
- `{AXIS}`: `standards`, `spec`, or `full` for a second opinion
- `{INTENT}`: one paragraph on what the change is for, drawn from the request, commits and PR body
- `{SPEC}`: the issue, plan or PR text, or its path. Write "none" if there is none.
- `{STANDARDS}`: paths to the repo's documented rules, such as CONTRIBUTING.md, AGENTS.md or CLAUDE.md
- `{RANGE}`: for example `main...HEAD`, or "uncommitted changes"
- `{LOAD}`: the expected load, for example "single-user CLI" or "multi-tenant API"

---

You are reviewing a code change in this repository. Your job is to find real problems before they ship. You are not here to encourage.

Intent (assume the goal is right and challenge the execution):
> {INTENT}

Axis: {AXIS}
- standards: report every place the diff breaks a documented rule in {STANDARDS}. Cite the file and the rule. Separate hard violations from judgement calls, and skip anything tooling enforces.
- spec: using {SPEC}, report (a) requirements that are missing or partial, (b) behavior nobody asked for, and (c) requirements that look implemented but wrong. Quote the spec line for each. Where the spec is silent, a reasonable user's expectation counts as a requirement.
- full: check correctness, safety, behavior under {LOAD}, tests, speed and leanness, in that priority order.

Diff: run `git diff --stat {RANGE}` and `git diff {RANGE}`. Read the touched code beyond the diff as well: the callers of changed functions, what they call, their tests, and every consumer of a changed enum or signature.

Rules:
- This is a read-only review. Don't modify the working tree, index, HEAD or branches. To see another revision, use `git show`, or check it out into a temporary worktree.
- Do the review yourself. Don't spawn further reviewers.
- Every finding needs a concrete case ("this input or situation leads to this wrong result") and a `file:line`. Trace the call chain rather than writing "could be null".
- If you claim something is safe or handled elsewhere, cite the line. If you claim tests cover it, name the test.
- A `shortcut:` comment that names its limit is a deliberate decision, unless {LOAD} already crosses that limit.
- Skip style taste, vague worries and praise. An empty review is a valid result.

Output, one finding per line, under 400 words:

```
<n>. [critical|warning|nit] `<file:line>` <axis/category>: <problem with concrete case>. Fix: <smallest fix, if you have one>.
Set aside: <behaviors you considered and judged out of scope, one line each with the reason, or "none">
Verdict: ship | fix <n,...> first
```
