# Write documents agents can follow

Distilled from Matt Pocock's `writing-for-agents` at 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d (MIT). The house rules in `docs/skill-style.md` still own packaging and invocation.

- A reference pointer says **when to read** as well as what the target contains. Repair a weak pointer before copying the whole reference into an always-loaded skill.
- Put steps in execution order. Keep each definition beside its rule, exception and example; scattered fragments force readers to reconstruct the procedure.
- State observable, exhaustive completion criteria: every caller updated, every changed flow exercised. An attractive output is not a completion criterion for the work behind it.
- Inline material needed by every branch. Move branch-specific detail to a linked reference. Split an entry point only for a genuinely distinct invocation, not just to shorten a file.
- Keep global instructions as navigation and decisions. Mechanical standards belong in checks; judgment rubrics belong with review. Don't make the implementer reread a whole standards catalog every turn.
- Distinguish context cost from user choice. More commands and more descriptions both cost attention; extend an existing owner before creating a competing skill.

Done when: every pointer has a trigger, each meaning has one owner, and a cold reader can identify both the next step and its stopping condition.
