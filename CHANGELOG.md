# Changelog

## 0.1.0 (unreleased)

First release, split out of the inode studio.

- Explainer kit: `script.md` + `story.py`, scene templates (Terminal, Board,
  Statement), themes (whiteboard, blackboard, clean), local Kokoro voice with
  forced-alignment word timings, soundtrack mix.
- Deterministic HTML-to-MP4 recorder with still-frame skipping and broken-frame
  recapture.
- Checks: timeline, layout lint, key-sound sync, loudness and SRT QA.
- `brand.json` for end card, logo and colours; nothing brand-specific in the code.
- Chrome found on macOS and Linux, or `CHROME_PATH`.
- `scripts/setup.sh`: one Python 3.12 environment, checksummed model download.
  Every Python script runs in that environment.
- rough.js bundled in `explainer/vendor/`: renders need no network after setup.
- A piece's `story.py` finds the kit at any folder depth under `motion/`.
- npm scripts report a missing `--piece`, a missing piece, or a missing `.venv`.
- CI: shell lint, JS and Python syntax, JSON, `script.md` compile, Chrome lookup on Linux.
- Example piece: `motion/examples/hello`.
