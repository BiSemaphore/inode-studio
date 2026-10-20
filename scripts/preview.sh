#!/usr/bin/env bash
# Build the page and open it in Chrome with the preview player.
#   scripts/preview.sh <group>/<piece>
# shellcheck source=scripts/lib.sh
. "$(dirname "$0")/lib.sh" "${1:-}"
"$PY" "$PIECE/story.py" >/dev/null
node -e "require('child_process').spawn(require('./tools/chrome'), [process.argv[1]], {detached: true, stdio: 'ignore'}).unref()" \
  "file://$ROOT/$PIECE/piece.html?preview"
