# Autonomous RSI delivery

**Goal:** Honor the user's opt-in to automatic push, validated merge, release and installation without routine approval prompts.
**Scope:** Evaluated RSI skill patches only. Unsupported suggestions remain issues, not executable changes.

- [x] Add `publish automatic` opt-in without changing existing review-only defaults.
- [x] Require the exact published head and base, all four successful CI jobs, mergeability and repository review policy before merging.
- [x] Resume merged proposals until a stable release includes their merge; sync the local installation.
- [x] Preserve private evaluation history in a local backup branch; refuse to overwrite unrelated local changes or commits.
- [x] Run policy, Git-history preservation and full compatibility tests, and review trust boundaries.
- [ ] Push, merge after CI, and verify the released and installed versions.

Existing session/weekly RSI passes drive retries; no busy polling or new daemon. The ordinary hourly session-start updater remains enabled by this explicit automatic-delivery command. Public issues alone never authorize code or create releases.
