"""After-render checks for an explainer: loudness, peaks, durations, SRT.

  .venv/bin/python explainer/qa.py motion/<piece>        (exit 1 on problems)

Broken frames are checked by tools/record.js while rendering; layout, timeline
and sync are checked before rendering (explainer/check.sh).
"""
import json
import pathlib
import re
import subprocess
import sys

piece = pathlib.Path(sys.argv[1])
name = piece.name
mp4 = piece / "out" / f"{name}.mp4"
problems, notes = [], []


def probe(stream):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries", "stream=duration",
                          "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout.strip()
    return float(out or 0)


v, a = probe("v:0"), probe("a:0")
notes.append(f"video {v:.2f}s, audio {a:.2f}s")
if abs(v - a) > 0.1:
    problems.append(f"video and audio lengths differ by {abs(v - a):.2f}s")

# Loudness: social platforms play around -14 to -16 LUFS; keep true peak under -1 dBTP.
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp4), "-af", "ebur128=peak=true", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", m)[-1])
peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", m)[-1])
notes.append(f"loudness {lufs:.1f} LUFS, true peak {peak:.1f} dBTP")
if not -17.0 <= lufs <= -14.0:
    problems.append(f"loudness {lufs:.1f} LUFS outside -17..-14")
if peak > -1.0:
    problems.append(f"true peak {peak:.1f} dBTP above -1")

# SRT: numbered, ordered, non-overlapping, inside the video.
srt = piece / f"{name}.srt"
if not srt.exists():
    problems.append("no SRT file")
else:
    def secs(t):
        h, m_, rest = t.split(":")
        s, ms = rest.split(",")
        return int(h) * 3600 + int(m_) * 60 + int(s) + int(ms) / 1000
    cues = re.findall(r"(\d+)\n(\S+) --> (\S+)\n(.+?)\n(?:\n|$)", srt.read_text(), re.S)
    prev = 0.0
    for n, (k, s0, s1, text) in enumerate(cues, 1):
        a0, a1 = secs(s0), secs(s1)
        if int(k) != n or a0 >= a1 or a0 < prev - 1e-3 or a1 > v + 0.05 or not text.strip():
            problems.append(f"SRT cue {k} invalid ({s0} --> {s1})")
        prev = a1
    notes.append(f"SRT {len(cues)} cues")

for n in notes:
    print("  " + n)
for p in problems:
    print("  PROBLEM: " + p)
print(f"qa: {len(problems)} problem(s)")
sys.exit(1 if problems else 0)
