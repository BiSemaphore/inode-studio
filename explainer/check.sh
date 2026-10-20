#!/usr/bin/env bash
# Pre-render gate: timeline (story.py fails on lag), layout lint, sync.
#   explainer/check.sh motion/<piece>
set -euo pipefail
piece="$1"
cd "$(dirname "$0")/.."
PY=.venv/bin/python
[ -x "$PY" ] || { echo "no .venv: run scripts/setup.sh first"; exit 1; }
echo "== build + timeline"
# The build must succeed; a failed build would leave the old page for the checks below.
out=$("$PY" "$piece/story.py" 2>&1) || { echo "$out" | tail -20; echo "build FAILED"; exit 1; }
echo "$out" | grep -E "LATE|ops|timeline" || true
echo "== layout";           node explainer/lint_layout.js "$piece"
echo "== sync";             node explainer/check_sync.js "$piece"
