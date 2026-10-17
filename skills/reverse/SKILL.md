---
name: reverse
description: "Reverse-engineer software you're authorized to study, via the REA toolchain: understand a shipped app, binary, APK, Electron/JS bundle, .NET assembly, website, firmware or network capture without its source, with evidence. Use for 'how does app X do Y', interop, or security research on your own/authorized targets."
disable-model-invocation: true
license: MIT
metadata:
  sources: "morluto/rea (REA, MIT) README, docs/mcp-contracts.md, docs/installation.md, .agents/skills/reverse-engineer-anything/SKILL.md"
---

# reverse

Drive [REA](https://github.com/morluto/rea) ("Reverse Engineer Anything") to study a shipped target without its source: native binaries, JavaScript/Electron apps, .NET, Android APKs, websites, firmware, and saved network captures. REA returns findings tied to evidence; you explain the behavior or rebuild it.

## Authorized use only — check first

Reverse engineering is lawful for many purposes (interoperability, security research, debugging, learning) but not all, and licenses and local law differ. Before analyzing anything, confirm in one line that the target is one of:

- software the user owns, wrote, or runs
- an explicit, in-scope authorized engagement (pentest, bug bounty, audit)
- a public CTF or research target meant to be analyzed

If it's none of these, or the user wants to strip DRM, forge licensing, clone a competitor wholesale, or defeat another party's protection, **stop and say so** — don't run REA. When in doubt, ask who owns the target and why. Analysis runs locally under the user's own permissions, and runtime capture actually executes the target, so never widen the scope beyond what the user named.

## Is REA connected?

REA is a separate MCP server; honey-stack does not bundle it. Check once:

1. If `mcp__rea__*` tools (or a `rea` CLI) are already available, use them directly — don't re-run setup.
2. If not, it's a one-time install the user approves:
   ```bash
   npx -y rea-agents@latest setup --client claude_code --dry-run --json   # or --client codex
   ```
   Show the proposed paths, backups and changes, get a yes, then rerun with `--yes`. Restart the agent so the tools load. `references/setup.md` has the recovery steps and the client list.
3. Static JavaScript needs nothing more. Native work needs Hopper, Ghidra or IDA already installed; APKs need JADX + a JDK. REA never installs Node, Java, Ghidra, IDA or JADX for you.

## Workflow

1. **Scope.** Turn the question into a checklist ("where is feature Y handled, and how"). Resolve which file/app/binary is the target from the conversation before asking again.
2. **Start small.** Open the target, take the smallest useful overview (inventory, module graph, manifest), then follow one hypothesis from its entry point. Expand only where the evidence leaves a concrete gap. Reuse an existing REA session; don't open duplicates.
3. **Right evidence for the claim.** Prefer static inspection. Use runtime observation only when static can't answer it and the user authorized running the target. Never describe static analysis as if it observed execution.
4. **Cite evidence.** Every conclusion separates observations, inferences, and unknowns, and names the REA Evidence IDs behind it. Keep REA's stated limitations and coverage gaps; don't round them away.
5. **Finish.** Explain in plain language. If the user wants to build their own version, switch to normal coding skills (`plan`, `tdd`, `verify`) and keep observed behavior separate from your design choices. Close a native session (`close_binary`) when done.

See the target-specific guides: `references/targets.md`. For deeper REA features, read its own docs under `docs/` in the REA repo rather than guessing tool names — use the connected server's real tool list and input schemas.

## When NOT to use REA

For ordinary analysis of a complete source repository you already have, use normal repo tools (`grep`, `architecture`, graphify). REA is for targets whose source you don't have.
