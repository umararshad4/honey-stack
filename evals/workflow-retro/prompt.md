---
max_turns: 5
tags: [workflow-skills, workflow-explicit]
allowed_tools: [Read, Glob, Grep, Skill]
---

/honey:rsi retro
For a retrospective only: In a synthetic session the agent repeatedly used a prohibited import; the repo already has a lint rule for it, but CI never runs that command. The proposed remedy is another global paragraph saying never use that import. Assess the best remedy without editing files, invoking a CLI retro subcommand or publishing an issue.
