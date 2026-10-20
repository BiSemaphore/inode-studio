#!/usr/bin/env bash
# Checks, render, QA: the whole path from story.py to a checked MP4.
#   scripts/video.sh <group>/<piece>
# shellcheck source=scripts/lib.sh
. "$(dirname "$0")/lib.sh" "${1:-}"
explainer/check.sh "$PIECE"
node tools/record.js "$PIECE/piece.html" "$PIECE/out"
"$PY" explainer/qa.py "$PIECE"
