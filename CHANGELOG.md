# Changelog

All notable changes to honey-stack. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/):

- **MAJOR**: breaking changes to hook commands (Codex would need to re-trust), the `~/.honey` data layout, or the CLI
- **MINOR**: new skills or RSI capabilities
- **PATCH**: fixes

Releases are cut with `python3 scripts/release.py X.Y.Z --push`. GitHub Actions then publishes the release from this file.

## [Unreleased]

### Added
- **Reply indicator.** Every reply starts with `🍯 HONEY`, plus any non-default mode (e.g. `🍯 HONEY · ultra · strict`), so you can see at a glance that honey-stack is on. `honey off` hides it.

### Fixed
- The `review` skill now fires reliably on short pasted diffs: the bootstrap routes "review code/diff/PR" requests to the skill instead of an inline opinion (trigger eval 3/3, up from 2/3).
- Verified the Codex agent role format against Codex 0.163: all 4 `honey-*` agents are discovered.

## [0.2.0] - 2026-10-17

### Added
- `honey --version`.
- Release tooling: `scripts/release.py` (bumps every version field, rolls the changelog, tests, tags), CI on macOS and Linux with Python 3.9 and 3.12, and GitHub releases published automatically from tags.
- Install straight from GitHub on both agents: `claude plugin marketplace add umararshad4/honey-stack` and `codex plugin marketplace add umararshad4/honey-stack`.

### Changed
- `honey install` now leaves your `CLAUDE.md` / `AGENTS.md` and your other skills alone by default. Overwriting the instruction files (`--slim-instructions`) and retiring absorbed MCT / Matt Pocock duplicates (`--retire-legacy`) are opt-in.
- Rewrote the README as a public quick-start.

## [0.1.0] - 2026-10-17

### Added
- An always-on bootstrap for Claude Code and Codex: task sizing, the smallest-complete-change ladder, proof before done, decisions over questions. Three mode axes (`honey ultra|lite|full`, `strict|light`, `terse|normal`) plus `honey off`.
- 22 skills distilled from Superpowers, Ponytail, Matt Pocock's skills, pstack and gstack, plus 4 subagents (also rendered for Codex).
- Safety hooks: a destructive-command guard, a scan for secrets in newly written text, and a receipt gate that only fires after turns that edited files.
- The RSI engine:
  - an observer with harness-origin filtering and an event log shared by both agents
  - `remember:` notes
  - a detached reflector with budget caps
  - a deterministic curator: promotion after 2 sessions, decay, budgets
  - `/rsi review` (Tier 1 instruction edits, Tier 2 eval-gated skill patches on branches, Tier 3 learned guards)
  - `/rsi coach`, `/rsi bootstrap`, the upstream radar, a golden suite and holdout sessions
- `honey install | uninstall | doctor | sync`: dry-run first, recorded in a manifest, fully reversible.

[Unreleased]: https://github.com/umararshad4/honey-stack/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/umararshad4/honey-stack/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/umararshad4/honey-stack/releases/tag/v0.1.0
