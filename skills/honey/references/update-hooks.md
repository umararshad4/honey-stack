# Update Honey hooks

Use this flow only when the user explicitly says `update hooks`, `$honey update hooks`, `/honey:honey update hooks`, or asks to update and approve Honey's hooks. The request delegates a one-time review and approval of the installed Honey version and the latest release checked during this run. It does not approve other plugins, future releases, or bypass Codex's trust checks.

## 1. Identify and review

1. Find the configured Honey marketplace checkout and installed plugin. Check the checkout's branch, Git status, remote, installed version and Codex's native hook registry. Run from the marketplace checkout, not another Honey worktree, so Codex resolves the intended plugin.
2. Compare the installed Honey files and hook definitions with the checkout and its published release. Review changes since the last independently verified trusted release, including executable code and dependencies. If that release cannot be identified, review the complete installed release. A sync receipt alone does not prove trust. Verify the release tag and commit against the configured upstream. If the source, installed bytes, release or review cannot be verified, stop and explain why.
3. If the current Honey hooks need approval, review them in Codex's `/hooks` UI. Approve only Honey hooks. Use a bulk approval only if both the registry and the UI show that every pending hook belongs to `honey@honey-stack` and matches the reviewed version. If that cannot be established, use individual entries or stop. Do not change stored trust hashes or use a trust-bypass flag.

## 2. Update and review again

1. From the verified marketplace checkout, run `python3 bin/honey autoupdate --now`. This checks release tags immediately; it does not override opt-out, concurrent updates, local changes or a diverged checkout. Read the JSON result. If a check is already in progress, wait for it to finish and retry once. Any other skipped or failed check is not an update; report its reason.
2. If the release changed, review the release diff and inspect the new installed files against that release. Review the new Honey hook definitions in `/hooks` using the same checks above. A plugin update can require approval again, even if its hook commands did not change.
3. Start a real new Codex session from the marketplace checkout without bypass flags. Use its actual session ID with `honey doctor --agent codex --session <id> --json`. Check the installed version, native trust status and observed session events separately. Report whether they agree and name any missing proof. The request does not authorize approving the next release without a new request.

If a native review UI is unavailable or a review cannot be completed, stop and report the blocker. Never assert that a text command itself grants Codex trust.
