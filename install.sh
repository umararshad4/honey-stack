#!/usr/bin/env bash
# honey-stack one-line installer.
#   curl -fsSL https://raw.githubusercontent.com/umararshad4/honey-stack/main/install.sh | bash
# Clones (or updates) the repo to ~/.honey-stack/repo and runs the reversible installer with a dry run first.
set -euo pipefail

REPO_URL="https://github.com/umararshad4/honey-stack.git"
DEST="${HONEY_STACK_DIR:-$HOME/.honey-stack/repo}"

command -v git  >/dev/null || { echo "honey-stack needs git on PATH."; exit 1; }
command -v python3 >/dev/null || { echo "honey-stack needs python3 (3.9+) on PATH."; exit 1; }

if [ -d "$DEST/.git" ]; then
  echo "Updating honey-stack in $DEST ..."
  git -C "$DEST" pull --ff-only --tags -q
else
  echo "Cloning honey-stack into $DEST ..."
  mkdir -p "$(dirname "$DEST")"
  git clone -q "$REPO_URL" "$DEST"
fi

echo
echo "Dry run (nothing is changed yet):"
python3 "$DEST/bin/honey" install --dry-run || true
echo
echo "Review the plan above. To apply it, run:"
echo "    python3 \"$DEST/bin/honey\" install"
echo "Then: start a new Claude Code session; in Codex run /hooks and trust the honey entries."
