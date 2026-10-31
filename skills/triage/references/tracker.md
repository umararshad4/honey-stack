# Tracker operations

Keep the canonical repository/project and item URL fixed throughout the run. Use structured tool fields where available. For CLI bodies, write exact Markdown to a temporary file and pass `--body-file`; never interpolate reporter text into shell commands.

## GitHub reads

Use `gh issue view <number> --repo <owner/repo> --json number,url,title,body,comments,labels,author,createdAt,updatedAt,state` for issue context and `gh pr view` plus `gh pr diff` for PR context. Fetch review threads, linked issues and attachments separately when they are not included. For long activity streams, use paginated `gh api` endpoints. Search both open and closed work; search-index results are leads, so read each claimed match.

Before applying changes, read the repository's labels and issue again. Map state meanings to existing labels. If the mapping is unknown, propose it without creating labels or silently replacing unrelated labels. Keep a record of the original category/state values so a failed partial update can be explained.

Done when: the full relevant context is read and each intended state maps to a known tracker field or is reported as unmapped.

## Authorized writes

- **Comment:** re-read comments to avoid an equivalent repeated triage note, then `gh issue comment` or `gh pr comment` with `--body-file`.
- **Label:** add the mapped new category/state labels and remove only the known superseded category/state labels. Preserve labels for priority, platform, ownership and other workflows.
- **Close:** only when closing the exact item is authorized, after confirming the canonical duplicate or established reason. A weak report with missing evidence remains open for information.
- **Read back:** verify the item URL, requested labels/state and comment content. A successful command exit alone is insufficient proof of the resulting tracker state.

Do not use admin bypass, force-push, auto-merge settings or release commands in triage. Publication and repository automation remain owned by their existing workflows.

Done when: every authorized effect is observed on the intended item, and partial failures are reported without repeating successful writes.

## Other trackers and unavailable access

Use the connected tracker tool for equivalent read/search/comment/state operations, honoring its native fields. Resolve project, team and state IDs from that tracker. If an operation or required access is unavailable, return a local triage report or draft with the missing capability. Never create an issue in a different repository/project as a fallback.

Done when: the same qualification evidence is available through the adapter, or its precise capability limit is visible in the report.
