# Spec and ticket templates

Distilled from mattpocock/skills `to-spec`, `to-tickets`, `to-prd`, `to-issues` (MIT, Matt Pocock).

## Spec

Write it to `docs/specs/YYYY-MM-DD-<slug>.md`, or as a GitHub issue labeled `spec` when tickets go to GitHub. Use the project's domain vocabulary and respect ADRs in the area.

```markdown
## Problem
<The user's problem, from their perspective.>

## Solution
<The solution, from the user's perspective.>

## User stories
1. As a <actor>, I want <feature>, so that <benefit>.
<Long and numbered; cover every aspect of the feature.>

## Implementation decisions
<Modules built or modified, their interfaces, schema changes, API contracts, architectural decisions. No file paths or code: they go stale. Exception: a snippet from a prototype that encodes a decision more precisely than prose (state machine, reducer, schema, type shape), trimmed and marked as from a prototype.>

## Testing decisions
<What a good test looks like here (external behavior, not internals), which modules get tested, at which seam, and prior art in the repo. Prefer existing seams, the highest one that reaches the behavior, and as few as possible.>

## Out of scope
<What this spec deliberately leaves out.>
```

## Ticket body

Same shape locally and on GitHub. Avoid file paths and code snippets, with the same prototype exception.

```markdown
# NN: <title>

**What to build:** <the end-to-end behavior this ticket makes work, from the user's perspective, not a layer-by-layer list>

**Blocked by:** <ticket numbers and titles, or "None (can start immediately)">

**Parent:** <spec path or issue, if any>

- [ ] <acceptance criterion>
- [ ] <acceptance criterion>
```

## Wide refactors

One mechanical change whose blast radius fans across the codebase (rename a column, retype a shared symbol) can't land green as a vertical slice. Sequence it as expand–contract:

1. **Expand**: add the new form beside the old so nothing breaks.
2. **Migrate** callers in batches sized by blast radius (per package or directory), each its own ticket blocked by the expand.
3. **Contract**: delete the old form in a ticket blocked by every migrate batch.

## Publishing

Detect GitHub: `git remote -v` shows a github.com remote and `gh auth status` succeeds.

```bash
gh label list --search ready-for-agent   # add --label ready-for-agent below only if it exists
gh issue create --title "01: <title>" --body-file <ticket body file>
```

Create in dependency order, blockers first, then edit later bodies so "Blocked by" cites the real issue numbers (`#123`). Leave any parent issue unmodified.

Otherwise write `docs/tickets/<slug>/NN-<slug>.md`, one ticket per file, numbered from `01` in dependency order.
