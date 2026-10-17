# honey-stack

One always-on agent toolkit for **Claude Code** and **Codex**. It combines the best ideas from Superpowers, Ponytail, Matt Pocock's skills, pstack, gstack and the author's own MCT toolkit. **RSI** learns from every session and improves the toolkit as you use it.

- **One layer, not four.** A single ~2 KB bootstrap replaces the old pile of always-on prompts (~25 KB). It tells the agent to size the task first and take the smallest complete change (lazy about what it adds, complete about what it touches). It also requires proof before claiming done, decisions over questions, and no commits unless you ask.
- **Skills, one per job.** Model-invoked: `grill`, `plan`, `execute`, `debug`, `tdd`, `verify`, `review`, `ship`. User-invoked: `/honey` (router + modes) and `/rsi`.
- **RSI, the recursive self-improvement engine.** Hooks log what happens in each session (corrections, "still broken", which skills fired and how they went) into `~/.honey/`, redacted and local-only, shared by both agents.
  - `remember: <rule>` becomes a learning immediately.
  - Other learnings auto-promote once at least two sessions back them, and decay when they stop applying.
  - Edits to skills, CLAUDE.md, AGENTS.md or hooks are only *proposed*. Nothing changes until you decide in `/rsi review`.

## Install

```bash
cd "/path/to/honey-stack"
bin/honey install --dry-run      # numbered actions + diffs of every file it would touch
bin/honey install                # asks before applying; records everything for uninstall
```

What the install does:
- Claude: installs the plugin (`honey@honey-stack`) from this checkout. It disables the competing always-on plugins (Superpowers, Ponytail) and the MCT hook scripts, points the statusline at honey, and removes dangling skill symlinks (their targets are recorded first). It slims `~/.claude/CLAUDE.md` to your personal preferences, with the original backed up, and moves `MCT.md` to the backups.
- Codex: installs the same plugin and disables Superpowers, Ponytail and pstack. It slims `~/.codex/AGENTS.md`.
- **Then trust the hooks once:** open `codex`, run `/hooks`, and trust the honey entries.

`bin/honey uninstall` replays the install manifest in reverse. If you edited a file after installing, uninstall reverts only honey's own keys and keeps your edits. Backups live in `~/.honey/backups/<timestamp>/`. `bin/honey install --home /tmp/sandbox` rehearses the whole thing against a fake home.

`bin/honey doctor` checks both agents, the hooks, the skill-listing budget and RSI. `bin/honey sync` re-copies the plugin into Codex's cache after repo changes. Claude reads it straight from this checkout (a `directory` marketplace), so edits apply at the next session or `/reload-plugins`.

## Use

| You type (as the whole message) | Effect |
|---|---|
| `honey ultra` / `honey lite` / `honey full` | Scope: push back harder / build what's asked / the ladder (default) |
| `honey strict` / `honey light` | Process: failing test first, plan before multi-file work, reviewer before done |
| `honey normal` / `honey terse` | Voice |
| `honey default ultra strict` | Save as the default for new sessions |
| `honey off` / `honey on` | Pause or resume honey-stack for this session (the safety guard stays on) |
| `rsi off` / `rsi on` | Pause or resume RSI observation for this session |
| `remember: when X, Y` | Save a learning now. Scopes: `remember (project): …`, `(claude)`, `(codex)`, `(skill:debug)` |
| `/rsi review` | Decide what RSI proposes: Apply, Edit, Skip or Never |
| `/rsi status`, `/rsi why <id>`, `/rsi forget <id>`, `/rsi brief` | Inspect or prune what it learned |

Codex uses `$honey` and `$rsi` instead of `/`.

## What's enforced vs advisory

These are enforced by code, in `bin/honey` → `honey/dispatch.py`:
- the destructive-command guard (asks, or denies under bypass mode and on Codex)
- the secret scan of newly written text
- the receipt gate (only after turns that edited files)
- prompt-origin classification, so harness text never triggers anything
- the RSI event log and learnings

The bootstrap and skills are advisory: they shape behavior. RSI's job is to measure where that shaping fails and to propose moving repeated failures into enforced checks.

## Verified platform facts (Phase 0 spike, Claude Code 2.1.302, Codex 0.163.0)

- **Codex plugin source.** Codex accepts `"source": {"source": "local", "path": "./"}` and `.codex-plugin/plugin.json` `"hooks": "./hooks/codex-hooks.json"`. `codex plugin add` re-copies into `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/` each time.
- **Codex hook environment.** Codex sets `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`, `PLUGIN_ROOT` and `PLUGIN_DATA`, and expands `${CLAUDE_PLUGIN_ROOT}` in hook commands.
- **Codex hook payloads.**
  - `tool_name` is `Bash` and `tool_input` is `{"command": …}`.
  - `tool_response` is a string.
  - SessionEnd fires with `reason: "other"`.
  - `transcript_path` is null under `codex exec --ephemeral`.
  - `additionalContext` reaches the model.
- **Claude.**
  - Hook commands work with a plugin path that contains spaces.
  - `UserPromptExpansion` reports `command_name` (e.g. `spike:hello`) and `command_source: "plugin"`.
  - `-p` sessions report `permission_mode: "auto"`.
- **Hook command strings are frozen.** Codex trusts each hook entry by hash, so any change would force a re-trust. All logic lives in Python behind them.

## Layout

```
hooks/hooks.json, hooks/codex-hooks.json   frozen hook registrations (one command per event)
bin/honey                                  CLI shim
honey/dispatch.py                          the single hook dispatcher
honey/{modes,guard,secrets,receipt}.py     bootstrap/modes, destructive guard, secret scan, receipt gate
honey/rsi/*                                observer, signals, curator (ledger + brief), review queue + toolkit audit
honey/{install,doctor}.py                  reversible installer, health check
skills/                                    one skill per job (style: docs/skill-style.md)
evals/                                     claude plugin eval cases
tests/run.py                               stdlib self-checks; run on python3 and /usr/bin/python3 (3.9)
```

## Develop

```bash
python3 tests/run.py && /usr/bin/python3 tests/run.py
claude plugin validate .
claude plugin eval . --tag smoke --runs 1 --ablation none --max-cost-usd 2 --no-publish --allow-tools Bash Write Edit
```

Licensed MIT. Upstream credits are in `THIRD_PARTY.md`.

## RSI tiers at a glance

| Tier | What changes | Who decides |
|---|---|---|
| 0 | Learnings (WHEN → THEN) in the per-session brief, skill notes, keyword reminders | Automatic. Needs evidence from ≥2 sessions (3 if review precision drops below 30%). Decays after 30/90 days |
| 1 | Lines in `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`: graduating proven learnings into a managed block, pruning contradicted lines | You, in `/rsi review`. `honey rsi revert <id>` undoes it |
| 2 | Skill files: ≤3 exact hunks on a `rsi/<skill>-<date>` branch. Kept only if a regression eval built from the real failure fails before and passes after, and no existing eval drops | You. Apply fast-forwards main and runs `honey sync` |
| 3 | Learned PreToolUse guards for rules that keep being violated. Verified by replaying the violating commands, with ≤1% false positives on recent commands | You |

Weekly (detached, at most once every 7 days): curate, graduate, instruction audit, guard proposals, ≤2 skill patches, the upstream radar and the coach report. Budget caps by default: $0.15 per reflection, $1.50 per week, $5 per month. Change them in `~/.honey/config.json` under `budgets`. Set `autonomy.holdout_rate` (e.g. 0.1) to leave the brief out of some sessions and measure its effect.
