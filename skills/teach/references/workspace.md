# Teaching workspace formats

Create each file or directory only when there is something to put in it.

## MISSION.md

```md
# Mission: {Topic}

## Why
{1-3 sentences: the concrete outcome they're chasing. "Ship a Rust CLI to my team", not "learn Rust".}

## Success looks like
- {A specific, observable thing they will be able to do}

## Constraints
- {Time, budget, learning preferences}

## Out of scope
- {Adjacent topics they don't want to chase now}
```

One mission per workspace, under a screen long. When the goal moves, update it (after confirming with the user) and write a learning record about the shift.

## learning-records/NNNN-slug.md

Numbered one past the highest existing record.

```md
# {What was learned or established}

{1-3 sentences: what is now known, and why it changes what to teach next.}
```

Optional, only when they carry information: `Status: active | superseded by LR-NNNN`; **Evidence** (the checkpoint answered, the exercise done, the experience cited); **Implications** (what this unlocks or rules out).

Write one when:
1. They showed real understanding of something non-trivial: evidence, not exposure.
2. They stated prior knowledge ("I already know X"), with the depth they claimed.
3. A misconception was corrected. These predict where related topics will trip them.
4. The mission shifted.

Not: material merely covered, a term already in `GLOSSARY.md`, or a session log. When a later record contradicts an earlier one, mark the old one superseded instead of deleting it.

## RESOURCES.md

```md
# {Topic} resources

## Knowledge
- [Title, author](url)
  What it covers. Use for: {when to reach for it}.

## Wisdom (communities)
- [Community](url)
  Use for: {feedback from practitioners}.

## Gaps
- {An area the mission needs with no good source yet}
```

High-trust only: primary sources, recognized experts, well-moderated communities. Annotate every entry. Remove sources that proved wrong or shallow. If the user doesn't want communities, note it here.

## GLOSSARY.md

```md
# {Topic} glossary

**Term**:
One or two sentences on what it is.
_Avoid_: {looser words for the same thing}
```

Add a term only once they can use it correctly. Use glossary terms inside other definitions. Revise in place as understanding deepens.
