# shellcheck shell=bash
# Shared by the npm scripts: repo root, the .venv Python, and the piece path.
#   . scripts/lib.sh "$1"     sets ROOT, PY, PIECE (motion/<group>/<piece>)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || { echo "no .venv: run scripts/setup.sh first"; exit 1; }
[ -n "${1:-}" ] || { echo "which piece? npm run <script> --piece=<group>/<piece>"; exit 1; }
PIECE="motion/$1"
[ -f "$PIECE/story.py" ] || { echo "$PIECE/story.py not found (npm run new --piece=$1 starts one)"; exit 1; }
