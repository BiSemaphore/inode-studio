#!/usr/bin/env bash
# Progress of the three most recent renders.
set -euo pipefail
cd "$(dirname "$0")/.."
for f in $(ls -t motion/*/*/out/progress.txt 2>/dev/null | head -3); do
  echo "$(basename "$(dirname "$(dirname "$f")")"): $(cat "$f")"
done
