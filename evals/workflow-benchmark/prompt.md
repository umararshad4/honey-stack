---
max_turns: 5
tags: [workflow-skills]
allowed_tools: [Read, Glob, Grep, Skill]
---

Use the perf skill. A benchmark says B is 50% faster than A, but B returned HTTP 429 for half the calls. A used a debug build, B a release build. Each ran once and the harness never checked output correctness. Assess the claim only, no execution.
