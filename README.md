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
`honey install` also adds a small managed activation block to global `~/.codex/AGENTS.md` and `~/.claude/CLAUDE.md`, preserving personal instructions. It loads `honey bootstrap --agent codex` (or `claude`) at the first user turn. This read-only fallback provides the workflow and visible indicator when startup context is absent; it never manufactures hook events. `🍯 HONEY · … · hooks unverified` means instructions loaded but native event delivery has not been observed. Uninstall removes the managed block while preserving later personal edits.
The **`🍯 HONEY`** prefix indicates injected rules. To check whether the current session actually receives hooks, use `honey doctor --agent codex --session <session-id> --json` (or `--agent claude`). Installation, enablement, recent delivery and payload coverage are reported separately; a prefix or smoke test is not proof of enforcement. For Codex, `hook_trust` reads the native hook registry: `review_required` means the installed plugin needs review in `/hooks`, and `unknown` means the registry could not be checked. Saved approvals alone are not proof of current trust.

## Modes

Choose one response style. Send it as the **whole message**. Add `default` to save it for new sessions (`honey direct default`).

| Mode | Does | Use when |
|---|---|---|
| `honey direct` *(default)* | Straight to the point, concise responses | You want the answer and essential details |
| `honey explain` | Comprehensive explanations with useful context and examples | You want to understand the reasoning |
| `honey balance` | Moderate detail, neither comprehensive nor too brief | You want the answer with key reasoning |
| `honey off` · `honey on` | Pause or resume for this session (safety guard stays on) | A task where honey's rules get in the way |

The indicator shows the active choice: `🍯 HONEY · direct`. Use `honey status` to check it. These modes change response detail; task sizing, verification, and safety controls apply in every mode. Explicit requests for detail take priority. Saved legacy `terse` settings read as `direct`, and `normal` as `balance`; the old scope/process choices are retired. Saving a new default replaces the old `modes` config without changing other settings.

Also: `remember: when X, Y` teaches a rule now. Scopes: `(project)` `(claude)` `(codex)` `(skill:<name>)`, e.g. `remember (project): …`. `rsi off` · `rsi on` pauses learning for this session.

## Task scope and evidence

Hooks retain a bounded task record: inspection or execution, workspace, targets and required checks. “Continue” and status questions retain the task. Explicit inspection stays read-only for recognized edit operations until the user asks for changes. This is an evidence aid, not a permission grant or a complete sandbox; natural-language classification and command recognition are conservative heuristics.

```bash
honey task status --json
honey task set --mode execute --operation code --cwd /actual/project --check tests --check lint
honey task verify --check tests --tool-call <actual-test-call-id>
honey task verify --check lint --tool-call <actual-lint-call-id>
```

Replace paths and call IDs with the actual values. Codex uses `CODEX_THREAD_ID`; otherwise add `--agent claude --session <session-id>` to each command. Bind the project before running its checks. `task set` starts a new bounded contract; it cannot promote an existing inspection task to execution without a user request.

The default code check recognizes direct test/lint commands. Explicit checks link a fresh successful result; the agent must still check that the command proves the named requirement. Later edits, potentially mutating shell commands, failed reruns and incomplete results invalidate proof. When start events are delivered, checks started before a mutation or in a previous task cannot verify the new state. Completion claims without evidence trigger one reminder per evidence cycle; honest unresolved reports and inspection answers are allowed.

For `--operation uninstall`, required checks are `application`, `helpers`, `startup` and `preserved-data`. Declare concrete targets with `--target`; `task verify --check application --absent /Applications/Example.app` measures and rechecks absence. `--present` checks existence. Helpers and startup require checks of their actual registrations, and preserved data requires an explicit check of what should remain. `--operation startup` requires its resulting registration to be checked.

Known shell/read/edit payloads, including `exec_command` with `cmd`, are normalized. JavaScript wrappers remain opaque unless the host delivers supported inner events. Missing hooks, unobserved external edits and concurrent last-writer-wins session updates limit the evidence; `doctor` reports delivery and coverage without claiming runtime enforcement.

## Skills

The agent picks these itself:
`grill` · `plan` · `execute` · `debug` · `tdd` · `verify` · `review` · `ship` · `deploy` · `test-design` · `tooling` · `database` · `perf` · `observability` · `api-design` · `upgrade` · `incident` · `frontend` · `qa` · `security` · `docs`

You call these: `honey` · `rsi` · `unslop` · `reverse-engineer` · `handoff` · `prototype` · `architecture` · `domain` · `teach` · `write-skill` · `principles` · `opensrc`

Flow: **grill → plan → execute → verify → review → ship**. Bugs start at **debug**.
Claude: `/honey:<skill>`. Codex: `$<skill>`.

## RSI: how it learns

1. **Observe:** hooks log bounded, redacted user requests, corrections, "still broken" and which skills fired. Feedback distinguishes behavior, requirements, preferences and environment failures. Task identity and explicit skill references guide attribution; ambiguous feedback remains uncertain instead of blaming every recent skill.
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
| `/rsi publish on / off / status / run` | Publish pending suggestions as GitHub issues and validated skill changes as PRs |
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
  "mode": "direct",
  "budgets":  {"enabled": true, "reflection_usd": 0.15, "weekly_usd": 1.5, "monthly_usd": 5},
  "autonomy": {"min_sessions": 2, "holdout_rate": 0}
}
```

- `holdout_rate: 0.1` leaves the brief out of 10% of sessions, so `/rsi coach` can measure whether rules help.
- `budgets.enabled: false` removes Honey's rolling weekly/monthly dollar caps and the dollar limits passed to drafting and evaluation calls. Usage is still recorded; unknown usage stays unknown. The daily improvement cadence, reflection rate limits, validation, and provider account limits still apply. `honey rsi status --json` reports `budget_caps_enabled`.
- Many other skills installed? `honey install --skill-budget 0.02` gives skill descriptions more room (Claude only).
- **Privacy:** no telemetry. Only redacted snippets of ≤300 characters are stored. Network use is limited to your model provider and the radar's public `git fetch`.
- **Platforms:** macOS and Linux. Windows isn't supported yet.

Enable autonomous application with `honey rsi autonomy on`. It persists in `~/.honey/config.json`; other installations keep review mode until enabled. Session-end catchup and the weekly job apply up to 20 pending proposals per pass. `honey rsi autonomy off` returns to manual review. `rsi off` still pauses observation and jobs for the current session.

With autonomy enabled, session-end and startup catchup jobs attempt one evidence-backed skill improvement every 24 hours. There is no background daemon: a session triggers due work. Existing validated proposals still apply each pass. Failures rotate behind other eligible work; a blocked patch does not freeze unrelated skills. Pending sync recovery pauses new drafting until the installed copy is consistent.

Skill diagnoses are routed to the existing patcher using verified user quotes. Repeated requests can produce a new skill only with actual requests from at least two sessions and positive/negative trigger evaluations. Keyword-only suggestions and unsupported runtime diagnoses remain pending. Genuine user evidence is evaluated separately from external tool output; older quarantined records are recovered only against their original user events.

With dollar caps enabled, the patcher reserves the draft and both evaluations against the existing weekly/monthly budgets before starting. Per-call limits are $0.15 for drafting and $0.35 for each evaluation. Unknown usage after a timeout retains the reserved cost; reported usage replaces it. A budget deferral does not consume the daily generation attempt, so due work can retry when budget becomes available. With dollar caps disabled, drafting and evaluation omit provider dollar limits and failed calls retain unknown usage rather than a false capped estimate. Evaluator errors and incomplete results never count as successful tests. Each arm includes generated cases, existing name-matched skill cases and independently maintained behavior cases for read-only preservation, scoped edits and failed verification. Fixture hashes and exact candidate content are checked before a proposal can apply. Missing or changed fixtures require re-evaluation, including for older proposals. This evaluator supports Claude plugin eval; it does not establish Codex behavior or coverage of every other skill.

`honey task status` exposes task/session tool counts, repeated reads/checks, failures, unknown results and reported durations. `/rsi coach` aggregates them with denominators. Repetition can be necessary, missing durations are not estimated, and these observations are not measured speedups. Uncertain feedback is visible but excluded from negative skill scores and patch evidence.

When a host does not provide the inner events for an opaque tool wrapper, use `honey task run --check verification -- python3 tests/run.py` after binding the execution task to its Git project root with `honey task set --mode execute --operation code --cwd /path/to/project`. This runs the real check without a shell and records its exit status and source snapshot. Printed success cannot manufacture proof; changed source, HEAD or index makes the result stale. The fallback covers tracked and non-ignored files (up to 20,000 files/64 MiB), rejects source symlinks, and does not claim to snapshot ignored dependencies or the external environment. Normal host-event verification remains available.

Use `honey rsi status` for the latest automatic result and `honey rsi review --json` for recent changes and blocked reasons. Unsupported diagnoses remain pending; RSI never executes a proposal's free-form fix text. Diagnosis and new-skill parents complete only after their evaluated child patch is applied, as do upstream ports. Evaluation overlays the current runtime into its worktree and application checks that snapshot. Edited patch targets, runtime drift and diverged branches block application; unrelated documentation edits are preserved, and configured cost limits still apply. Run `honey sync` from the source checkout once to refresh Codex and record the editable source location; the plugin cache is never an editable source.

Instruction edits have conflict-checked `honey rsi revert <id>` snapshots; toolkit repairs retain installer undo records. Guard IDs remain inspectable with `honey rsi guards`. A failed skill sync records `sync_pending` for retry. Legacy instruction snapshots used random short hashes, so automatic revert refuses those; the original text remains in the proposal's `before` field for manual recovery. Automatic decisions do not count as user feedback.

### Publishing improvements

Run `honey rsi publish on` from your Honey source checkout to authorize publishing pending suggestions as issues and applied skill improvements as PRs to its GitHub origin. This pins the repository and its default branch in your local configuration and requires authenticated `gh` access with permission to create issues, push branches and create PRs. `honey rsi publish off` stops publication; `honey rsi publish status --json` shows the configuration. Older PR-only opt-ins retain their previous behavior until `publish on` is run again.

Pending toolkit diagnoses, new-skill suggestions and upstream proposals become **GitHub issues automatically during ordinary RSI processing**, even if automatic local application is off. No implementation or passing evaluation is required to record a suggestion. Each issue identifies the proposal and explicitly says it is unimplemented and needs confirmation. Only the bounded, redacted title, diagnosis and proposed next step are shared; session quotes, session identifiers and local evidence are excluded. Closed issues are respected and not recreated. Issue publication does not mark a local proposal applied. `honey rsi review` shows the issue link. `honey rsi publish run --json` publishes the current eligible backlog without invoking paid reflection or evaluation.

The full flow is **suggestion → GitHub issue → evaluation → apply and sync locally → skill-only commit → PR**. Automatic passes publish eligible applied skill patches when autonomy and publication are enabled; explicitly applying a skill patch also attempts publication. Existing eligible applied patches are included. `honey rsi status` reports published URLs and exact heads, or blocked reasons. The proposal's `github_issue` and `publication` records retain the issue URL and PR SHA/URL respectively. Failed GitHub requests retry on a later pass and look for an existing issue or PR first. Publication failures do not undo successful local application. Published means the issue or PR exists, not that a suggestion is proven or a PR has passed CI or merged.

Personal preferences, instruction files, machine repairs, guards, session logs, and generated evaluation prompts stay local. Public commits start from the remote base and contain only the evaluated `skills/<name>/SKILL.md`; local evaluation commits and their history are not pushed. PR text uses fixed metadata, never user quotes or the model's rationale. The skill text itself is shared. Runtime changes absent from the remote baseline, dirty runtime files, legacy patches without snapshots, unexpected files, and changed remote branches block publication. No force pushes, automatic merges or releases. A published PR's closure is respected.

## Update · Uninstall

honey checks for updates at session start, at most once an hour. For local Git marketplaces it fetches the newest `vX.Y.Z` release tag reachable from `main`, fast-forwards the checkout, and refreshes the installed plugin copies. It leaves local changes, feature branches and diverged checkouts untouched, reporting them as skipped even when they already contain the latest release tag. If a plugin refresh fails, it retries on a later session; the update notice appears after the refresh succeeds. The new version loads in a subsequent session. Remote plugin marketplaces use the agent's own marketplace update commands and follow the marketplace's configured ref. Turn updates off with `{"autoupdate": false}` in `~/.honey/config.json`. Codex checks the installed plugin contents as well as hook commands. Any plugin update, including an evaluated skill patch, can require fresh review in `/hooks`; Honey does not approve changed plugin code automatically.

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

Every push or merge to `main` runs the complete CI test matrix, then automatically versions and publishes the tested current revision. Conventional commits select the bump: `feat` produces a minor release, a `!` header or `BREAKING CHANGE:` produces a major release, and other changes produce a patch release. Both plugin manifests, the Python version, changelog, release commit and tag are kept together. If Unreleased is empty, commit subjects provide the release notes.

Repeated release jobs for the same revision are serialized; different revisions cannot cancel each other's pending jobs. If another merge arrives before an older run can release, that older run skips; the newer successful CI run includes those changes in its release. An atomic push prevents concurrent changes from leaving an orphan tag. Rerunning a failed job resumes an already-tagged release instead of bumping again. The repository token publishes the release in the same job, avoiding reliance on another workflow being triggered by a bot push. Failed tests never publish.

The release job needs `contents: write` on `main`; branch rules must permit its version commit. Pull-request tests have read-only repository permissions. Manual versioned tags remain supported, and their publication is also idempotent. Automatic releases become active when this workflow is merged to `main`.

```bash
python3 tests/run.py                    # stdlib self-checks
claude plugin validate .
claude plugin eval . --tag smoke --runs 1 --ablation none --max-cost-usd 2 --no-publish --allow-tools Bash Write Edit
python3 scripts/release.py X.Y.Z --push # optional manual release
```

The runner gives every test script temporary state and a fake model provider. Direct imports through the test helper also use temporary state when `HONEY_HOME` is unset. Maintained fixture tests run offline; JavaScript regex compatibility is additionally checked when Node is installed. These tests do not run paid model evaluations.

[SemVer](https://semver.org/) + [CHANGELOG](CHANGELOG.md). Skill style: [docs/skill-style.md](docs/skill-style.md). Design: [docs/design/plan.md](docs/design/plan.md).

MIT © King Umar. Credits and licenses: [THIRD_PARTY.md](THIRD_PARTY.md).
