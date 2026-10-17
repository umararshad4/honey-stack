# Skill evals (`claude plugin eval` format)

Cases live in the repo's top-level `evals/` folder, one folder per case. The runner finds every `evals/<case>/prompt.md` with its `graders/*.md`.

```
evals/
  <situation>-uses-<skill>/      # should fire
    prompt.md
    graders/fired.md
    graders/<behavior>.md        # optional: what the skill must make the agent do
  <near-miss>-not-<skill>/       # should not fire
    prompt.md
    graders/not-fired.md
```

## prompt.md

YAML frontmatter, then the user's message exactly as a user would type it.

```markdown
---
max_turns: 4
tags: [skill-debug]
allowed_tools: [Read, Glob, Grep, Skill]
---

Our checkout test fails intermittently with `KeyError: 'currency'` about one run in five. Before changing anything, how should we track this down?
```

- `max_turns`: 3–4 for a trigger check; up to 8 when a behavior grader needs the agent to act.
- `tags`: free labels, e.g. `[skill-<name>]` or `[regression]`.
- `allowed_tools`: always include `Skill`, or the skill can't fire. Add `Bash`, `Write`, `Edit` only when a grader needs them.
- Write the prompt in the user's words and don't name the skill. The case tests whether the description's triggers catch real phrasing. Make it substantive: the agent skips skills on one-step asks it can answer directly, so a trivial prompt fails for the wrong reason.

## Graders

One file per grader, frontmatter only unless it's an `llm` grader.

**Should fire** (`graders/fired.md`). Replace `NAME` with the skill name; the optional prefix matches `honey:NAME` as well as `NAME`.

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?NAME"'
---
```

**Should not fire** (`graders/not-fired.md`): the same match, with zero calls allowed on both arms.

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?NAME"'
min: 0
max: 0
arm: both
---
```

**Behavior graders**, when the skill must change what the agent does:

| Type | Frontmatter | Body |
|---|---|---|
| `llm` | `type: llm` | One `PASS if …` line and one `FAIL if …` line, both concrete and observable |
| `regex` | `type: regex`, `pattern: "Checks run:"` | none; matches the last message |
| `tool_used` | `type: tool_used`, `tool: Bash`, `input_match: 'pytest'` | none; add `min`/`max` for counts |
| `file_exists` | `type: file_exists`, `path: "greet.py"` | none |

## Picking the cases

- **Should fire**: the most common real phrasing of the skill's main branch. For a patch, use the exact situation from the failure evidence.
- **Should not fire**: a near-miss. It shares keywords or a domain with the skill but needs something else; usually it belongs to a neighboring honey skill (a UI idea that isn't a bug for `debug`, a quick question that isn't a plan for `plan`). An obviously unrelated prompt tests nothing.
- **Regression** (patches): rebuild the failing session as a prompt, and grade the behavior that was missing. It must fail on the old skill.
- User-invoked skills can't fire on their own, so they get no trigger cases. Test their behavior by giving a fresh subagent the SKILL.md path and a task that tempts the failure, with a no-skill control run alongside.

## Running

From the repo root:

```bash
claude plugin eval . --case "<glob>" --runs 1 --ablation none --max-cost-usd 1 --no-publish
```

- `--case` takes a glob over case folder names, e.g. `"*-debug"` or `"bug-uses-debug"`.
- `--ablation none` skips the no-plugin arm. Under the default `with-without`, `tool_used: Skill` graders become with-only indicators and don't score.
- `--runs 1` is the cheap first pass. Before accepting a patch or calling a flaky result, re-run with `--runs 3`; one sample can mislead.
- Results land in `evals/results/<timestamp>/aggregate-result.json`: read `aggregates.casesPassed` and each case's `aggregates.passRate` and grader `explanation`. Add `--json <path>` for the full trace paths.
- For old-vs-new on a patch, run the same command on a checkout of each version and compare per case.
- On Codex, or anywhere without the `claude` CLI, record the eval as skipped with that reason; don't report it as passed.
