"""Fail if a rendered video has broken frames.

  .venv/bin/python tools/check_video.py <video.mp4> [--json]

A broken frame differs from both neighbours while the neighbours agree with
each other (something blinked out for one frame), or went black while both
neighbours did not. Camera
moves and normal drawing change frames smoothly and are not flagged.
"""
import subprocess
import sys

import numpy as np

path = sys.argv[1]
as_json = "--json" in sys.argv
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "scale=320:180,format=gray", "-f", "rawvideo", "-"],
                     capture_output=True, check=True).stdout
f = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 180, 320).astype(np.int16)
bad = []
for i in range(len(f)):
    # "black": a frame that dropped to black while its neighbours did not.
    # (Absolute darkness is not a fault: dark films are mostly dark.)
    m = f[i].mean()
    if 0 < i < len(f) - 1 and m < 8 and f[i - 1].mean() > 25 and f[i + 1].mean() > 25:
        bad.append((i, "black"))
    elif 0 < i < len(f) - 1:
        a, b = np.abs(f[i] - f[i - 1]).mean(), np.abs(f[i] - f[i + 1]).mean()
        c = np.abs(f[i - 1] - f[i + 1]).mean()
        if a > 0.8 and b > 0.8 and c < 0.35 * min(a, b):
            bad.append((i, "blink"))
if as_json:
    import json
    print(json.dumps({"frames": len(f), "broken": [i for i, _ in bad]}))
    sys.exit(0)
print(f"{path}: {len(f)} frames, {len(bad)} broken")
for i, kind in bad:
    print(f"  frame {i} ({i / 30:.2f}s): {kind}")
sys.exit(1 if bad else 0)
