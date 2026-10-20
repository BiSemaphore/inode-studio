#!/usr/bin/env bash
# Start a new video from the template: explainer/new.sh explainers/ep03-topic
set -euo pipefail
dir="motion/$1"
[ -e "$dir" ] && { echo "$dir already exists"; exit 1; }
mkdir -p "$dir/out"
cp explainer/template/script.md explainer/template/story.py "$dir/"
echo "created $dir: edit script.md (narration) and story.py (scenes), then: npm run preview --piece=$1"
