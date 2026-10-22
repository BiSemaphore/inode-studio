"""Check what the narration actually says against the script, beat by beat.

  .venv/bin/python tools/verify_voice.py motion/<group>/<piece>

Cuts voice/voice.wav at each beat (voice/timings.json), transcribes the clip with
faster-whisper (no prompt, so mistakes are not hidden), and compares it with the beat's
"show" text. Writes voice/verify.txt; the first line is OK or FAIL. Tech terms (words with
capitals, digits or dots) that the transcript does not contain are listed for a listen:
they are often the words the voice gets wrong. The publish hook requires verify.txt to be
OK and newer than voice.wav.
"""
import difflib
import json
import pathlib
import re
import sys

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

piece = pathlib.Path(sys.argv[1])
beats = json.loads((piece / "beats.json").read_text())["beats"]
timings = json.loads((piece / "voice/timings.json").read_text())
timings = timings["beats"] if isinstance(timings, dict) else timings
x, sr = sf.read(str(piece / "voice/voice.wav"), dtype="float32")
if x.ndim > 1:
    x = x.mean(axis=1)
model = WhisperModel("small.en", device="cpu", compute_type="int8")
words = lambda s: re.sub(r"[^a-z0-9' ]", " ", s.lower()).split()

lines, worst = [], 1.0
for b, t in zip(beats, timings):
    seg = x[int(max(0, t["start"] - 0.1) * sr):int((t["end"] + 0.15) * sr)]
    seg16 = np.interp(np.arange(int(len(seg) * 16000 / sr)) / 16000, np.arange(len(seg)) / sr, seg).astype(np.float32)
    heard = " ".join(s.text.strip() for s in model.transcribe(seg16, beam_size=5)[0])
    ratio = difflib.SequenceMatcher(None, words(b["show"]), words(heard)).ratio()
    worst = min(worst, ratio)
    terms = [w.strip(".,:;!?") for w in b["show"].split() if re.search(r"[A-Z].*[A-Z]|\d|\w\.\w", w)]
    missing = [w for w in terms if w.lower().replace(".", "") not in heard.lower().replace(".", "")]
    flag = "ok  " if ratio >= 0.85 else "DIFF"
    lines.append(f"{flag} {ratio:.2f}  [{b['id']}]\n   script: {b['show']}\n   heard:  {heard}"
                 + (f"\n   listen: {', '.join(missing)}" if missing else ""))

status = "OK" if worst >= 0.85 else "FAIL"
report = f"{status} (lowest beat match {worst:.2f})\n" + "\n".join(lines) + "\n"
(piece / "voice/verify.txt").write_text(report)
print(report)
sys.exit(0 if status == "OK" else 1)
