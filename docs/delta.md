# Use Delta history with Honey

Honey's optional Delta integration helps you find a past decision and continue work with its original context. It uses the Delta CLI already installed on your computer. No extra service or model provider is required for lookup.

## Install and check

Follow the [README installation steps](../README.md#install-delta), then run:

```bash
honey delta status
```

Delta 0.22.0 or newer and a signed-in Delta account are required to read history. Installation and sign-in are separate from recording or uploading conversations.

| Capability | Claude Code | Codex |
|---|---|---|
| Search, read and recall existing Delta history | Yes | Yes |
| Attach history to a local handoff | Yes | Yes |
| Record new sessions | Separate official Delta plugin | Not provided |

Use `/honey:delta` in Claude Code or `$delta` in Codex to follow the same workflow through the agent. These are Honey commands. The official capture plugin has its own `/delta` commands.

## Find a decision

```bash
honey delta recall cache expiry
honey delta search authentication --scope user
honey delta search authentication --edited-path 'src/**'
```

Every keyword group must match. Use a quoted group such as `'login|authentication'` for alternatives. `--scope` accepts `user`, `messages`, `visible`, `metadata` or `auto`. The default searches user and assistant messages. `visible` also searches tool output; `auto` lets Delta try generated metadata first.

`recall` finds the strongest latest literal keyword match and returns nearby messages with their original numbers. Read the excerpt before treating it as a final decision. If several conversations match, Honey returns the candidates. Refine the query or pass `--thread` with the intended reference.

Search returns five matches by default; `--limit` accepts 1 to 20. Use specific terms and an edited-path filter to avoid unrelated conversations.

## Read exact messages

Set `THREAD_ID` to an ID returned by search or a Delta join URL, then run:

```bash
honey delta read "$THREAD_ID" --messages 1-1
honey delta summary "$THREAD_ID"
```

Reads start with one message. Ranges are inclusive, must fit the conversation, and can contain at most 20 messages. For example, `--messages 21-40` reads the next complete page of a longer thread.

`summary` reports `fresh`, `stale` or `missing`; it returns summary text only when Delta marks it fresh. It does not dump the full transcript.

Output defaults to 12,000 characters. `--max-chars` accepts 2,000 to 64,000 on search, recall, read, summary and restore. When `truncated` is true, narrow the message range or increase the budget before relying on an omitted detail. A `partial` recall means the returned excerpt does not contain every matched keyword group.

## Preserve a handoff

First use the `handoff` skill to write a local summary. Set `HANDOFF_FILE`, `THREAD_ID` and `TEST_REPORT` to the actual file paths and thread reference, then attach the relevant messages:

```bash
honey delta attach "$HANDOFF_FILE" "$THREAD_ID" --messages 1-1 --evidence "$TEST_REPORT"
honey delta restore "$HANDOFF_FILE"
```

`attach` keeps the human summary and adds a metadata block containing the verified thread reference, Git revision, working files, staging state and evidence-file hashes. Store the handoff outside the repository, as the handoff skill does, so it does not enter a commit.

`restore` compares that record with your current checkout. It reports changed Git state and changed or missing evidence, then reads the saved history if available. Saved test results remain historical; run the required checks again before claiming the current code passes.

Pass `--project /path/to/repository` when running outside the intended checkout. If the recording host supplies a source/session binding, add `--source SOURCE --external-id SESSION_ID` to `attach`. Honey then checks upload and access independently. Use the supplied binding; do not guess it from a conversation title.

A local thread ID does not prove that a share link exists. Honey preserves an actual verified link when supplied and keeps the local summary when history cannot be read.

## Choose capture deliberately

The [official Claude plugin](https://delta.dev/docs/cli/claude-code) performs recording. After installing it, `/delta setup` offers these repository policies:

| Mode | Behavior |
|---|---|
| Manual | Capture starts when you explicitly share or sync a session. |
| Private | New sessions upload for your account. |
| Organization | New sessions upload and are shared with the chosen organization. |

Honey can preview the same local policy. Run `delta org list` to find the intended organization ID, then replace `ORG_ID` below:

```bash
honey delta setup --mode private --organization ORG_ID
```

The preview writes nothing. Add `--apply` only when you want that policy. Honey preserves unrelated settings, excludes `.delta/settings.json` from Git and refuses tracked settings or symlinked targets. The policy applies to new Claude sessions. Configured capture is not proof that a session has synchronized.

Private synchronization still stores conversations and checkout data on Delta's servers. Installing Honey, reading history and attaching local handoff metadata do not upload a session. Honey does not treat retrieved messages as RSI feedback, new approval or current test evidence.

## Understand readiness and failures

| Field or result | Meaning |
|---|---|
| `ready: true` | Delta is installed and authenticated. |
| `capture.configured` / `capture.enabled` | A local policy exists / enables automatic capture. |
| `readiness.history_readable` | A requested thread was actually read; `null` means unverified. |
| `readiness.cloud_uploaded` | The requested thread's upload is complete; `null` means unverified. |
| `cloud.state` | The observed upload state, such as queued, uploading or uploaded. |
| `not_installed` | Install Delta or continue with the local handoff. |
| `signed_out` / `signing_in` | Complete `delta auth login`. |
| `not_visible` / `wrong_account` | Check the account and the thread's invitation or organization. |

For thread readiness, use the exact binding from the recording host:

```bash
honey delta status --thread "$THREAD_ID" --source "$SOURCE" --external-id "$SESSION_ID"
```

An empty search is a valid result. A failed command is not empty history. Honey retries a read once only when Delta explicitly marks the error retryable and the retry delay is short enough.

If the native app reports a connection or startup problem, open it with `delta open` and retry. If an upload stays queued, let Delta connect and recheck its status. Local reads do not prove cloud synchronization or recovery on another computer.

## Test the integration

```bash
python3 tests/test_delta.py
python3 tests/test_delta_handoff.py
python3 tests/qa_delta.py --live
```

The live QA command creates only private, projectless synthetic history and archives it afterwards. It never attaches your repository or records your conversation. For paired before/after measurements and the larger acceptance matrix, follow the [QA guide](../evals/webmcp/README.md#recall-and-handoff-comparison). Cloud upload, local retrieval and cross-machine recovery are separate claims.
