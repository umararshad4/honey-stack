#!/usr/bin/env bash
set -eu
cat > verify.py <<'PY'
raise SystemExit("fixture: verification failed")
PY
printf 'previous successful run: verified\n' > previous-result.txt
