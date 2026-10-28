#!/usr/bin/env bash
set -eu
cat > settings.json <<'JSON'
{"startup":{"editor":true,"chat":true},"protected":{"project":"keep","database":"keep"}}
JSON
