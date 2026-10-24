"""Check what the narration actually says against the script, beat by beat.

  .venv/bin/python tools/verify_voice.py motion/<group>/<piece>

Cuts voice/voice.wav at each beat (voice/timings.json), transcribes the clip with
faster-whisper (no prompt, so mistakes are not hidden), and compares it with the beat's
"show" text. Writes voice/verify.txt; the first line is OK or FAIL. Tech terms (words with
capitals, digits or dots) that the transcript does not contain are listed for a listen:
they are often the words the voice gets wrong. The publish hook requires verify.txt to be
OK and newer than voice.wav.

Spelled-out words ("S-T-R" for the token "str", said on purpose with letter phonemes) are joined
back into one word before comparing. A beat under 0.85 gets a second opinion from
medium.en (small.en often keeps "spelling" after a spelled word: "berry" became "B-R-E"); the
better match counts and the report names the model. Every word given exact phonemes in "say"
([[word|...]]) must be heard as that word by one of the two models, or the beat fails.
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
second = None


def words(s):
    """Lower-case words; letters joined by hyphens (S-T-R) become one word (str)."""
    s = re.sub(r"\b[A-Za-z](?:-[A-Za-z])+\b", lambda m: m.group(0).replace("-", ""), s)
    return re.sub(r"[^a-z0-9' ]", " ", s.lower().replace("-", " ")).split()


def hear(m, seg16):
    return " ".join(s.text.strip() for s in m.transcribe(seg16, beam_size=5)[0])


lines, worst = [], 1.0
for b, t in zip(beats, timings):
    seg = x[int(max(0, t["start"] - 0.1) * sr):int((t["end"] + 0.15) * sr)]
    seg16 = np.interp(np.arange(int(len(seg) * 16000 / sr)) / 16000, np.arange(len(seg)) / sr, seg).astype(np.float32)
    heard, by = hear(model, seg16), ""
    ratio = difflib.SequenceMatcher(None, words(b["show"]), words(heard)).ratio()
    # every word given exact phonemes ([[word|...]]) must be heard as that word, or the beat fails: a whole
    # sentence can score high while its one tech term is wrong ("embedding" was heard as "Emma bedding")
    marked = [m.lower() for m in re.findall(r"\[\[([^|\]]+)\|", b.get("say", ""))]
    unheard = lambda h: [m for m in marked if not set(words(m)) <= set(words(h))]
    if ratio < 0.85 or unheard(heard):
        second = second or WhisperModel("medium.en", device="cpu", compute_type="int8")
        h2 = hear(second, seg16)
        r2 = difflib.SequenceMatcher(None, words(b["show"]), words(h2)).ratio()
        if (len(unheard(h2)), -r2) < (len(unheard(heard)), -ratio):
            heard, ratio, by = h2, r2, " (medium.en)"
    if unheard(heard):
        ratio = min(ratio, 0.0)                                   # a misheard tech term fails the beat
    worst = min(worst, ratio)
    terms = [w.strip(".,:;!?") for w in b["show"].split() if re.search(r"[A-Z].*[A-Z]|\d|\w\.\w", w)]
    missing = [w for w in terms if w.lower().replace(".", "") not in heard.lower().replace(".", "")]
    flag = "ok  " if ratio >= 0.85 else "DIFF"
    lines.append(f"{flag} {ratio:.2f}  [{b['id']}]{by}" + (f"  NOT HEARD: {', '.join(unheard(heard))}" if unheard(heard) else "") + "\n   script: {b['show']}\n   heard:  {heard}"
                 + (f"\n   listen: {', '.join(missing)}" if missing else ""))

status = "OK" if worst >= 0.85 else "FAIL"
report = f"{status} (lowest beat match {worst:.2f})\n" + "\n".join(lines) + "\n"
(piece / "voice/verify.txt").write_text(report)
print(report)
sys.exit(0 if status == "OK" else 1)
