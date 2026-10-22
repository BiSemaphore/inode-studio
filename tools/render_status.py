"""Show every frames render in progress: percent, frames, time left, expected finish.

  .venv/bin/python tools/render_status.py
"""
import json
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
found = False
for p in sorted(ROOT.glob("motion/*/*/out/render-progress.json")):
    d = json.loads(p.read_text())
    age = time.time() - p.stat().st_mtime
    if d["state"] == "done" and age > 600:
        continue
    found = True
    left = f"{d['eta_s'] // 60} min {d['eta_s'] % 60} s left, done about {d['finish_at']}" if d.get("eta_s") is not None else "starting"
    stale = "  (no update for %d s: stopped?)" % age if d["state"] == "rendering" and age > 120 else ""
    print(f"{d['piece']}: {d['state']} {d['pct']}% ({d['frame']}/{d['frames']} frames), {left}{stale}")
if not found:
    print("no render in progress")
