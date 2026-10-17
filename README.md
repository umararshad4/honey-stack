# 🍯 honey-stack

**One always-on toolkit for Claude Code and Codex that learns from every session.**

[![ci](https://github.com/umararshad4/honey-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/umararshad4/honey-stack/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/v/release/umararshad4/honey-stack)](https://github.com/umararshad4/honey-stack/releases)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

honey-stack distills the best of [Superpowers](https://github.com/obra/superpowers), [Ponytail](https://github.com/DietrichGebert/ponytail), [Matt Pocock's skills](https://github.com/mattpocock/skills), [pstack](https://github.com/cursor/plugins/tree/main/pstack) and [gstack](https://github.com/garrytan/gstack) into **one layer** instead of five competing ones. On top sits **RSI** (recursive self-improvement): it notices where the agent gets corrected, learns your preferences, and proposes fixes to its own skills, which you approve.

- **Small.** About 2 KB of always-on rules instead of ~25 KB of stacked prompts.
- **Opinionated.** It sizes each task, takes the smallest complete change, proves it before saying done, and decides instead of asking.
- **Self-improving, with you in charge.** Small learnings apply automatically; anything bigger waits for your yes.
- **Local and reversible.** Your data stays in `~/.honey/`, and `honey uninstall` restores everything.

---

## Install

**Requires:** Claude Code and/or Codex CLI, `python3` (3.9+) and `git`.

### Option A: full install (recommended)

One line (clones + shows a dry run; you approve the apply):

```bash
curl -fsSL https://raw.githubusercontent.com/umararshad4/honey-stack/main/install.sh | bash
```

Or by hand:

```bash
git clone https://github.com/umararshad4/honey-stack.git
cd honey-stack
bin/honey install --dry-run     # shows every change it would make
bin/honey install               # applies them (asks first)
```

This installs the plugin in both agents, puts `honey` on your PATH, and switches off competing always-on plugins (Superpowers, Ponytail, pstack). Each change is recorded so `honey uninstall` can reverse it.

### Option B: plugin only

```bash
# Claude Code
claude plugin marketplace add umararshad4/honey-stack
claude plugin install honey@honey-stack

# Codex
codex plugin marketplace add umararshad4/honey-stack          # add --ref v0.2.0 to pin a release
codex plugin add honey@honey-stack
```

### Then, once

| Agent | Do this |
|---|---|
| Claude Code | Start a new session, or run `/reload-plugins`. |
| Codex | Run `codex`, then `/hooks`, and **trust the honey entries** (Codex asks once per hook). |
| Both | `honey doctor` checks that everything is wired. After Option B, run it as `python3 <plugin dir>/bin/honey doctor`. |

You'll know it's active when every reply starts with **`🍯 HONEY`** (plus any non-default mode, e.g. `🍯 HONEY · ultra · strict`). Claude's statusline also shows `[HONEY]`.

---

## Use it

Type these **as the whole message**. Hooks catch them before the model runs.

| Type | Effect |
|---|---|
| `honey ultra` · `honey lite` · `honey full` | Scope: push back on extras · build what's asked · smallest complete change (default) |
| `honey strict` · `honey light` | Process: test first, plan before multi-file work, reviewer before done · lighter |
| `honey terse` · `honey normal` | Voice |
| `honey default ultra strict` | Save as your default |
| `honey off` · `honey on` | Pause or resume for this session (the safety guard stays on) |
| `remember: when X, Y` | Teach a rule now. Scopes: `remember (project): …`, `(claude)`, `(codex)`, `(skill:debug)` |
| `rsi off` · `rsi on` | Pause or resume learning for this session |

Slash commands: Claude uses `/honey`, `/rsi …`, `/honey:<skill>`. Codex uses `$honey`, `$rsi …`, `$<skill>`.

---

## How it works

```
 you ──▶ Claude Code / Codex ──hooks──▶ bin/honey (one dispatcher)
                                          ├─ bootstrap + your learned brief   (session start)
                                          ├─ mode switches, remember: notes   (each prompt)
                                          ├─ destructive-command guard        (before shell)
                                          ├─ secret scan, skill tracking      (after tools)
                                          └─ receipt gate, session log        (stop / end)
                                                   │
                                session end ──▶ RSI reflects (cheap, no tools, budget-capped)
                                                   │
                         ~/.honey: learnings · scorecards · proposals · coach reports (local git)
```

### Skills: one per job

| The agent picks these itself | You invoke these |
|---|---|
| `grill` (pin down intent) · `plan` · `execute` (work through a queue) · `debug` · `tdd` · `verify` · `review` · `ship` (commit/PR) · `deploy` (cloud/Docker/K8s/IaC/CI) · `test-design` (edge-case matrix) · `tooling` (monorepo/hooks/lint/CI) · `database` (schema/migrations/queries) · `perf` (profiling/caching/load) · `observability` (logs/metrics/traces/SLOs) · `api-design` (REST/GraphQL/gRPC) · `upgrade` (deps/CVEs/EOL) · `incident` (outage response) · `frontend` · `qa` (real browser) · `security` · `docs` | `honey` (router + modes) · `rsi` · `unslop` (cut AI tells from any text) · `reverse` (study a shipped app via REA) · `handoff` · `prototype` · `architecture` · `domain` · `teach` · `write-skill` · `principles` · `opensrc` |

Main flow: **grill → plan → execute → verify → review → ship**. Bugs go through **debug** first.

### RSI: how it learns

1. **Observe.** Hooks log corrections ("no, I said…"), "still broken", acceptance, and which skill fired and how it went. Everything is redacted before it's stored.
2. **Reflect.** After a session with real signal, a small model (Haiku, about $0.002 per session) proposes WHEN → THEN rules. Every rule must cite evidence and pass a "would a future agent get this wrong?" test.
3. **Curate.** Plain code merges duplicates, promotes a rule once **2 sessions** back it, and retires rules that stop applying (stale after 30 days, archived after 90).
4. **Gate.** Changes are tiered by how much they can affect:

| Tier | Changes | Decided by |
|---|---|---|
| 0 | Learned rules in each session's brief (≤1.5 KB) | Automatic |
| 1 | Lines in your `CLAUDE.md` / `AGENTS.md` (managed block, revertible) | You, in `/rsi review` |
| 2 | Skill files. A patch is kept only if a regression eval built from the real failure fails before and passes after | You |
| 3 | An enforced guard for a rule that keeps being broken, replay-verified with ≤1% false positives | You |

5. **Coach.** `/rsi coach` shows where you're improving, where mistakes repeat, which skills help, and up to 3 suggestions, each citing its evidence.
6. **Radar.** Every week it checks the upstream toolkits and surfaces only the changes that match friction you actually had.

Useful commands: `/rsi review` · `/rsi coach` · `/rsi status` · `/rsi why <id>` · `/rsi forget <id>` · `/rsi bootstrap` (seed rules from your existing agent memories).

---

## Configure

`~/.honey/config.json`. Every key is optional.

```json
{
  "modes":    {"scope": "full", "process": "light", "voice": "terse"},
  "budgets":  {"reflection_usd": 0.15, "weekly_usd": 1.5, "monthly_usd": 5},
  "autonomy": {"min_sessions": 2, "holdout_rate": 0}
}
```

`holdout_rate: 0.1` leaves the brief out of 10% of sessions, so the coach can measure whether the learned rules actually help.

**Skill-listing room.** honey keeps its model-invoked skill descriptions under a hard budget (CI fails if they exceed it). Those descriptions share ~1% of the context window with every other skill you have installed. If you run many other skills and want more room, `honey install --skill-budget 0.02` raises Claude's `skillListingBudgetFraction` (reversible via `honey uninstall`).

**Freshness.** Each skill carries a `reviewed:` date; `honey doctor` warns when a skill's version-specific facts are over a year old so you can refresh them.

**Platform.** Built and tested on macOS and Linux (CI runs both, Python 3.9 and 3.12). Windows is not yet supported — the hooks and installer assume a POSIX shell and paths.

**Privacy.** No telemetry. Prompts are stored only as redacted snippets (≤300 characters) around signals. Sessions that pulled in web or MCP content can't auto-promote rules. Network use is limited to your model provider and anonymous `git fetch`es of public repos (the radar).

---

## Update

```bash
honey update          # full install: pulls the latest release and refreshes Codex; then /reload-plugins in Claude
```

Plugin-only install:

```bash
claude plugin marketplace update honey-stack && claude plugin update honey@honey-stack
codex plugin marketplace upgrade honey-stack && codex plugin add honey@honey-stack
```

## Uninstall

```bash
honey uninstall --dry-run && honey uninstall    # restores every changed file and link; keeps ~/.honey
honey uninstall --purge                         # …and deletes ~/.honey
```

Opt-in extras, for migrating from MCT or Matt Pocock skills: `honey install --slim-instructions` replaces CLAUDE.md and AGENTS.md with `migrate/` templates (edit those first), and `--retire-legacy` moves absorbed skills to backups. Both are reversible.

---

## Versions & releases

honey-stack follows [SemVer](https://semver.org/) and [Keep a Changelog](CHANGELOG.md).

- **MAJOR**: breaking changes to hook commands, data layout or the CLI
- **MINOR**: new skills or RSI features
- **PATCH**: fixes

```bash
honey --version
git checkout v0.2.0                                  # pin a release (Option A)
codex plugin marketplace add umararshad4/honey-stack --ref v0.2.0
python3 scripts/release.py 0.3.0 --push              # maintainers: bump, test, tag; CI publishes the release
```

## Develop

```bash
python3 tests/run.py && /usr/bin/python3 tests/run.py          # stdlib self-checks, Python 3.9+
claude plugin validate .
claude plugin eval . --tag smoke --runs 1 --ablation none --max-cost-usd 2 --no-publish --allow-tools Bash Write Edit
claude plugin eval . --tag quality --ablation with-without --no-publish --allow-tools Bash   # does honey improve output vs no plugin?
```

Style guide for skills: [docs/skill-style.md](docs/skill-style.md). Design: [docs/design/plan.md](docs/design/plan.md).

## Credits

MIT © King Umar. Built on ideas and trimmed text from the projects listed in [THIRD_PARTY.md](THIRD_PARTY.md), whose licenses are in `licenses/`.
