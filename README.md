# 🍯 honey-stack

**An always-on workflow layer for Claude Code and Codex that learns from every session.**

[![ci](https://github.com/umararshad4/honey-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/umararshad4/honey-stack/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/v/release/umararshad4/honey-stack)](https://github.com/umararshad4/honey-stack/releases)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![docs](https://img.shields.io/badge/docs-honey--stack.vercel.app-f3b544)](https://honey-stack.vercel.app)

honey-stack combines the best of [Superpowers](https://github.com/obra/superpowers), [Ponytail](https://github.com/DietrichGebert/ponytail), [Matt Pocock's skills](https://github.com/mattpocock/skills), [pstack](https://github.com/cursor/plugins/tree/main/pstack) and [gstack](https://github.com/garrytan/gstack) in one small layer, then adds **RSI** (recursive self-improvement): it learns from your corrections and can apply validated improvements on its own.

- **Small:** ~2 KB of always-on rules, not ~25 KB of stacked prompts.
- **Disciplined:** sizes each task, makes the smallest complete change and proves it before "done".
- **Self-improving:** turns your corrections into rules and evaluated skill patches.
- **Local and reversible:** data stays in `~/.honey/`; `honey uninstall` restores everything.

## Quick start

Needs Claude Code and/or Codex, `python3` 3.9+ and `git` on macOS or Linux.

**1. Install.** This clones the repo and shows a dry run; then run the install command it prints.

```bash
curl -fsSL https://raw.githubusercontent.com/umararshad4/honey-stack/main/install.sh | bash
```

**2. Activate.** Claude Code: start a new session or run `/reload-plugins`. Codex: open `/hooks` and trust the honey entries.

**3. Check.** Run `honey doctor`. Replies now start with `🍯 HONEY · direct`.

Manual and plugin-only installs, hook troubleshooting and the `hooks unverified` label are covered in the [setup guide](docs/setup.md).

## Everyday use

Work as usual: honey sizes each task and picks the right skill. To steer it, send one of these as the whole message:

| Say | What it does |
|---|---|
| `honey direct` · `honey balance` · `honey explain` | Concise (default), moderate or detailed replies. Append `default` to save. |
| `honey off` · `honey on` | Pause or resume honey for this session. The safety guard stays on. |
| `honey status` | Show the active mode. |
| `remember: when X, Y` | Teach a rule now. Scope it with `(project)`, `(claude)`, `(codex)` or `(skill:<name>)`. |
| `rsi off` · `rsi on` | Pause or resume learning for this session. |
| `update hooks` | Update now and review honey's hooks in Codex. |

Modes change how much is explained, not how carefully work is done. Sizing, verification and safety apply in every mode.

## Skills

**Flow:** grill → plan → execute → verify → review → ship. Bugs start at `debug`.

| Invoked | Skills |
|---|---|
| **Automatic** | `grill` `plan` `execute` `debug` `tdd` `verify` `review` `ship` `deploy` `test-design` `tooling` `database` `perf` `observability` `api-design` `upgrade` `incident` `frontend` `stageshow` `qa` `security` `docs` |
| **On demand** | `honey` `rsi` `unslop` `reverse-engineer` `handoff` `prototype` `architecture` `domain` `teach` `write-skill` `principles` `opensrc` `project-verify` `triage` `research` `statechart` |

Call a skill with `/honey:<skill>` in Claude Code or `$<skill>` in Codex. See [docs/skills.md](docs/skills.md) for focused workflows and browser QA.

## RSI: how it learns

1. **Observe:** hooks log redacted corrections, "still broken" moments and which skills fired.
2. **Reflect:** after a session with signal, a small model (Haiku, ~$0.002) proposes evidence-backed `WHEN → THEN` rules.
3. **Curate:** a rule goes live once two sessions back it, goes stale after 30 days and is archived after 90.
4. **Apply:** learned rules load automatically. Instruction edits, skill patches and guards wait for `/rsi review`, or apply after validation when autonomy is on.

| Command | Use it to |
|---|---|
| `/rsi status` | See what's running and queued. |
| `/rsi review` | Approve or reject pending proposals. |
| `/rsi autonomy on` · `off` | Apply validated changes automatically, or go back to review. |
| `/rsi coach` | Get an evidence-based report on what's improving. |
| `/rsi why <id>` · `forget <id>` | Inspect a rule or reject it for good. |

In Codex, use `$rsi …`. Tiers, budgets, autonomy and GitHub publishing are covered in [docs/rsi.md](docs/rsi.md).

## Configure

All keys in `~/.honey/config.json` are optional:

```json
{
  "mode": "direct",
  "autoupdate": true,
  "budgets":  {"enabled": true, "reflection_usd": 0.15, "weekly_usd": 1.5, "monthly_usd": 5},
  "autonomy": {"min_sessions": 2, "holdout_rate": 0}
}
```

**Privacy:** no telemetry. Only redacted snippets of up to 300 characters are stored, and network use is limited to your model provider and public `git fetch`.

## Update and uninstall

honey checks for a new release at session start, at most once an hour.

```bash
honey update                                   # update now; then /reload-plugins in Claude
honey uninstall --dry-run && honey uninstall   # keeps ~/.honey; add --purge to delete it
```

## Docs

**Documentation site: [honey-stack.vercel.app](https://honey-stack.vercel.app)** — every feature, explained with interactive diagrams. The guides below are the in-repo source.

| Guide | Covers |
|---|---|
| [Setup](docs/setup.md) | Install options, activation, hook checks, modes, updates |
| [Skills](docs/skills.md) | Focused workflows, browser QA with e2e and WebMCP |
| [RSI](docs/rsi.md) | Tiers, autonomy, budgets, publishing improvements |
| [Task evidence](docs/task-evidence.md) | `honey task` scope and proof of checks |
| [Development](docs/development.md) | Tests, CI and automatic releases |
| [Skill style](docs/skill-style.md) | Writing conventions for skills |

MIT © King Umar · [Changelog](CHANGELOG.md) · [Credits and licenses](THIRD_PARTY.md)
