"""Soundtrack for an explainer: narration, keys, pops, whooshes, music.

  .venv/bin/python explainer/mix.py motion/<piece>

Reads <piece>/sfx.json (written by story.py) and <piece>/voice/voice.wav,
writes <piece>/audio.wav, which tools/record.js muxes into the MP4.
Effects reuse tools/sound.py in its "mac" style, including the recorded Mac
keys (eklee, qubodup, CC BY 3.0: credit them in the post caption). Frames pieces also
get drawn sound (pen scratch, paper taps, headline swish, air on moves and cuts) and an
ambient bed kept in the range phone speakers play. The bed ducks under the voice.
"""

import json
import pathlib
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
_argv, sys.argv = sys.argv, ["sound.py", "-", "-", "mech"]   # mechanical key recordings (bank chosen at import)
import sound  # noqa: E402
sys.argv = _argv
SR = sound.SR
band = sound.band
rng = np.random.default_rng(11)


def pop():
    n = int(0.09 * SR)
    tt = np.arange(n) / SR
    f = 520 + 900 * tt / 0.09
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * sound.env_exp(n, 0.02)


def pen(dur):
    """Pen on paper for one stroke: grainy mid-high noise that follows the stroke length."""
    n = int((dur + 0.08) * SR)
    tt = np.arange(n) / SR
    grain = sound.smooth(np.abs(rng.standard_normal(n)), int(SR / 40)) * 2.2
    s = band(rng.standard_normal(n), 1800, 6500) * grain + 0.35 * band(rng.standard_normal(n), 400, 1400)
    att = np.minimum(1, tt / 0.03) * np.clip((dur + 0.08 - tt) / 0.08, 0, 1)
    return s * att * (0.8 + 0.2 * np.sin(2 * np.pi * 3.1 * tt))


def tap():
    """A sheet touching paper: soft, short, more body than click."""
    n = int(0.12 * SR)
    tt = np.arange(n) / SR
    return band(rng.standard_normal(n), 500, 2600) * sound.env_exp(n, 0.014) + 0.5 * np.sin(2 * np.pi * 190 * tt) * sound.env_exp(n, 0.03)


def swish():
    """A brush stroke for a headline: quick rise, slow fall, plus a soft low body."""
    n = int(0.5 * SR)
    tt = np.arange(n) / SR
    e = np.minimum(1, tt / 0.05) * np.exp(-tt / 0.14)
    return band(rng.standard_normal(n), 700, 4200) * e + 0.6 * np.pad(sound.thump(), (0, max(0, n - len(sound.thump()))))[:n]


def ambient(total):
    """Slow warm chords (8 s each) and faint air. Partials sit at 200 Hz to 3 kHz so a phone plays them."""
    n = int(total * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    chords = [[53, 60, 64, 67, 72], [50, 57, 62, 65, 69], [48, 55, 60, 64, 67], [46, 53, 58, 62, 65]]
    bar, k = 8.0, 0
    while k * bar < total:
        i0, j = int(k * bar * SR), min(n, int((k * bar + bar + 3.0) * SR))
        t = np.arange(j - i0) / SR
        a = np.minimum(1, t / 2.5) * np.clip((bar + 3.0 - t) / 3.0, 0, 1)
        for q, m in enumerate(chords[k % 4]):
            f = sound.NOTE(m)
            for det in (-0.08, 0.0, 0.08):
                ph = 2 * np.pi * f * 2 ** (det / 12) * t + 0.4 * np.sin(2 * np.pi * 0.2 * t + q)
                out[i0:j] += (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)) * a * (0.6 if q == 0 else 1.0)
        k += 1
    out = band(out, 180, 3200)
    air = band(rng.standard_normal(n), 300, 1500) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.06 * tt))
    out = out / (np.sqrt(np.mean(out ** 2)) + 1e-9) + 0.25 * air / (np.sqrt(np.mean(air ** 2)) + 1e-9)
    return out * np.minimum(1, tt / 1.5) * np.clip((total - tt) / 2.5, 0, 1)


# ---------- recorded sound library (assets/sfx) ----------
LIB = pathlib.Path(__file__).resolve().parent.parent / "assets" / "sfx"
_cache = {}


def sample(path):
    """Any audio file as mono float at SR, peak 1."""
    path = str(path)
    if path not in _cache:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype="<f4").astype(float)
        _cache[path] = x / (np.abs(x).max() + 1e-9)
    return _cache[path]


def pick(pattern):
    """A random file matching a glob under assets/sfx, or None."""
    files = sorted(f for f in LIB.glob(pattern) if f.suffix.lower() in (".ogg", ".wav", ".mp3", ".flac", ".m4a"))
    return sample(files[int(rng.integers(len(files)))]) if files else None


def stretch_take(x, dur):
    """A piece of a longer recording, dur seconds long, with short fades (for writing under a stroke)."""
    n = int(dur * SR)
    if len(x) <= n:
        y = np.tile(x, n // len(x) + 1)[:n]
    else:
        i = int(rng.integers(0, len(x) - n))
        y = x[i:i + n].copy()
    f = min(len(y) // 4, int(0.05 * SR))
    if f:
        y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def kit_effects(e, sfx):
    """Recorded sounds: owner downloads in incoming/ first, Kenney CC0 accents otherwise."""
    for t, d in e.get("draws", []):
        rec = pick("incoming/*write*") or pick("incoming/*pen*") or pick("incoming/*marker*")
        if rec is not None:
            sound.place(sfx, stretch_take(rec, d + 0.1), t, 0.10, rng.uniform(-0.15, 0.15))
        else:   # a soft pencil grain: short scratches along the stroke
            k = 0.0
            while k < d:
                sound.place(sfx, pick("kenney/interface-sounds/scratch_00[123].ogg"), t + k, 0.025, rng.uniform(-0.2, 0.2))
                k += rng.uniform(0.09, 0.14)
    for t in e.get("taps", []):
        sound.place(sfx, pick("kenney/interface-sounds/drop_00*.ogg"), t, 0.035, rng.uniform(-0.2, 0.2))
    for t in e.get("brushes", []):
        sound.place(sfx, pick("kenney/impact-sounds/impactSoft_medium_00*.ogg"), t - 0.02, 0.10, 0)
    for t, kind in e.get("zooms", []):
        rec = pick("incoming/*whoosh*")
        if rec is not None:
            sound.place(sfx, rec, t, 0.08, 0)
        else:
            sound.place(sfx, sound.whoosh(0.6), t, 0.02, 0)
            sound.place(sfx, pick(f"kenney/interface-sounds/{'maximize' if kind == 'in' else 'minimize'}_00[123].ogg"), t + 0.05, 0.03, 0)
    for t in e.get("checks", []):
        sound.place(sfx, pick("kenney/interface-sounds/confirmation_00[12].ogg"), t, 0.05, 0)
    for t, d in e.get("moves", []):
        sound.place(sfx, sound.whoosh(0.4 + 0.3 * min(d, 1.0)), t, 0.02, 0)
    for t in e.get("cuts", []):
        sound.place(sfx, sound.whoosh(0.8), t - 0.05, 0.018, 0)


def music_bed(total):
    """An owner-downloaded track from incoming/ (music*), trimmed with fades; None if there is none."""
    files = sorted(f for f in LIB.glob("incoming/*music*") if f.suffix.lower() in (".ogg", ".wav", ".mp3", ".flac", ".m4a"))
    if not files:
        return None
    x = sample(files[0]); n = int(total * SR)
    x = np.tile(x, n // len(x) + 1)[:n]
    tt = np.arange(n) / SR
    return x * np.minimum(1, tt / 1.5) * np.clip((total - tt) / 2.5, 0, 1)


def load_voice(path):
    with wave.open(str(path)) as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if sw == 2:
        x = np.frombuffer(raw, "<i2").astype(np.float64) / 32768
    else:  # soundfile writes 16-bit PCM by default; float as a fallback
        x = np.frombuffer(raw, "<f4").astype(np.float64)
    if ch == 2:
        x = x.reshape(-1, 2).mean(axis=1)
    t_in = np.arange(len(x)) / sr
    t_out = np.arange(int(len(x) * SR / sr)) / SR
    return np.interp(t_out, t_in, x)


def main(piece):
    piece = pathlib.Path(piece)
    e = json.loads((piece / "sfx.json").read_text())
    total = e["total"]
    n = int(total * SR)
    sfx = np.zeros((2, n))

    for t, kind in e["keys"]:
        # Quiet: clicks about 28 dB under the voice (measured from the stems).
        sound.place(sfx, sound.key_sound(kind), t, 0.055 if kind == "enter" else 0.045, rng.uniform(-0.1, 0.1))
    for t in e.get("clicks", []):
        # Mouse clicks for screen-recorded pieces; a touch above the keys so a UI click reads.
        sound.place(sfx, sound.mouse_sound(), t - 0.01, 0.07, rng.uniform(-0.1, 0.1))
    for t in e["ticks"]:
        sound.place(sfx, sound.beeps([(1568, 0.02)]), t, 0.012)
    for t in e["pops"]:
        sound.place(sfx, pop(), t, 0.06, rng.uniform(-0.2, 0.2))
    for t, mag in e["whooshes"]:
        sound.place(sfx, sound.whoosh(mag), t, 0.03, 0)
    for t in e["misses"]:
        sound.place(sfx, sound.beeps([(523, 0.09), (392, 0.22)], 0.04), t, 0.06)
    for t in e["hits"]:
        sound.place(sfx, sound.beeps([(1175, 0.05), (1568, 0.08)]), t, 0.045)
    for t in e.get("thumps", []):
        sound.place(sfx, sound.thump(), t, 0.22)
    if e.get("kit") == "recorded":
        kit_effects(e, sfx)
    else:
        for t, d in e.get("draws", []):
            sound.place(sfx, pen(d), t, 0.022, rng.uniform(-0.15, 0.15))
        for t in e.get("taps", []):
            sound.place(sfx, tap(), t, 0.05, rng.uniform(-0.2, 0.2))
        for t in e.get("brushes", []):
            sound.place(sfx, swish(), t - 0.03, 0.07, 0)
        for t, d in e.get("moves", []):
            sound.place(sfx, sound.whoosh(0.4 + 0.3 * min(d, 1.0)), t, 0.02, 0)
        for t in e.get("cuts", []):
            sound.place(sfx, sound.whoosh(0.8), t - 0.05, 0.018, 0)
    for t in e["chord"]:
        for d, m in enumerate((65, 69, 72, 76)):
            sound.place(sfx, sound.bell(sound.NOTE(m), 2.4), t + d * 0.09, 0.05, (d - 1.5) * 0.15)

    voice = load_voice(piece / "voice" / "voice.wav")[:n]
    vbuf = np.zeros(n)
    vbuf[: len(voice)] = voice
    # Duck the music by up to ~9 dB while the voice speaks.
    env = sound.smooth(np.abs(vbuf), int(0.25 * SR))
    env = np.clip(env / (env.max() + 1e-9) * 4, 0, 1)
    if e.get("bed") == "ambient":
        # about 20 dB under the voice while she speaks, about 14 dB in the gaps
        vr = np.sqrt(np.mean(vbuf[np.abs(vbuf) > 0.01] ** 2)) * 1.6
        bed = music_bed(total) if e.get("kit") == "recorded" else None
        bed = ambient(total) if bed is None else bed / (np.sqrt(np.mean(bed ** 2)) + 1e-9)
        mus = bed * vr * 10 ** (-14 / 20) * (1 - 0.5 * env)
    else:
        mus = sound.music(total) * 0.5 * (1 - 0.65 * env)

    mix = sound.space(sfx) + sound.space(np.vstack([mus, mus]) * np.array([[1.0], [0.97]]), ((0.23, 0.25), (0.37, 0.15)))
    mix += np.vstack([vbuf, vbuf]) * 1.6
    mix = np.tanh(mix * 1.2) / 1.2
    mix *= 0.89 / max(1e-9, np.abs(mix).max())
    pcm = (mix.T * 32767).astype("<i2")
    raw = str(piece / "audio.raw.wav")
    with wave.open(raw, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "ebur128", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    integrated = float(meas.rsplit("I:", 1)[1].split("LUFS")[0])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                    f"volume={-15.5 - integrated:.2f}dB,alimiter=limit=0.79:attack=2:release=60:level=disabled",
                    "-ar", str(SR), str(piece / "audio.wav")], check=True)
    pathlib.Path(raw).unlink()
    print(f"{piece / 'audio.wav'}: {total:.2f}s, {len(e['keys'])} keys, "
          f"{len(e['pops'])} pops, {len(e['whooshes'])} camera moves")


if __name__ == "__main__":
    main(*sys.argv[1:])
