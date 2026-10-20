"""Synthesize a soundtrack for a motion piece from its events.json.

Key presses and mouse clicks use real recordings when audio/keypresses-eklee
is present (CC BY 3.0, eklee and qubodup: the video must credit them); otherwise
they are synthesized. Everything else is generated here: robotic UI beeps
(command accepted, output blips, spinner "computing" chatter, found / not found /
audit / login ok, agent send and receive), whooshes on camera moves, a logo sting,
and a quiet music bed (pad + plucked arpeggio + sub) that fades in and out.

Style "mac" (third argument) is the smooth, headphone-friendly mix: MacBook-like
keys (short, soft taps from the Mac recordings, top end rolled off), sine beeps
instead of square, sparse quiet chatter, softer whooshes, keys centred.

Usage: .venv/bin/python tools/sound.py motion/<piece>/events.json motion/<piece>/audio.wav [mech|mac]
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

SR = 48000
rng = np.random.default_rng(7)
MAC = len(sys.argv) > 3 and sys.argv[3] == "mac"


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def place(buf, sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= buf.shape[1]:
        return
    j = min(buf.shape[1], i + len(sig))
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    buf[0, i:j] += sig[: j - i] * gain * l
    buf[1, i:j] += sig[: j - i] * gain * r


def smooth(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def band(x, lo, hi):
    """Band-pass by FFT with soft (raised-cosine) skirts, so nothing leaks above `hi`."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.clip((f - lo * 0.5) / (lo * 0.5), 0, 1) * np.clip((hi * 1.5 - f) / (hi * 0.5), 0, 1)
    return np.fft.irfft(X * (0.5 - 0.5 * np.cos(np.pi * m)), len(x))


# ---------- sound effects ----------

def key_click(kind):
    n = int(0.06 * SR)
    noise = rng.standard_normal(n)
    hi = band(noise, 1800, 5500) * env_exp(n, 0.0025)              # plastic contact
    mid = band(noise, 350, 1800) * env_exp(n, 0.006)               # key body
    f = {"key": rng.uniform(190, 260), "space": rng.uniform(120, 150), "enter": 150}[kind]
    tt = np.arange(n) / SR
    thock = np.sin(2 * np.pi * f * tt) * env_exp(n, 0.012 if kind == "key" else 0.02)
    s = 2.2 * hi + 1.6 * mid + 0.55 * thock
    if kind == "enter":
        s = s * 1.5
    return s * rng.uniform(0.75, 1.0)


# ---------- recorded keyboard (eklee, qubodup, CC BY 3.0) ----------

SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio", "keypresses-eklee", "flac48000")


def load(name, max_len=0.32):
    """Load a sample, trim to the attack (onset - 1.5 ms), cap the tail with a short fade."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(SAMPLES, name), "-f", "f32le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    on = max(0, int(np.argmax(np.abs(x) > 0.15 * np.abs(x).max())) - int(0.0015 * SR))
    x = x[on:on + int(max_len * SR)]
    fade = int(0.04 * SR)
    x[-fade:] *= np.linspace(1, 0, fade)
    return x / np.abs(x).max()


def tame(x, cut=3000, air=0.12):
    """MacBook-style smoothing: keep the low-mid 'tok', keep only a trace of the high 'tick',
    and round the first millisecond so the attack is soft rather than a sharp click."""
    low = band(x, 40, cut)
    y = low + air * (x - low)
    k = int(0.0012 * SR)
    y[:k] *= np.sin(np.linspace(0, np.pi / 2, k)) ** 2
    return y


BANK = None
if os.path.isdir(SAMPLES) and MAC:
    BANK = {"key": [tame(load(f"eklee-KeyPressMac0{i}.flac", 0.12)) for i in (1, 2, 3, 5, 6)],
            "heavy": [tame(load("eklee-KeyPressMac02.flac", 0.14), 2600, 0.2)],
            "mouse": [tame(load("eklee-KeyPressMac04.flac", 0.1), 2800, 0.25)]}
    for k in BANK:
        BANK[k] = [x / np.abs(x).max() for x in BANK[k]]
elif os.path.isdir(SAMPLES):
    BANK = {"key": [load(f"eklee-KeyPressOld0{i}.flac") for i in (1, 2, 3, 4, 5)],
            "heavy": [load("eklee-KeyPressOld06.flac", 0.4)],
            "mouse": [load(f"eklee-KeyPressMac0{i}.flac", 0.16) for i in (4, 6)]}


def repitch(x, ratio):
    """Resample by `ratio` (>1 = higher and shorter)."""
    idx = np.arange(0, len(x) - 1, ratio)
    return np.interp(idx, np.arange(len(x)), x)


def key_sound(kind):
    if BANK is None:
        return key_click(kind)
    if kind == "enter":
        return repitch(BANK["heavy"][0], 0.9 if MAC else 0.94) * (1.1 if MAC else 1.25)
    x = BANK["key"][int(rng.integers(len(BANK["key"])))]
    if kind == "space":
        return repitch(x, rng.uniform(0.84, 0.9)) * 1.1          # longer, deeper stabiliser thud
    return repitch(x, rng.uniform(0.96, 1.05)) * rng.uniform(0.8, 1.0)


def mouse_sound():
    if BANK is None:
        return mouse_click()
    x = BANK["mouse"][int(rng.integers(len(BANK["mouse"])))]
    up = repitch(x, 1.15) * 0.55
    out = np.zeros(len(x) + int(0.08 * SR))
    out[:len(x)] += x
    out[int(0.075 * SR):int(0.075 * SR) + len(up)] += up            # press, then the lighter release
    return out


# ---------- robotic UI beeps ----------

def square(freq, dur, top=7000):
    """Band-limited square wave (odd harmonics up to `top`), 3 ms attack, quick release.
    In the mac style this is a soft sine beep instead (gentle on headphones)."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    if MAC:
        s = np.sin(2 * np.pi * freq * tt) + 0.12 * np.sin(2 * np.pi * 2 * freq * tt)
        a = np.minimum(1, np.arange(n) / (0.006 * SR)) * np.exp(-np.arange(n) / (0.6 * n)) \
            * np.minimum(1, (n - np.arange(n)) / (0.015 * SR))
        return s * a * 0.9
    s = np.zeros(n)
    h = 1
    while h * freq < top:
        s += np.sin(2 * np.pi * h * freq * tt) / h
        h += 2
    a = np.minimum(1, np.arange(n) / (0.003 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.012 * SR))
    return s * a * 0.8


def beeps(notes, gap=0.03):
    """Concatenate (freq, dur) beeps with small gaps: beep-beep, beep-boop."""
    parts = []
    for f, d in notes:
        parts += [square(f, d), np.zeros(int(gap * SR))]
    return np.concatenate(parts)


def chirp(f0, f1, dur):
    n = int(dur * SR)
    f = np.geomspace(f0, f1, n)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) if MAC else np.sign(np.sin(ph)) * 0.5 + np.sin(ph) * 0.5
    s = band(s, 200, 4000 if MAC else 6000)
    a = np.minimum(1, np.arange(n) / (0.004 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.02 * SR))
    return s * a


def chatter(dur):
    """Computer 'thinking': short random beeps from a pentatonic set, irregular spacing."""
    n = int(dur * SR)
    out = np.zeros(n)
    scale = [784, 880, 1047, 1175, 1319, 1568, 1760, 2093]
    t = 0.0
    while t < dur - 0.04:
        b = square(scale[int(rng.integers(len(scale)))], rng.uniform(0.018, 0.034))
        i = int(t * SR)
        j = min(n, i + len(b))
        out[i:j] += b[: j - i] * rng.uniform(0.6, 1.0)
        t += rng.uniform(0.09, 0.17) if MAC else rng.uniform(0.045, 0.1)
    return out


def tick():
    n = int(0.03 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 2300 * tt) * env_exp(n, 0.006)


def mouse_click():
    n = int(0.11 * SR)
    s = np.zeros(n)
    for off, g in ((0, 1.0), (int(0.075 * SR), 0.6)):
        m = int(0.02 * SR)
        noise = rng.standard_normal(m)
        tt = np.arange(m) / SR
        c = band(noise, 1500, 6000) * env_exp(m, 0.0015) * 1.6 + np.sin(2 * np.pi * 1400 * tt) * env_exp(m, 0.003)
        s[off:off + m] += c * g
    return s


def whoosh(mag):
    d = 0.45 + 0.25 * min(mag, 1.2)
    n = int(d * SR)
    noise = rng.standard_normal(n)
    a = band(noise, 250, 2600) * 2.5                                # air, no hiss
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    return a * e * (0.6 + 0.4 * min(mag, 1.2))


def bell(freq, dur=1.2, bright=0.35):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * freq * tt) + bright * np.sin(2 * np.pi * freq * 2.01 * tt) * env_exp(n, 0.15)
         + 0.12 * np.sin(2 * np.pi * freq * 3.0 * tt) * env_exp(n, 0.08))
    att = np.minimum(1, np.arange(n) / (0.004 * SR))
    return s * env_exp(n, dur / 3.5) * att


def soft(freq, dur=0.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(2 * np.pi * freq * 2 * tt)
    att = np.minimum(1, np.arange(n) / (0.01 * SR))
    return s * env_exp(n, dur / 3) * att


def thump():
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    f = 110 * np.exp(-tt * 9) + 48
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.09)


NOTE = lambda m: 440.0 * 2 ** ((m - 69) / 12)


# ---------- music bed ----------

def music(total):
    n = int(total * SR)
    out = np.zeros(n)
    tt_all = np.arange(n) / SR
    # Fmaj9 - Am7 - Cmaj7 - G6sus, 4 s each (60 bpm feel, calm)
    chords = [[53, 57, 60, 64, 67], [45, 52, 55, 60, 64], [48, 55, 59, 62, 64], [43, 50, 55, 57, 62]]
    bar = 4.0
    k = 0
    while k * bar < total:
        ch = chords[k % 4]
        t0 = k * bar
        seg = int((bar + 2.0) * SR)
        i0 = int(t0 * SR)
        j = min(n, i0 + seg)
        tt = np.arange(j - i0) / SR
        a = np.minimum(1, tt / 1.2) * np.clip((bar + 2.0 - tt) / 2.0, 0, 1)
        pad = np.zeros(j - i0)
        for m in ch[1:]:
            f = NOTE(m)
            for det in (-0.12, 0.0, 0.12):
                ff = f * 2 ** (det / 12)
                pad += (np.sin(2 * np.pi * ff * tt) + 0.25 * np.sin(2 * np.pi * 2 * ff * tt) + 0.08 * np.sin(2 * np.pi * 3 * ff * tt))
        out[i0:j] += pad * a * 0.022
        sub = np.sin(2 * np.pi * NOTE(ch[0] - 12) * tt) * a
        out[i0:j] += sub * 0.05
        # plucked arpeggio, eighth notes at 120 bpm, from the chord's upper tones
        pattern = [ch[2] + 12, ch[3] + 12, ch[4] + 12, ch[3] + 12, ch[1] + 12, ch[3] + 12, ch[4] + 12, ch[2] + 24]
        for b in range(8):
            ts = t0 + b * 0.5
            if ts >= total:
                break
            p = soft(NOTE(pattern[b]), 0.6) * (0.5 if b % 2 else 0.7)
            ii = int(ts * SR)
            jj = min(n, ii + len(p))
            out[ii:jj] += p[: jj - ii] * 0.03
        k += 1
    trem = 1 + 0.06 * np.sin(2 * np.pi * 0.25 * tt_all)
    out *= trem
    fade = np.minimum(1, tt_all / 2.0) * np.clip((total - tt_all) / 3.0, 0, 1)
    return out * fade


def space(x, taps=((0.11, 0.32), (0.19, 0.22), (0.29, 0.15), (0.43, 0.09))):
    y = x.copy()
    for d, g in taps:
        k = int(d * SR)
        y[:, k:] += x[:, :-k] * g
    return y


def main(events_path, out_path, style="mech"):
    e = json.load(open(events_path))
    total = e["total"] + 0.2
    n = int(total * SR)
    sfx = np.zeros((2, n))

    for t, kind in e["keys"]:
        # recordings already have human variance; no timing jitter so every press lands on its frame
        pan = rng.uniform(-0.05, 0.05) if MAC else rng.uniform(-0.2, 0.2)
        place(sfx, key_sound(kind), t, (0.26 if kind == "enter" else 0.2) if MAC else (0.3 if kind == "enter" else 0.24), pan)
        if kind == "enter":
            place(sfx, beeps([(1319, 0.035)]), t + 0.07, 0.05, 0.1)        # command accepted
    lines = sorted(e["ticks"])
    for k, t in enumerate(lines):
        run = 0
        while k - run - 1 >= 0 and t - lines[k - run - 1] < 0.12 * (run + 1) + 0.01:
            run += 1
        place(sfx, square(1568 * 2 ** (min(run, 5) * 2 / 12), 0.022), t, 0.035)   # output blips, rising in a burst
    for t, d in e.get("spins", []):
        place(sfx, chatter(d), t, 0.022 if MAC else 0.03, rng.uniform(-0.15, 0.15))
    for t in e.get("oks", []):
        place(sfx, beeps([(1175, 0.06), (1568, 0.09)]), t, 0.06)
    for t in e.get("tx", []):
        place(sfx, chirp(600, 1900, 0.16), t, 0.05, -0.2)
    for t in e.get("rx", []):
        place(sfx, chirp(1900, 800, 0.14), t, 0.05, 0.2)
        place(sfx, beeps([(1319, 0.03), (1319, 0.03)]), t + 0.17, 0.04, 0.2)
    for t in e.get("pops", []):
        place(sfx, beeps([(988, 0.04), (1480, 0.07)], 0.02), t, 0.045)        # window opens
        place(sfx, whoosh(0.4), t - 0.05, 0.025, 0)
    for t in e.get("flips", []):
        place(sfx, beeps([(1760, 0.025)]), t, 0.035, 0.3)                       # clock flips
    for t in e["clicks"]:
        place(sfx, mouse_sound(), t - 0.01, 0.26, 0.15)
    for t, mag in e["whooshes"]:
        place(sfx, whoosh(mag), t, 0.032 if MAC else 0.05, 0)
    for t in e["hits"]:
        place(sfx, beeps([(880, 0.07), (1319, 0.12)], 0.035), t, 0.07)            # beep-boop: found it
        place(sfx, bell(NOTE(83), 1.4), t + 0.2, 0.035, 0.1)
    for t in e["misses"]:
        place(sfx, beeps([(523, 0.09), (392, 0.22)], 0.04), t, 0.075)             # bee-bowww: nothing
    for t in e["audits"]:
        place(sfx, beeps([(1760, 0.05), (1760, 0.05), (1760, 0.05)], 0.045), t, 0.05)   # alert: logged
    # brand sting: thump + arpeggiated bell chord on the logo, a lift on the title
    i0, i1 = e["intro"]
    place(sfx, thump(), i0, 0.35)
    for d, m in enumerate((72, 76, 79, 84)):
        place(sfx, bell(NOTE(m), 1.8), i0 + 0.08 + d * 0.07, 0.06, (d - 1.5) * 0.15)
    place(sfx, bell(NOTE(88), 1.6, 0.2), i1, 0.04)
    # end card: resolve
    for d, m in enumerate((65, 69, 72, 76)):
        place(sfx, bell(NOTE(m), 2.4), e["end"] + d * 0.09, 0.055, (d - 1.5) * 0.15)

    mus = music(total) * 0.42                                       # bed sits about 7 dB under the effects
    mix = space(sfx) + space(np.vstack([mus, mus]) * np.array([[1.0], [0.97]]), ((0.23, 0.25), (0.37, 0.15)))
    mix = np.tanh(mix * 1.4) / 1.4                                  # soft limiter
    mix *= 0.89 / max(1e-9, np.abs(mix).max())                      # peak at about -1 dBFS
    pcm = (mix.T * 32767).astype("<i2")
    raw = out_path + ".raw.wav"
    with wave.open(raw, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    # Social platforms play around -14 to -16 LUFS; normalise loudness with a true-peak ceiling.
    # One fixed gain (keeps the mix balance) plus a peak limiter, not dynamic loudnorm.
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "ebur128", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    integrated = float(meas.rsplit("I:", 1)[1].split("LUFS")[0])
    gain = -15.5 - integrated
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                    f"volume={gain:.2f}dB,alimiter=limit=0.79:attack=2:release=60:level=disabled",
                    "-ar", str(SR), out_path], check=True)
    os.remove(raw)
    print(f"{out_path}: {total:.2f}s, {len(e['keys'])} keys, {len(e['clicks'])} clicks, {len(e['whooshes'])} whooshes")


if __name__ == "__main__":
    main(*sys.argv[1:])
