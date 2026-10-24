"""Fail if a rendered video has broken frames.

  .venv/bin/python tools/check_video.py <video.mp4> [--json]

A broken frame differs from both neighbours while the neighbours agree with
each other (something blinked out for one frame), or went black while both
neighbours did not. Timing is checked too: the frame rate must be a steady 30 and
the picture and the sound must end within one frame of each other (a blurred render
once drifted 0.6 s because each joined chunk was 1/60 s short). Camera
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
probe = lambda sel, key: subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", f"stream={key}",
                                         "-of", "default=nw=1:nk=1", path], capture_output=True, text=True).stdout.split()
rate, vdur, adur = probe("v:0", "r_frame_rate"), probe("v:0", "duration"), probe("a:0", "duration")
timing = []
if rate and rate[0] != "30/1":
    timing.append(f"frame rate {rate[0]}, not a steady 30/1")
if vdur and adur and abs(float(vdur[0]) - float(adur[0])) > 1 / 30 + 0.03:   # aac pads its last packet by up to ~21 ms
    timing.append(f"picture {float(vdur[0]):.3f} s but sound {float(adur[0]):.3f} s")
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
print(f"{path}: {len(f)} frames, {len(bad)} broken" + (f", TIMING: {'; '.join(timing)}" if timing else ""))
for i, kind in bad:
    print(f"  frame {i} ({i / 30:.2f}s): {kind}")
sys.exit(1 if bad or timing else 0)
