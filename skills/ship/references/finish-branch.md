# Finishing a branch: commands and cleanup

Read after the user picks an option from the finish-branch decision brief.

## Capture state first, from inside the workspace

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
WORKTREE_PATH=$(git rev-parse --show-toplevel)
MAIN_ROOT=$(git -C "$GIT_COMMON/.." rev-parse --show-toplevel)
BRANCH=$(git branch --show-current)   # empty on a detached HEAD
```

`GIT_DIR == GIT_COMMON` means a normal checkout with no worktree to clean up.

The base is the branch this work forked from: its upstream, the plan, or `git merge-base`. If that isn't clear, state your guess in the brief. Merging into the wrong base is expensive to undo.

## 1. Merge locally

```bash
cd "$MAIN_ROOT"
git checkout <base> && git pull
git merge "$BRANCH"
<test command>          # verify the merged result, not the branch
```

If the merged result fails, stop. Leave the branch and worktree in place: nothing has been pushed, so the merge can still be recovered. If it passes, clean up the worktree (below), then run `git branch -d "$BRANCH"`.

## 2. Push and open a PR

Follow the Push and PR sections of the skill. From a detached HEAD, use `git push origin HEAD:refs/heads/<new-branch>`. Keep the worktree, because review fixes happen there.

## 3. Keep as-is

Report: `Keeping <branch>. Worktree at <path>.`

## 4. Discard (only on the typed word "discard")

```bash
cd "$MAIN_ROOT"
# clean up the worktree (below), then:
git branch -D "$BRANCH"
```

## Worktree cleanup (options 1 and 4 only)

- Remove only worktrees you created under `.worktrees/` or `worktrees/`. The host owns any other worktree, so leave it, or use the harness's exit-worktree tool.
- Run the removal from `MAIN_ROOT`: `git worktree remove "$WORKTREE_PATH" && git worktree prune`.
- If removal is refused because of modified or untracked files, those files exist nowhere else. Show `git -C "$WORKTREE_PATH" status --porcelain -uall` and ask whether to commit them, move them to the main checkout, or delete them. Never add `--force` on your own.
