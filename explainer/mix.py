"""Soundtrack for an explainer: narration, keys, pops, whooshes, music.

  .venv/bin/python explainer/mix.py motion/<piece>

Reads <piece>/sfx.json (written by story.py) and <piece>/voice/voice.wav,
writes <piece>/audio.wav, which tools/record.js muxes into the MP4.
Effects reuse tools/sound.py in its "mac" style, including the recorded Mac
keys (eklee, qubodup, CC BY 3.0: credit them in the post caption). Drawing
makes no sound (house rule). The music bed ducks under the voice.
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
rng = np.random.default_rng(11)


def pop():
    n = int(0.09 * SR)
    tt = np.arange(n) / SR
    f = 520 + 900 * tt / 0.09
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * sound.env_exp(n, 0.02)


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
    for t in e["chord"]:
        for d, m in enumerate((65, 69, 72, 76)):
            sound.place(sfx, sound.bell(sound.NOTE(m), 2.4), t + d * 0.09, 0.05, (d - 1.5) * 0.15)

    voice = load_voice(piece / "voice" / "voice.wav")[:n]
    vbuf = np.zeros(n)
    vbuf[: len(voice)] = voice
    # Duck the music by up to ~9 dB while the voice speaks.
    env = sound.smooth(np.abs(vbuf), int(0.25 * SR))
    env = np.clip(env / (env.max() + 1e-9) * 4, 0, 1)
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
