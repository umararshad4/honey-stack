# REA setup and recovery

REA is installed and driven through the `rea-agents` npm package (Node.js 22.19+/24.11+/26+). honey-stack does not bundle it.

## Install (user approves)
```bash
npx -y rea-agents@latest setup --client <client> --dry-run --json   # read-only plan
npx -y rea-agents@latest setup --client <client> --yes              # after approval
```
Clients: `claude_code`, `codex`, `cursor`, `gemini_cli`, `windsurf`, `devin`, `opencode`, `antigravity`, `copilot_cli`, `vscode`, `grok_build`, and others. Setup adds the MCP server, writes REA's own workflow skill, and backs up existing config. Restart the agent afterward.

## Diagnose when tools are missing
```bash
npx -y rea-agents@latest doctor --client <client> --json
```
- **Missing/stale registration** → rerun scoped `setup`.
- **Registered but no tools this session** → restart/reconnect the agent (doctor can't prove the live agent connected).
- **Missing provider** → affects only tasks needing it. Static JS needs no engine; native needs Hopper/Ghidra/IDA; Android needs JADX + JDK. REA never installs these.

## CLI fallback (no MCP)
```bash
npx -y rea-agents@latest analyze-javascript-application /absolute/path/to/app --json
```
Returns the evidence record directly. Read its limitations and unknowns the same as an MCP result.

## Official sources only
Install from `morluto/rea`, rea.tools, or the `rea-agents` npm package. A similar repo name or copied README does not make a download official.
