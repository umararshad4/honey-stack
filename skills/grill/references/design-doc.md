# Design doc and builder check

Distilled from obra/superpowers 7.0.0 `skills/brainstorming/SKILL.md` and `builder-check-prompt.md` (MIT, Jesse Vincent).

## Where it goes

`docs/designs/YYYY-MM-DD-<slug>.md` in a repo, unless the repo already keeps designs or specs somewhere else; follow the repo's convention. Outside a repo, ask where.

## Template

Write a plain document a talented builder in the domain could plan from without going back to the user.

```markdown
# <Name> design

## Intent
<What this is for, who it serves, and why now. The why in the user's words.>

## Goals / non-goals / anti-goals
- Goal: ...
- Non-goal: ...
- Anti-goal: <what would make this a failure even if it technically works>

## Constraints
<Platform, versions, budgets, deadlines, compatibility. Exact values.>

## Decisions
- <decision> (user)
- <decision> (delegated: my call, because ...)

## Left to the builder
<What the user explicitly doesn't care about.>

## Out of scope
<Considered and ruled out, one line each with the reason.>
```

## Builder check

Before handing the doc over, have a fresh reader try to plan from it. Tell the user a reviewer reads it first and you may come back once with a few questions.

Dispatch a fresh subagent with this prompt (fill in the domain and path). Without a subagent tool, read the doc yourself as that builder.

```
You are a talented <DOMAIN, e.g. "software engineer">. You've been handed a
design document and asked to plan what it describes. You cannot talk to
its author.

Read <DOC_PATH>.

Report only the questions you'd still need answered to plan this well:
places where you'd have to guess and a wrong guess would matter. For each,
give the question and why the answer changes the plan. Rank by importance.

Skip anything the document leaves to the builder, anything you could
reasonably decide yourself, and wording nitpicks.

If nothing important is left, say "nothing important left".
```

Sort what comes back into three piles:

- **Answered already** by the conversation or the repo: put the answer in the doc.
- **Minor**: a sensible builder could settle it without changing what gets built. Settle it and mark it in Decisions as your call.
- **Theirs**: only the user can answer it, and the answer changes what gets built. Bring these in one message, most important first.

Update the doc with their answers, then hand it over with a short list of the calls you made so they can check those while reading. That's the only question round the check produces.
