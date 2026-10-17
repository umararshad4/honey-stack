#!/usr/bin/env bash
# Find which test file creates an unwanted file or directory.
# Adapted from obra/superpowers 7.0.0 skills/systematic-debugging/find-polluter.sh
# (MIT, Jesse Vincent): runner is configurable, emoji removed.
#
# Usage:   find-polluter.sh <path_to_watch> <test_glob>
# Example: find-polluter.sh '.git' 'src/**/*.test.ts'
#          TEST_CMD='npx vitest run' find-polluter.sh 'tmp/leak.db' 'test/**/*.spec.ts'
#
# TEST_CMD is the command that runs one test file (default: npm test --).
# Exits 1 and names the polluter when found, 0 when every file is clean.

set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 <path_to_watch> <test_glob>" >&2
  exit 2
fi

WATCH="$1"
PATTERN="${2#./}"
TEST_CMD="${TEST_CMD:-npm test --}"

if [ -e "$WATCH" ]; then
  echo "'$WATCH' already exists. Remove it first, then re-run." >&2
  exit 2
fi

# find -path can't match '**/' against zero directories, so also try the
# pattern with '**/' collapsed to cover files directly under the base dir.
FILES=$(find . \( -path "./$PATTERN" -o -path "./${PATTERN//\*\*\//}" \) -type f | sort -u)
if [ -z "$FILES" ]; then
  echo "No test files match '$PATTERN'." >&2
  exit 2
fi
TOTAL=$(printf '%s\n' "$FILES" | wc -l | tr -d ' ')

echo "Watching for: $WATCH"
echo "Runner: $TEST_CMD <file>"
echo "Test files: $TOTAL"

COUNT=0
while IFS= read -r FILE; do
  COUNT=$((COUNT + 1))
  echo "[$COUNT/$TOTAL] $FILE"
  $TEST_CMD "$FILE" >/dev/null 2>&1 || true
  if [ -e "$WATCH" ]; then
    echo
    echo "FOUND POLLUTER: $FILE"
    echo "Created: $WATCH"
    ls -la "$WATCH"
    echo
    echo "Next: run '$TEST_CMD $FILE' alone and read its setup and teardown."
    exit 1
  fi
done <<< "$FILES"

echo "No polluter found: every test file is clean."
exit 0
