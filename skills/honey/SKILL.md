---
name: honey
description: "Pick the honey-stack skill or flow for a situation, or switch modes: status, lite, full, ultra, strict, light, terse, normal, off, on, default."
disable-model-invocation: true
license: MIT
metadata:
  reviewed: "2026-10-18"
  sources: "mattpocock/skills ask-matt, handoff; DietrichGebert/ponytail 4.7.0 skills/ponytail-help; obra/superpowers 7.0.0 skills/brainstorming (size table); cursor/plugins pstack 0.15.25 poteto-mode"
---

# honey

Router and mode switch for honey-stack.

- **Mode words** (`status`, `lite`, `ultra`, `strict`, `default ultra terse`, …): apply them per the Modes section and reply with one status line.
- **A situation** ("I have a bug report and a half-written plan"): name the skill or flow that fits, say why in one line, then run it.
- **Nothing**: show the main flow and the situation table below, trimmed to what fits the current repo.

## Main flow: idea to shipped

```
grill ──> prototype? ──> plan ──> execute ──> verify ──> review ──> ship
```

1. **`grill`**: pin down intent and the product calls the repo can't answer. Quick or small work skips straight to building.
2. **`prototype`**, only when a question needs a runnable answer (behavior, timing, a layout you have to see). Bridge out and back with `handoff` if it needs its own session.
3. **`plan`**: a session plan for work that fits one or two sessions, or a spec plus tracer-bullet tickets for a multi-session build.
4. **`execute`**: drain the plan, tickets, or `TODO.md` without check-ins. For tickets, one fresh session per ticket.
5. **`verify`** after each item, **`review`** on the finished diff, **`ship`** when the user asks to commit, push, or open a PR.

Bugs merge onto the flow at `debug`, which hands its fix to `verify`.

## Situation to skill

| Situation | Skill |
|---|---|
| Vague idea, missing product decision, "grill me", "brainstorm" | `grill` |
| Question only running code can settle; throwaway sketch | `prototype` |
| Multi-file or multi-session work; plan, spec, PRD, tickets | `plan` |
| "continue", "next", "do the TODOs", "run the plan" | `execute` |
| Broken, throwing, failing, flaky, slow; a fix that didn't work | `debug` |
| Writing a feature or fix test-first at an agreed seam | `tdd` |
| About to say done, fixed, or passing | `verify` |
| Diff or PR ready for a second look; self-review | `review` |
| Commit, push, PR, release, changelog | `ship` |
| Deploy to a cloud/PaaS, write Docker/K8s/IaC, fix a failing deploy or pipeline | `deploy` |
| Design the test matrix and hard edge cases for a feature before writing tests | `test-design` |
| Set up a monorepo, micro-frontend, microservices, pre-commit hooks, lint/format/CI | `tooling` |
| Schema design, migrations, indexing, slow queries, N+1, transactions | `database` |
| Profiling, hot paths, caching, load testing, backend perf with before/after numbers | `perf` |
| Logging, metrics, tracing, error tracking, SLOs, alerting, instrument a service | `observability` |
| Design or version a REST/GraphQL/gRPC API, error contracts, pagination, idempotency | `api-design` |
| Safely upgrade dependencies, patch a CVE, handle a breaking change or EOL | `upgrade` |
| A production outage: triage, mitigate, roll back, communicate, postmortem | `incident` |
| A skill misfired or a lesson should stick; improve honey-stack itself | `rsi` |
| UI, layout, styling, responsive, design-system work | `frontend` |
| Drive the real app to find bugs before users do | `qa` |
| Auth, sessions, secrets, payments, user data, webhooks | `security` |
| Behavior, setup, commands, or APIs changed; docs drift | `docs` |
| Text reads like AI wrote it; tighten a message, post, prompt or doc | `unslop` |
| Thread is long or branching; carry state to a fresh session | `handoff` |
| Codebase hard to change or test; deepen modules, find seams | `architecture` |
| Name the domain terms, keep `CONTEXT.md` and ADRs | `domain` |
| Learn a concept over several sessions | `teach` |
| Write or edit a skill | `write-skill` |
| A design call needs a named principle (root cause, idempotency, boundaries) | `principles` |
| Need a library's real source or docs for a declared dependency | `opensrc` |
| Understand a shipped app, binary, APK or site you don't have source for (authorized) | `reverse-engineer` |

When two rows fit, take the earlier one in the main flow: settle intent before planning, plan before executing.

### Overlaps — which one wins
- **`debug` vs `incident`**: local/non-urgent root-cause → `debug`; production is down or degraded right now → `incident` (mitigate first, then `debug` for the root cause).
- **`perf` vs `database`**: a slow query, N+1, index, or migration → `database`; profiling, caching, load testing, or a non-DB hot path → `perf`. A slow endpoint caused by SQL is `database`; by CPU/serialization/IO is `perf`.
- **`tdd` vs `test-design` vs `qa`**: *what* cases to test → `test-design`; *writing* them test-first → `tdd`; driving the real browser/UI → `qa`.
- **`review` vs `verify`**: judging someone's diff/PR → `review`; proving your own change is actually done before you claim it → `verify`.
- **`ship` vs `deploy`**: commit/push/PR → `ship`; getting it running on a server/cloud → `deploy`.
- **`security` vs `upgrade`**: a design/code security concern or audit → `security`; patching a vulnerable dependency → `upgrade`.
- **`docs` vs `unslop`**: writing/updating project docs → `docs`; tightening any prose of AI tells → `unslop`.

## Modes

Three independent axes. Combine words in one message: `honey ultra strict`.

| Axis | Word | Effect |
|---|---|---|
| scope | `lite` | Build what's asked; name the lazier alternative in one line. |
| | `full` | The ladder enforced on every addition. |
| | `ultra` | Deletion before addition; challenge the requirement before building. |
| process | `light` | Targeted checks per item; one review at the end. |
| | `strict` | Failing test first, a reviewer subagent per task, builder check on designs, the user's go on plans. |
| voice | `terse` | Fragments, receipts, no recap. |
| | `normal` | Full sentences with short explanations. |
| control | `status` | Print the active modes and whether each came from this session or the saved default. |
| | `off` / `on` | Pause the whole layer (bootstrap, hooks, routing) / resume it. |
| | `default <words>` | Save words as the default for new sessions, e.g. `honey default ultra terse`. |

Shipped defaults: `full`, `light`, `terse`. Session switches last until changed or the session ends.

**The hook does the switching.** Send `honey ultra` or `/honey strict` (Codex: `$honey strict`) as the whole message and the prompt hook applies it before the model runs. If this skill receives mode words instead, the hook didn't fire: honor the modes in conversation for the rest of the session and say in one line that nothing was saved.

## Context hygiene

- **One unbroken thread for grill → plan**, so the plan argues from the same thinking. Compact or clear after the plan is written, not during grilling.
- **`/clear` (Codex: `/new`) between unrelated tasks.** Leftover context from task A steers task B.
- **`handoff` forks; `/compact` continues.** Use `handoff` when you want a fresh session but need this one's state (a prototype detour, a thread nearing its smart zone, the next ticket). Use `/compact` at a phase boundary inside one task when losing verbatim history is fine; never mid-debug or mid-grill, where the details are the work.
- **Fresh session per ticket.** Start each with `execute`, the spec, and that one ticket.
- **Reasoning degrades well before the window is full.** When a long thread starts repeating itself or losing decisions, write a `handoff` and continue fresh rather than pushing on.
