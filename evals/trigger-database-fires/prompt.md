---
max_turns: 3
tags: [trigger, database]
allowed_tools: [Read, Glob, Grep, Skill]
---

Design the Postgres schema and a safe migration to add a nullable `archived_at` column to our 50M-row orders table without downtime.
