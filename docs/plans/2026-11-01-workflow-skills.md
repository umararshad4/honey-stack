# Workflow skills plan

**Goal:** Implement every accepted skill recommendation while preserving Honey's main flow.
**Approach:** HOLD scope: four new user-invoked skills and targeted references/branches in existing skills. Reuse the current CLI, verification records, and delivery gates; importing entire collections or building a second agent runtime would create overlap.
**Design:** Accepted recommendations in the conversation.

## What already exists
`verify`, `qa`, `frontend`, `review`, `perf`, `rsi`, `write-skill`, `plan`, and `execute` own the main flow. Stageshow v0.14.0 supplies product-demo assets. Existing skill metadata, licenses, budget tests, and eval runner cover packaging.

## Global constraints
- No new always-loaded workflow; four new entry points are user-invoked with Codex metadata.
- Preserve attribution with pinned upstream revisions; adapt host-specific tools and omit upstream ceremonial replies.
- References are loaded by explicit conditions. Keep skills under 150 lines where practical.
- A skill is guidance, not a running GitHub bot or automatic permission grant. Keep remote publishing and merge behavior unchanged.
- Generated verification harnesses preserve user processes/data and distinguish unavailable prerequisites from proof.
- Triage records evidence, deduplicates, creates actionable briefs, and verifies fixes before recommending delivery.
- Existing app motion uses its own stack; Stageshow owns mocked illustrations and demos.

## File map / ownership
- `skills/project-verify/**`: creation and maintenance of project-local feature verification (lane 1).
- `skills/triage/**`: tracker triage and bounded reproduce/fix workflow, including Benny's discipline (lane 2).
- `skills/frontend/**`, `skills/qa/**`, `skills/stageshow/SKILL.md`: motion, worst-case data and mobile behavior (lane 3).
- `skills/research/**`, `skills/statechart/**`: primary-source research and bounded model checking (coordinator).
- `skills/{honey,verify,review,perf,rsi,write-skill,grill,plan,execute}/**`: routing and targeted improvements (coordinator).
- `README.md`, `THIRD_PARTY.md`, `docs/skill-style.md`, `evals/workflow-*/**`, `tests/test_workflow_skills.py`: documentation and validation (coordinator).

## Parallel lanes
| Lane | Files | Depends on |
|---|---|---|
| 1 | project-verify only | accepted scope |
| 2 | triage only | accepted scope |
| 3 | frontend, qa, stageshow only | v0.14.0 baseline |
| Coordinator | remaining files above | integrate lane outputs before final tests |

## Tasks
- [x] Add project-verify create/maintain with actual launch/doctor/drive/evidence/cleanup and feature coverage; run its focused packaging and behavior checks.
- [x] Add triage with needs-info/ready/duplicate/rejected decisions, full report reads, before/after proof and existing-fix handling; run focused checks.
- [x] Expand motion review/performance, worst-case UI and mobile QA; clarify Stageshow boundary; run focused checks.
- [x] Add primary-source research and optional statechart model-checking; integrate routing and RSI retrospective, agent-writing and performance guidance.
- [x] Add evals covering unavailable prerequisites, ambiguous issues, source uncertainty, bounded proofs, motion-only reviews and repeated instruction failures; compare baseline/new behavior where the runner permits.
- [x] Run full Python suite, release consistency, skill doctor and diff checks; review every changed file against scope.

## Review focus / failures
| Surface | Failure | Proof |
|---|---|---|
| Project verification | Cleanup kills a user process or erases evidence | ownership and evidence-survival behavior eval |
| Triage | Unclear report gets treated as a confirmed fix or auto-close | missing-evidence behavior eval |
| Motion | Demo stack imported into production components | motion review routing eval |
| Research | Secondary claim presented as verified primary fact | uncertainty behavior eval |
| Statechart | Bounded model result presented as proof of production | model scope behavior eval |
| RSI | More generic prose instead of a deterministic check | retrospective behavior eval |

## Not in scope
Activating a hosted bot, creating secrets, posting or closing live issues, committing, pushing, releasing, or installing this development tree globally. These were not requested by the accepted skill-addition scope. The earlier bot credential decision remains pending.

## Validation record
- Packaging/reference-link tests: passed; four new explicit-only commands have Claude frontmatter and Codex metadata.
- Model-invoked description budget: 3,454/3,500 characters.
- Claude plugin manifest validation: passed (pre-existing optional listing-icon warning).
- Release consistency: v0.14.0 remains consistent; no release bump was made.
- Full Python suite: 38 test files pass with TZ=UTC. Default local timezone reproduces the unchanged baseline failure in test_rsi_budgets.py::test_unknown_usage_is_not_presented_as_zero_total: UTC timestamps are filtered using the local month. The runtime bug is outside this skill-only change.
- Stageshow positive/negative routing and label-only triage behavior: passed.
- Initial natural-language evals passed all eight behavior graders, but five explicit-only commands did not emit an automatic Skill tool call. The test was corrected to use explicit slash commands and behavior grading; automatic invocation is intentionally disabled. Baseline controls already passed the safety behavior checks, so no behavior-quality improvement is claimed from that comparison.
- Static standards/spec review found and resolved label-only comment authorization and explicit-only routing inconsistencies.

Ruling: the requested additions are skill workflows and references. They do not change the RSI background publisher or activate the earlier credential-gated hosted bot.
Ruling: use reference reads for conditional handoffs to explicit-only skills, keeping the standalone command invocation policy intact.

## Final verification
- Eleven distinct one-run behavior/routing cases passed: 3 existing-skill behavior cases, 6 explicit-command cases (including label-only triage), and 2 Stageshow routing cases. Corrected explicit-command results are in /tmp/honey-project-verify-eval and /tmp/honey-explicit-workflow-evals; routing results are in /tmp/honey-stageshow-routing-evals.
- Actual Claude startup metadata exposed all four new slash commands.
- Full UTC suite, skill packaging/reference links, description budget, release consistency and whitespace checks passed. Default-timezone baseline issue remains documented above.
- No runtime, hook, GitHub workflow, installed-cache, remote issue or release changes were made.
