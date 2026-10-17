# Personal instructions

honey-stack (plugin `honey`) supplies the always-on workflow rules: sizing, the ladder, proof before done, decision policy and the receipt line. This file holds only personal preferences.

## Operating principles
- Follow explicit user constraints literally. If the user says frontend only, vendor only, no code changes, or preserve the UI, treat it as a hard boundary.
- Prefer current stable tooling and project-local conventions over inventing a new stack.
- Be pragmatic: say when an idea is risky or not worth it, and offer a cleaner alternative.
- Write clean, scalable, readable code with small modules and clear ownership.
- Do not run full builds in normal sessions unless the change is broad, risky, or the user asks.

## Frontend defaults
- Prefer React, Next.js App Router, TypeScript, Tailwind, and shadcn/ui patterns when the project already uses them.
- Keep server/client boundaries explicit.
- Avoid prop drilling when local composition, context, or query/cache patterns are cleaner.
- Keep components focused. If a component grows past roughly 300 lines, consider extraction.
- Preserve existing UI patterns unless the user asks for redesign.
- For UI changes, verify responsive behavior when the affected surface is meaningful.

## Response style
Be concise. Default to a few lines. No preamble, no recap, no restating the request. Expand only when asked to explain, or when a real risk needs flagging (one or two sentences, then stop).

# graphify
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.
Also use the graphify skill proactively (without being asked) when:
- `graphify-out/graph.json` exists in the project and the user asks any question about the codebase, its architecture, or file relationships — answer via `graphify query` first instead of grepping from scratch.
- The user asks for a map, overview, or architecture explanation of an unfamiliar codebase — offer to build the graph with `/graphify` if none exists.
