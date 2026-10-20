#!/usr/bin/env bash
# One-time setup: checks the tools, installs puppeteer-core, builds .venv
# (Python 3.12) and downloads the Kokoro voice model into tts/.
# Safe to run again: finished steps are skipped.
#   scripts/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

need() { command -v "$1" >/dev/null || { echo "missing: $1 ($2)"; exit 1; }; }
need node "https://nodejs.org"
need ffmpeg "macOS: brew install ffmpeg; Debian/Ubuntu: apt install ffmpeg"
need curl "needed to download the voice model"
node tools/chrome.js >/dev/null || { node tools/chrome.js; exit 1; }
echo "== chrome: $(node tools/chrome.js)"

echo "== node packages"
npm install --no-audit --no-fund

echo "== python environment (.venv)"
if [ ! -x .venv/bin/python ]; then
  if command -v uv >/dev/null; then
    uv venv --python 3.12 .venv
  elif command -v python3.12 >/dev/null; then
    python3.12 -m venv .venv
  else
    echo "missing: Python 3.12 (install uv, https://docs.astral.sh/uv/, and run this again)"; exit 1
  fi
fi
if command -v uv >/dev/null; then
  uv pip install --python .venv/bin/python -r requirements.txt
else
  .venv/bin/pip install -r requirements.txt
fi

echo "== voice model (tts/)"
BASE=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
sha() { if command -v shasum >/dev/null; then shasum -a 256 "$1"; else sha256sum "$1"; fi | cut -d' ' -f1; }
fetch() {
  local name="$1" want="$2"
  if [ -f "tts/$name" ] && [ "$(sha "tts/$name")" = "$want" ]; then
    echo "tts/$name: ok"; return
  fi
  echo "tts/$name: downloading"
  curl -L --fail --progress-bar -o "tts/$name.part" "$BASE/$name"
  [ "$(sha "tts/$name.part")" = "$want" ] || { echo "tts/$name: checksum mismatch"; rm -f "tts/$name.part"; exit 1; }
  mv "tts/$name.part" "tts/$name"
}
fetch kokoro-v1.0.onnx 7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5
fetch voices-v1.0.bin bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d

echo
echo "ready. try the example:"
echo "  npm run preview --piece=examples/hello"
echo "  npm run video   --piece=examples/hello"
