---
max_turns: 5
tags: [workflow-skills, workflow-explicit]
allowed_tools: [Read, Glob, Grep, Skill]
---

/honey:statechart A teammate drew a queue diagram and checked a TLA+ model with two workers and at most one retry. No counterexample appeared. They want to say production can never process a job twice, although the database write was modeled as atomic and real persistence was never tested. Assess that claim only; do not install tools or write files.
