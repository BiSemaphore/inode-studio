"""Narration for an explainer: one Kokoro clip per beat, joined with pauses.

Run with the repo's environment (.venv, Python 3.12, from scripts/setup.sh):
  .venv/bin/python explainer/voice.py <beats.json> <outdir>

beats.json: {"voice": "af_heart", "speed": 1.0, "lead": 1.0,
             "beats": [{"say": "...", "pause": 0.45}, ...]}
Writes <outdir>/voice.wav (24 kHz mono) and <outdir>/timings.json with the
start and end of every beat in seconds, and the start and end of every word
of the beat's "show" text (the caption), for word-by-word subtitles.

Word times come from forced alignment of the spoken text ("say") to each clip
(torchaudio MMS_FA), then the spoken words are matched to the caption words
("show"), so "seven hundred and sixty-eight" gives the time span of the
caption word "768". (Earlier versions transcribed with faster-whisper, which
sometimes dropped or repeated sentences.) Clips and word times are cached by text,
voice and speed in <outdir>/clips/, so editing one line redoes only that line.
"""

import difflib
import hashlib
import json
import re
import pathlib
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

TTS = pathlib.Path(__file__).resolve().parent.parent / "tts"


def trim(x, sr, thresh=0.01, pad=0.04):
    """Cut leading and trailing silence, keeping a short pad."""
    idx = np.where(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(x), idx[-1] + int(pad * sr))
    return x[a:b]


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def spread(times, i1, i2, n):
    """n equal slices of the time span covered by spoken words i1..i2."""
    a, b = times[i1][0], times[i2 - 1][1]
    return [(a + (b - a) * k / n, a + (b - a) * (k + 1) / n) for k in range(n)]


def align(src, ref_times, dst):
    """Times for the words of dst, given times for the words of src."""
    sm = difflib.SequenceMatcher(None, [norm(w) for w in src], [norm(w) for w in dst], autojunk=False)
    out = [None] * len(dst)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(j2 - j1):
                out[j1 + k] = ref_times[i1 + k]
        elif op == "replace" or (op == "insert" and i1 > 0):
            lo, hi = (i1, i2) if op == "replace" else (i1 - 1, i1)
            for k, t in enumerate(spread(ref_times, lo, hi, j2 - j1)):
                out[j1 + k] = t
    # Anything still missing (inserted at the very start) borrows its neighbour.
    for k in range(len(out)):
        if out[k] is None:
            nxt = next((t for t in out[k:] if t), (0, 0))
            out[k] = (nxt[0], nxt[0])
    return out


_fa = None


def forced_align(path, say):
    """[[word, start, end]] for every word of `say`, by forced alignment of
    the known text to the audio (torchaudio MMS_FA, a wav2vec2 CTC model).
    Unlike transcription it cannot drop, repeat or mishear words: it only
    finds where each given word is."""
    global _fa
    import torch
    import torchaudio
    if _fa is None:
        b = torchaudio.pipelines.MMS_FA
        _fa = (b, b.get_model(with_star=False), b.get_tokenizer(), b.get_aligner())
    bundle, model, tokenizer, aligner = _fa
    x, sr = sf.read(path, dtype="float32")
    sr16 = bundle.sample_rate
    x16 = np.interp(np.arange(int(len(x) * sr16 / sr)) / sr16, np.arange(len(x)) / sr, x).astype(np.float32)
    wave = torch.from_numpy(x16).unsqueeze(0)
    said = say.split()
    # Each spoken word becomes one or more alignable tokens (letters only):
    # "eye-node," -> ["eye", "node"]; the word spans from its first to last.
    pieces = [[p for p in re.split(r"[^a-z']+", w.lower()) if p] for w in said]
    flat = [p for ps in pieces for p in ps]
    with torch.inference_mode():
        emission, _ = model(wave)
        spans = aligner(emission[0], tokenizer(flat))
    ratio = wave.size(1) / emission.size(1) / sr16
    times, k = [], 0
    for w, ps in zip(said, pieces):
        if not ps:                                   # a word with no letters ("3", "-"): borrow a neighbour
            times.append(None)
            continue
        first, last = spans[k], spans[k + len(ps) - 1]
        times.append([w, round(first[0].start * ratio, 3), round(last[-1].end * ratio, 3)])
        k += len(ps)
    for i, t in enumerate(times):
        if t is None:
            prev = next((times[j] for j in range(i - 1, -1, -1) if times[j]), None)
            nxt = next((times[j] for j in range(i + 1, len(times)) if times[j]), None)
            a = prev[2] if prev else (nxt[1] if nxt else 0.0)
            b = nxt[1] if nxt else a
            times[i] = [said[i], a, b]
    return times


def word_times(path, say, show, dur):
    """[(word, start, end)] for the caption words of one clip, cached."""
    cache = path.with_suffix(".fa.json")
    if cache.exists():
        heard = json.loads(cache.read_text())
    else:
        heard = forced_align(path, say)
        cache.write_text(json.dumps(heard))
    said = say.split()
    if heard:
        t_said = align([h[0] for h in heard], [(h[1], h[2]) for h in heard], said)
    else:
        t_said = [(dur * k / len(said), dur * (k + 1) / len(said)) for k in range(len(said))]
    words = show.split()
    return [(w, max(0.0, a), min(dur, b)) for w, (a, b) in zip(words, align(said, t_said, words))]


MARK = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]")
PLACEHOLDERS = ["Zorblat", "Quenzar", "Vexmorin", "Taldrupe", "Brennix", "Gulvaro"]


def plain(say):
    """Spoken text without phoneme markers (for alignment and captions)."""
    return MARK.sub(lambda m: m.group(1), say)


def phonemes_for(kokoro, say):
    """Phonemes for `say` with [[word|phonemes]] markers spoken exactly as given.
    Each marker is swapped for a nonsense placeholder word, the sentence is
    phonemized as usual (keeping its rhythm and punctuation), and the
    placeholder's phonemes are replaced by the given ones."""
    marks = MARK.findall(say)
    text, i = say, 0
    for k, (word, ph) in enumerate(marks):
        text = text.replace(f"[[{word}|{ph}]]", PLACEHOLDERS[k], 1)
    out = kokoro.tokenizer.phonemize(text, "en-us")
    for k, (word, ph) in enumerate(marks):
        pp = kokoro.tokenizer.phonemize(PLACEHOLDERS[k], "en-us").strip()
        if pp not in out:
            raise SystemExit(f"could not place phonemes for {word!r} in {say!r}")
        out = out.replace(pp, ph, 1)
    return out


def main(beats_path, outdir):
    spec = json.loads(pathlib.Path(beats_path).read_text())
    out = pathlib.Path(outdir)
    clips = out / "clips"
    clips.mkdir(parents=True, exist_ok=True)
    voice, speed = spec.get("voice", "af_heart"), spec.get("speed", 1.0)
    kokoro = None
    sr = 24000

    audio = [np.zeros(int(spec.get("lead", 1.0) * sr), dtype=np.float32)]
    t = spec.get("lead", 1.0)
    timings = []
    for beat in spec["beats"]:
        key = hashlib.sha1(f"{voice}|{speed}|{beat['say']}".encode()).hexdigest()[:16]
        path = clips / f"{key}.wav"
        if path.exists():
            x, sr = sf.read(path, dtype="float32")
        else:
            kokoro = kokoro or Kokoro(str(TTS / "kokoro-v1.0.onnx"), str(TTS / "voices-v1.0.bin"))
            if MARK.search(beat["say"]):
                x, sr = kokoro.create(phonemes_for(kokoro, beat["say"]), voice=voice, speed=speed, lang="en-us", is_phonemes=True)
            else:
                x, sr = kokoro.create(beat["say"], voice=voice, speed=speed, lang="en-us")
            x = trim(np.asarray(x, dtype=np.float32), sr)
            sf.write(path, x, sr)
        d = len(x) / sr
        words = word_times(path, plain(beat["say"]), beat.get("show", plain(beat["say"])), d)
        timings.append({"start": round(t, 3), "end": round(t + d, 3),
                        "words": [[w, round(t + a, 3), round(t + b, 3)] for w, a, b in words]})
        audio.append(x)
        pause = beat.get("pause", 0.45)
        audio.append(np.zeros(int(pause * sr), dtype=np.float32))
        t += d + pause

    sf.write(out / "voice.wav", np.concatenate(audio), sr)
    (out / "timings.json").write_text(json.dumps(timings, indent=1))
    print(f"{len(timings)} beats, {t:.2f}s of narration -> {out / 'voice.wav'}")


if __name__ == "__main__":
    main(*sys.argv[1:])
