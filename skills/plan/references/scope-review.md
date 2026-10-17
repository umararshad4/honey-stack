# Scope review

Distilled from garrytan/gstack `plan-ceo-review` Step 0 and `plan-eng-review` Step 0 (MIT, Garry Tan). Run it before writing tasks for project-size work.

## 1. Premise

1. Is this the right problem? Could a different framing give a much simpler or more valuable solution?
2. What's the actual user outcome? Is the plan the most direct path to it, or is it solving a proxy?
3. What happens if we do nothing? Real pain, or hypothetical?

## 2. What already exists

Map each sub-problem to existing code that already solves it fully or partly. Prefer capturing outputs from existing flows over building parallel ones. If the plan rebuilds something, say why rebuilding beats refactoring. For each new pattern or piece of infrastructure, check whether the runtime or framework has a built-in.

## 3. Approaches

Write two or three distinct approaches:

```
APPROACH A: <name>
  Summary: <1-2 sentences>
  Effort:  S | M | L | XL
  Risk:    low | med | high
  Pros:    <2-3 bullets>
  Cons:    <2-3 bullets>
  Reuses:  <existing code or patterns>
```

One is the minimal viable version (fewest files, smallest diff). One is the ideal architecture (best six-month trajectory). Weigh them equally: recommend whichever best serves the goal, including "scrap it and do this instead" when the foundation is wrong. Close with `Recommendation: <X> because <reason>`. Choosing between approaches that change what gets built is the user's call: one decision brief.

**Complexity smell:** more than 8 files touched or more than 2 new services or classes. Name what looks overbuilt and propose the smaller version before going further.

## 4. Scope mode

| Mode | Posture | Default when |
|---|---|---|
| EXPANSION | Push scope up. What's the 10x version for 2x the effort? What adjacent 30-minute touches would make it sing? | Greenfield feature; the user says "go big" |
| SELECTIVE | Hold the scope and make it bulletproof, but surface each expansion separately for the user to cherry-pick, with neutral effort and risk. | Enhancing an existing system |
| HOLD | Scope is accepted. Make it bulletproof: failure modes, edge cases, observability. Neither add nor cut silently. | Bug fix, refactor |
| REDUCTION | Find the minimum that ships the core outcome; everything else becomes a follow-up. Separate "must ship together" from "nice to ship together". | Plan touches more than 15 files; honey scope `ultra` |

Expansions are opt-in, one decision brief each, with three options: add to this plan, defer (write it down under "Not in scope" with the reason), or skip. Raise scope concerns once, here. After the mode is chosen, execute it faithfully: in REDUCTION don't sneak scope back, in EXPANSION don't argue for less.

## 5. Decide now, not mid-build

Walk the implementation forward and resolve what the implementer would otherwise hit cold:

- Foundations: what does the implementer need to know first?
- Core logic: what ambiguities will they hit?
- Integration: what will surprise them?
- Polish and tests: what will they wish had been planned?

Answer what the repo can answer. Bring only product calls to the user.
