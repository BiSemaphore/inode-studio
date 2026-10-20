#!/usr/bin/env bash
# Review an explainer before showing it: a frame every STEP seconds, laid out
# as contact sheets of 10 frames (sheet-01.png, sheet-02.png, ...).
#   explainer/review.sh motion/<piece>/piece.html <outdir> [step]
set -euo pipefail
piece="$1"; out="$2"; step="${3:-1}"
total=$(grep -o 'duration: [0-9.]*' "$piece" | head -1 | awk '{print $2}')
rm -rf "$out"; mkdir -p "$out/frames"
times=$(.venv/bin/python -c "import sys; t,s=float(sys.argv[1]),float(sys.argv[2]); print(' '.join(f'{i*s:.1f}' for i in range(int(t/s)+1)))" "$total" "$step")
node tools/peek.js "$piece" "$out/frames" $times > /dev/null
n=0
for chunk in $(ls "$out/frames" | sort -t t -k2 -n | xargs -n 10 | tr ' ' ','); do
  n=$((n + 1)); d="$out/part$n"; mkdir -p "$d"
  for f in ${chunk//,/ }; do cp "$out/frames/$f" "$d/"; done
  .venv/bin/python tools/sheet.py "$d" "$out/sheet-$(printf %02d $n).png" > /dev/null
done
echo "$n sheets in $out"
