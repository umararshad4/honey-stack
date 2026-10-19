---
name: rsi
description: "honey RSI: review what it learned, coach on your progress, save or forget learnings, pause it. Subcommands: status, autonomy, review, coach, bootstrap, why, forget, note, brief, audit, guards, radar, weekly, costs, revert, off, on."
disable-model-invocation: true
license: MIT
metadata:
  reviewed: "2026-10-18"
  sources: "honey-stack original; review flow after cursor/plugins pstack 0.15.25 skills/reflect (explicit approval) and BayramAnnakov/claude-reflect (Apply/Edit/Skip); learning gate after EveryInc/compound-engineering-plugin ce-compound"
---

# rsi — the recursive self-improvement engine

RSI watches every honey-stack session through hooks. Corrections, "still broken", acceptance, which skills fired and how they went are all logged to `~/.honey/` and redacted. A `remember:` note becomes a learning at once. Other learnings are promoted on their own once two or more sessions back them, and they decay when they stop applying. Review mode queues instruction edits, toolkit repairs, skill patches and guards for user decisions. With `honey rsi autonomy on`, existing session-end and weekly jobs apply supported proposals automatically after validation. Budgets, evidence checks, never-list exclusions and current user instructions still apply. Unsupported repairs stay pending with reasons; do not execute free-form fix text.

Run the CLI: `honey rsi <sub>`. If `honey` isn't on PATH, use `python3 "<plugin root>/bin/honey" rsi <sub>`; the plugin root is two folders above this skill's directory. Show the output compactly and invent nothing beyond what the CLI returned.

## Subcommands (from the user's arguments; none = `status`)

| Ask | Run | Then |
|---|---|---|
| autonomy on / off / status | `honey rsi autonomy on`, `off`, or `status` | Change or inspect the persistent application policy; enabling does not bypass checks |
| status | `honey rsi status` | Relay it in 2–4 lines |
| review | `honey rsi review --json` | See **Review** below |
| why <id> | `honey rsi why <id>` | Show the rule, its evidence quotes and counters |
| forget <id> | `honey rsi forget <id>` | Confirm in one line. The id joins the never-list, so it won't be re-proposed |
| note <text> | `honey rsi note <text> [--scope project\|claude\|codex\|skill:<name>]` | Confirm the saved id |
| brief | `honey rsi brief` | Show the learned-preferences block every session gets |
| audit | `honey rsi audit` | List toolkit misfires found in the current config |
| coach | `honey rsi coach` | Show the report as-is. It is evidence-based and cites the data behind each point |
| bootstrap | `honey rsi bootstrap --dry-run` first, then without `--dry-run` once the user agrees | It mines past sessions and memories into *proposed* learnings for one review |
| guards | `honey rsi guards` | List learned guards (proposed, active, rejected) and how often each fired |
| radar | `honey rsi radar --dry-run`, then `honey rsi radar` | Upstream toolkit changes that match your friction become proposals; the rest are only counted |
| weekly | `honey rsi weekly` | Run the weekly job now: curate, graduate learnings, audit instruction files, propose guards and eval-gated skill patches, radar, coach. It normally runs on its own every 7 days |
| costs | `honey rsi costs` | Spend by month and job |
| revert <id> | `honey rsi revert <id>` | Undo an applied instruction-file edit |
| golden | `honey rsi golden --dry-run` | Replays past review decisions through the reflector prompt. Run it before changing RSI's own prompts |
| off / on | Tell the user to send `rsi off` (or `rsi on`) as the whole message | The hook pauses or resumes observation for this session only |

## Review

1. Run `honey rsi review --json`. It returns pending `proposals`, `proposed_learnings`, `autonomous`, `recent_autonomy` and `recent_changes`. If autonomous, summarize applied changes and blocked/deferred reasons; do not ask for routine approval. Follow explicit user requests to apply, skip, forget, revert or disable autonomy.
2. If both are empty, say "Nothing to review." and stop.
3. In review mode, ask about the items in batches of up to 4. On Claude use AskUserQuestion; on Codex use a numbered list the user answers like `1a 2s 3n`. For each item show:
   - the title or rule
   - one line on why, plus one evidence quote
   - the fix
   - the options: **Apply**, **Edit** (the user's wording replaces it), **Skip** (ask again later), **Never** (never re-propose).
4. Record each answer: `honey rsi decide <id> apply|edit|skip|never [--text "<user's wording>"]`.
5. What Apply does depends on the item's `type`:
   - `instr_line`, `instr_remove` or `instr_edit`: edits CLAUDE.md or AGENTS.md. Additions go inside the managed `honey:rsi` block. `honey rsi revert <id>` undoes the edit if the file has not changed since application. Legacy snapshots without a verifiable hash require manual recovery from `before`.
   - `skill_patch`: show its `diff` and the `eval` before/after scores first. Apply fast-forwards the honey-stack repo to the patch branch and syncs Codex. Skip or Never deletes the branch.
   - `guard`: activates an enforced check on shell commands. Show the verification counts first.
   - `upstream_port`: drafts a new eval-gated patch, which comes back as a `skill_patch` item.
   - `skill_new`: suggest drafting it with the `write-skill` skill.
   - `toolkit_fix`: applies a supported structured audit repair and saves installer undo records. An unstructured diagnosis has no executable operation and remains pending.
6. Done when every item has a recorded decision. Report it in one line, e.g. `rsi review: 3 applied, 1 skipped, 1 never`.

In review mode, your recommendation is never approval. Ask, then record exactly what the user chose. Autonomous mode supplies standing authorization only for supported, validated RSI operations; it does not authorize unrelated work or remote pushes.
