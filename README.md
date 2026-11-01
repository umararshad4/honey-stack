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
- **Local and reversible:** Honey state stays in `~/.honey/`; `honey uninstall` restores everything. External history integrations are optional.

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
| **On demand** | `honey` `rsi` `unslop` `reverse-engineer` `handoff` `delta` `prototype` `architecture` `domain` `teach` `write-skill` `principles` `opensrc` `project-verify` `triage` `research` `statechart` |

Call a skill with `/honey:<skill>` in Claude Code or `$<skill>` in Codex. See [docs/skills.md](docs/skills.md) for focused workflows and browser QA.

## Delta: pick up where you left off

Honey integrates with [Delta](https://delta.dev/cli) to find decisions in earlier conversations and carry their context into a new session. Use it to recover a decision, check what was already tried, or attach conversation history to a handoff. Honey keeps working normally without Delta.

### Install Delta

Install the optional Delta app and CLI on each computer where you want to use history. On macOS or Linux:

```bash
curl -fsSL https://delta.dev/install.sh -o delta-install.sh
sh delta-install.sh
delta auth login
delta --version
honey delta status
```

Use Delta 0.22.0 or newer. If it is already installed, check for updates with `delta update --check` and install an available update with `delta update`. The [official installation guide](https://delta.dev/docs/cli/get-started) covers other platforms.

### Use your history

Ask for `/honey:delta` in Claude Code or `$delta` in Codex, or run these commands in your terminal:

| You want to… | Run |
|---|---|
| Check installation, sign-in and capture settings | `honey delta status` |
| Find an earlier decision | `honey delta recall cache expiry` |
| Find conversations that touched a file | `honey delta search authentication --edited-path 'src/**'` |
| Read a specific conversation | `honey delta read THREAD_ID --messages 1-1` |
| Check whether its summary is current | `honey delta summary THREAD_ID` |

Replace `THREAD_ID` with an ID returned by search, or use a Delta join link. Reads start with one message so short conversations work. Choose a larger range when needed, up to 20 messages per call. History results are JSON and default to at most 12,000 characters; shortened results say `truncated: true`.

For handoffs, Honey can attach a verified thread reference, the current Git state and test-report fingerprints to your local summary. Restoring it checks what changed and keeps the summary usable if Delta is unavailable. See the [Delta guide](docs/delta.md) for `attach`, `restore`, readiness fields and troubleshooting.

### Record new conversations, optionally

History lookup works in both Claude Code and Codex. To record new **Claude Code** sessions, install Delta's separate official plugin:

```bash
claude plugin marketplace add zed-industries/delta-claude
claude plugin install delta@zed-industries
```

Start a new Claude session or run `/reload-plugins`. Then use `/delta setup` in your repository to choose manual, private or organization capture. Honey can preview the manual policy with `honey delta setup --mode manual`; only an explicit `--apply` writes it. Native Codex session recording is not included.

**Privacy:** installing Honey or reading history does not enable capture. Private sync uploads conversation and checkout data to Delta's servers. Organization capture shares it with that organization. Honey keeps history separate from RSI feedback and fresh verification evidence. See [Delta's capture guide](https://delta.dev/docs/cli/claude-code) before enabling uploads.

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

**Privacy:** Honey has no telemetry and stores redacted learning snippets of up to 300 characters locally. Explicit Delta lookups read your separate Delta account. Capture is opt-in; private Delta synchronization uploads conversations and checkout data to its servers. Honey's history reads and handoff metadata do not upload sessions or import history into RSI.

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
| [Delta](docs/delta.md) | Install, find past decisions, configure capture and restore handoffs |
| [RSI](docs/rsi.md) | Tiers, autonomy, budgets, publishing improvements |
| [Task evidence](docs/task-evidence.md) | `honey task` scope and proof of checks |
| [Development](docs/development.md) | Tests, CI and automatic releases |
| [Skill style](docs/skill-style.md) | Writing conventions for skills |

MIT © King Umar · [Changelog](CHANGELOG.md) · [Credits and licenses](THIRD_PARTY.md)
