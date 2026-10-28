# 🍯 honey-stack

**One always-on toolkit for Claude Code and Codex that learns from every session.**

[![ci](https://github.com/umararshad4/honey-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/umararshad4/honey-stack/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/v/release/umararshad4/honey-stack)](https://github.com/umararshad4/honey-stack/releases)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

The best of [Superpowers](https://github.com/obra/superpowers), [Ponytail](https://github.com/DietrichGebert/ponytail), [Matt Pocock's skills](https://github.com/mattpocock/skills), [pstack](https://github.com/cursor/plugins/tree/main/pstack) and [gstack](https://github.com/garrytan/gstack) in **one layer**, plus **RSI**: it learns from your corrections and can apply validated improvements autonomously.

- **Small:** ~2 KB of always-on rules, not ~25 KB of stacked prompts.
- **Opinionated:** sizes each task, makes the smallest complete change, proves it before "done".
- **You choose:** learned rules apply on their own; enable autonomous RSI to apply validated improvements across all tiers.
- **Local and reversible:** data lives in `~/.honey/`; `honey uninstall` restores everything.

## Install

Needs Claude Code and/or Codex, `python3` 3.9+ and `git`.

```bash
curl -fsSL https://raw.githubusercontent.com/umararshad4/honey-stack/main/install.sh | bash   # clones + dry run; then run the install command it prints
# or by hand:
git clone https://github.com/umararshad4/honey-stack.git && cd honey-stack
bin/honey install --dry-run && bin/honey install
```

Installs into both agents, puts `honey` on PATH, and turns off competing always-on plugins. Every change is reversible.

<details><summary>Plugin only</summary>

```bash
claude plugin marketplace add umararshad4/honey-stack && claude plugin install honey@honey-stack
codex plugin marketplace add umararshad4/honey-stack && codex plugin add honey@honey-stack   # pin: marketplace add … --ref v0.2.0
```

`honey` isn't on PATH here: run it as `python3 <plugin dir>/bin/honey doctor` (same for `uninstall`).
</details>

**Then:** Claude → `/reload-plugins`. Codex → `/hooks`, trust the honey entries. Check with `honey doctor`.
It's on when replies start with **`🍯 HONEY`**.

## Modes

Send as the **whole message**. Add `default` to save it (`honey ultra strict default`).

| Mode | Does | Use when |
|---|---|---|
| `honey lite` | Builds what you asked, offers a smaller option in one line | The spec is fixed and isn't yours to question |
| `honey full` *(default)* | Smallest complete change; skips unrequested extras | Everyday features and fixes |
| `honey ultra` | Pushes back on anything the need doesn't justify; prefers deleting | Vague asks, cleanup, or you suspect overbuilding |
| `honey light` *(default)* | Test-first where it's easy; one runnable check per non-trivial change | Normal work |
| `honey strict` | Failing test first, plan before multi-file work, reviewer before done | Payments, auth, migrations, anything costly to break |
| `honey terse` *(default)* | No preamble, no recap, short sentences | You know the domain |
| `honey normal` | Claude's usual voice | Learning, or you want the reasoning |
| `honey off` · `honey on` | Pause or resume for this session (safety guard stays on) | A task where honey's rules get in the way |

Also: `remember: when X, Y` teaches a rule now. Scopes: `(project)` `(claude)` `(codex)` `(skill:<name>)`, e.g. `remember (project): …`. `rsi off` · `rsi on` pauses learning for this session.

## Skills

The agent picks these itself:
`grill` · `plan` · `execute` · `debug` · `tdd` · `verify` · `review` · `ship` · `deploy` · `test-design` · `tooling` · `database` · `perf` · `observability` · `api-design` · `upgrade` · `incident` · `frontend` · `qa` · `security` · `docs`

You call these: `honey` · `rsi` · `unslop` · `reverse-engineer` · `handoff` · `prototype` · `architecture` · `domain` · `teach` · `write-skill` · `principles` · `opensrc`

Flow: **grill → plan → execute → verify → review → ship**. Bugs start at **debug**.
Claude: `/honey:<skill>`. Codex: `$<skill>`.

## RSI: how it learns

1. **Observe:** hooks log bounded, redacted user requests, corrections, "still broken" and which skills fired. Everything is redacted.
2. **Reflect:** after a session with signal, a small model (Haiku via Claude, ~$0.002; else Codex) proposes evidence-backed WHEN → THEN rules.
3. **Curate:** a rule goes live once 2 sessions back it; it goes stale after 30 days and is archived after 90.
4. **Apply:** review mode queues changes for `/rsi review`. Autonomous mode applies supported changes after validation:

| Tier | Changes | Who decides |
|---|---|---|
| 0 | Learned rules in each session's brief (≤1.5 KB) | Automatic |
| 1 | Instruction edits and known toolkit repairs, with backups | You, or autonomous RSI |
| 2 | Skill patches and new skills that pass regression evaluations | You, or autonomous RSI |
| 3 | Enforced guards (≤1% false positives on replay) | You, or autonomous RSI |

| Command | Use when |
|---|---|
| `/rsi autonomy on / off / status` | Enable, disable, or inspect automatic application |
| `/rsi improve` | Run a due improvement pass and apply eligible proposals |
| `/rsi status` | Check it's running and what's queued |
| `/rsi review` | Claude's statusline shows `rsi:N`; decide on proposals |
| `/rsi coach` | You want an evidence-based report on what's improving or repeating |
| `/rsi bootstrap` | Fresh install; seed rules from your existing agent memories |
| `/rsi why <id>` · `forget <id>` | Inspect a rule, or reject it for good |

Codex: `$rsi …` instead of `/rsi …`.

A weekly job also checks upstream toolkits and surfaces only the changes that match friction you had.

## Configure

`~/.honey/config.json`. All keys optional:

```json
{
  "modes":    {"scope": "full", "process": "light", "voice": "terse"},
  "budgets":  {"reflection_usd": 0.15, "weekly_usd": 1.5, "monthly_usd": 5},
  "autonomy": {"min_sessions": 2, "holdout_rate": 0}
}
```

- `holdout_rate: 0.1` leaves the brief out of 10% of sessions, so `/rsi coach` can measure whether rules help.
- Many other skills installed? `honey install --skill-budget 0.02` gives skill descriptions more room (Claude only).
- **Privacy:** no telemetry. Only redacted snippets of ≤300 characters are stored. Network use is limited to your model provider and the radar's public `git fetch`.
- **Platforms:** macOS and Linux. Windows isn't supported yet.

Enable autonomous application with `honey rsi autonomy on`. It persists in `~/.honey/config.json`; other installations keep review mode until enabled. Session-end catchup and the weekly job apply up to 20 pending proposals per pass. `honey rsi autonomy off` returns to manual review. `rsi off` still pauses observation and jobs for the current session.

With autonomy enabled, session-end and startup catchup jobs attempt one evidence-backed skill improvement every 24 hours. There is no background daemon: a session triggers due work. Existing validated proposals still apply each pass. Failures rotate behind other eligible work; a blocked patch does not freeze unrelated skills. Pending sync recovery pauses new drafting until the installed copy is consistent.

Skill diagnoses are routed to the existing patcher using verified user quotes. Repeated requests can produce a new skill only with actual requests from at least two sessions and positive/negative trigger evaluations. Keyword-only suggestions and unsupported runtime diagnoses remain pending. Genuine user evidence is evaluated separately from external tool output; older quarantined records are recovered only against their original user events.

The patcher reserves the draft and both evaluations against the existing weekly/monthly budgets before starting. Per-call limits are $0.15 for drafting and $0.35 for each evaluation. Unknown usage after a timeout retains the reserved cost; reported usage replaces it. Budget exhaustion defers work, not validation. Evaluator errors and incomplete results never count as successful tests. New-skill evaluation covers its generated positive/negative cases; it does not prove every other skill's behavior.

Use `honey rsi status` for the latest automatic result and `honey rsi review --json` for recent changes and blocked reasons. Unsupported diagnoses remain pending; RSI never executes a proposal's free-form fix text. Diagnosis and new-skill parents complete only after their evaluated child patch is applied, as do upstream ports. Evaluation overlays the current runtime into its worktree and application checks that snapshot. Edited patch targets, runtime drift and diverged branches block application; unrelated documentation edits are preserved, and existing cost limits still apply. Run `honey sync` from the source checkout once to refresh Codex and record the editable source location; the plugin cache is never an editable source.

Instruction edits have conflict-checked `honey rsi revert <id>` snapshots; toolkit repairs retain installer undo records. Guard IDs remain inspectable with `honey rsi guards`. A failed skill sync records `sync_pending` for retry. Legacy instruction snapshots used random short hashes, so automatic revert refuses those; the original text remains in the proposal's `before` field for manual recovery. Automatic decisions do not count as user feedback.

## Update · Uninstall

honey checks for updates at session start, at most once an hour. For local Git marketplaces it fetches the newest `vX.Y.Z` release tag reachable from `main`, fast-forwards the checkout, and refreshes the installed plugin copies. It leaves local changes and diverged checkouts untouched. If a plugin refresh fails, it retries on a later session; the update notice appears after the refresh succeeds. The new version loads in a subsequent session. Remote plugin marketplaces use the agent's own marketplace update commands and follow the marketplace's configured ref. Turn updates off with `{"autoupdate": false}` in `~/.honey/config.json`. A major release can change hook commands, so Codex may ask you to re-trust them (`/hooks`).

```bash
honey update                                   # update now; then /reload-plugins in Claude
honey uninstall --dry-run && honey uninstall   # keeps ~/.honey; add --purge to delete it
```

Plugin-only installs:

```bash
claude plugin marketplace update honey-stack && claude plugin update honey@honey-stack
codex plugin marketplace upgrade honey-stack && codex plugin add honey@honey-stack
```

## Develop

```bash
python3 tests/run.py                    # stdlib self-checks
claude plugin validate .
claude plugin eval . --tag smoke --runs 1 --ablation none --max-cost-usd 2 --no-publish --allow-tools Bash Write Edit
python3 scripts/release.py 0.3.0 --push # bump, test, tag; CI publishes
```

[SemVer](https://semver.org/) + [CHANGELOG](CHANGELOG.md). Skill style: [docs/skill-style.md](docs/skill-style.md). Design: [docs/design/plan.md](docs/design/plan.md).

MIT © King Umar. Credits and licenses: [THIRD_PARTY.md](THIRD_PARTY.md).
