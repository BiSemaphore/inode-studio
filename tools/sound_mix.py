"""Build a video's soundtrack from a cue sheet (the sound-design skill's mixer).

    .venv/bin/python tools/sound_mix.py motion/<topic>/<part>            # reads <piece>/sound/cues.json

Writes <piece>/assets/audio/: music-bed.wav, sfx-stem.wav and soundtrack.wav (voice + music + foley, loudness
normalised for social: -14 LUFS integrated, true peak -1.5 dBTP), and prints a report: every cue with where its hit
lands, its level against what plays under it, and the final loudness. All paths in cues.json are relative to the piece.

cues.json:
{
  "fps": 30, "length": 47.6, "voice": "assets/audio/voice.wav",
  "music": {"src": "...", "from": 0.0, "gain_db": -9, "fade_in": 0.15, "fade_out": [46.2, 47.6],
            "duck": {"db": -8, "attack": 0.08, "release": 0.5, "lookahead": 0.12, "threshold_db": -45},
            "automation": [[37.9, 0], [38.0, -14], [38.28, -14], [38.34, 0]]},
  "cues": [{"t": 3.05, "src": "assets/audio/sfx/tape-duct.mp3", "db": -18, "what": "sticker presses onto the cover",
            "anchor": "onset" | "peak" | <seconds into the file>, "trim": [from, to], "rate": 1.0, "dur": 0.4}]
}
A cue is placed either at a typed time "t", or (preferred) on the picture itself:
  {"on": "#cover", "n": 2, "event": "start" | "land" | "fast" | "end", "align": "onset" | "peak", "span": true}
"on"/"n" pick the n-th tween of that element (from the running timeline: tools/timeline_events.js); "land" is when the eased
move first reaches 95% of its change, "fast" its fastest frame. "span" trims the sample to the move's length. The
cue's anchor lands one frame after the event (light arrives before sound). Nothing a cue plays may start before its
move starts: onset cues lose their lead-in, peak cues lose any build earlier than the move. The report flags any cue
whose anchor is off by more than a frame or whose sound starts before its move.
Music automation can be tied to a move too: "automation_at": {"on": "#p3e2", "event": "start", "points": [[dt, db], ...]}.
The film length is read from index.html (root data-duration). Each sample is first
normalised to a 0 dBFS peak, so "db" is the cue's peak level in the mix before the final loudness gain.
"""
import json, subprocess, sys
from pathlib import Path

import numpy as np

SR = 48000


def decode(path, trim=None, rate=1.0):
    args = ["ffmpeg", "-v", "error"]
    if trim:
        args += ["-ss", str(trim[0]), "-to", str(trim[1])]
    af = f"asetrate={int(SR * rate)},aresample={SR}" if rate != 1.0 else f"aresample={SR}"
    args += ["-i", str(path), "-af", af, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    raw = subprocess.run(args, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def db(x):
    return 10 ** (x / 20)


def fade(x, fin=0.004, fout=0.03):
    n_in, n_out = min(len(x), int(fin * SR)), min(len(x), int(fout * SR))
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in)[:, None]
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out)[:, None]
    return x


def anchor_of(x, how):
    a = np.abs(x).max(axis=1)
    if isinstance(how, (int, float)):
        return float(how)
    if how == "peak":
        return float(np.argmax(a)) / SR
    return float(np.argmax(a > 0.3 * a.max())) / SR  # onset: first sample above 30% of the peak


def env_db(x, win=0.05):
    """Short-term level in dB per sample position (RMS over win seconds)."""
    m = x.mean(axis=1) ** 2
    k = max(1, int(win * SR))
    c = np.convolve(m, np.ones(k) / k, mode="same")
    return 10 * np.log10(c + 1e-12)


def duck_gain(voice, n, d):
    """Music gain curve: d['db'] while the voice speaks, 0 dB otherwise, smoothed by attack and release."""
    frame = int(0.01 * SR)
    v = voice[:n].mean(axis=1) if len(voice) >= n else np.pad(voice.mean(axis=1), (0, n - len(voice)))
    frames = len(v) // frame
    lvl = 10 * np.log10((v[: frames * frame].reshape(frames, frame) ** 2).mean(axis=1) + 1e-12)
    active = lvl > d.get("threshold_db", -45)
    # hold through short gaps between words (under 0.25 s), so the music does not pump inside a sentence
    hold = int(0.25 / 0.01)
    idx = np.where(active)[0]
    for a, b in zip(idx[:-1], idx[1:]):
        if 1 < b - a <= hold:
            active[a:b] = True
    look = int(d.get("lookahead", 0.12) / 0.01)
    active = np.concatenate([active[look:], np.zeros(look, bool)]) | active
    target = np.where(active, d["db"], 0.0)
    g = np.zeros_like(target)
    a_c, r_c = np.exp(-0.01 / d.get("attack", 0.08)), np.exp(-0.01 / d.get("release", 0.5))
    cur = 0.0
    for i, t in enumerate(target):
        c = a_c if t < cur else r_c
        cur = c * cur + (1 - c) * t
        g[i] = cur
    g = np.repeat(g, frame)
    return np.pad(g, (0, max(0, n - len(g))), mode="edge")[:n]


def automation_gain(points, n):
    if not points:
        return np.zeros(n)
    t = np.arange(n) / SR
    ts, vs = zip(*points)
    return np.interp(t, ts, vs)


def loudness(path):
    out = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    i = [l for l in out.splitlines() if l.strip().startswith("I:")][-1].split()[1]
    p = [l for l in out.splitlines() if l.strip().startswith("Peak:")][-1].split()[1]
    return float(i), float(p)


import math, re


def ease_fn(name):
    name = (name or "none").replace(" ", "")
    m = re.match(r"(power(\d)|expo|sine|back|circ|none|linear)(?:\.(in|out|inOut))?(?:\(([\d.]+)\))?", name)
    kind, pw, mode, arg = (m.group(1), m.group(2), m.group(3) or "out", m.group(4)) if m else ("none", None, "out", None)
    if kind in ("none", "linear"):
        return lambda x: x
    if kind.startswith("power"):
        k = int(pw) + 1
        base = lambda x: x ** k
    elif kind == "expo":
        base = lambda x: 0.0 if x == 0 else 2 ** (10 * (x - 1))
    elif kind == "sine":
        base = lambda x: 1 - math.cos(x * math.pi / 2)
    elif kind == "circ":
        base = lambda x: 1 - math.sqrt(max(0.0, 1 - x * x))
    else:  # back
        c = float(arg or 1.70158)
        base = lambda x: x * x * ((c + 1) * x - c)
    if mode == "in":
        return base
    if mode == "out":
        return lambda x: 1 - base(1 - x)
    return lambda x: base(2 * x) / 2 if x < 0.5 else 1 - base(2 * (1 - x)) / 2


def tween_events(tw):
    s, d, f = tw["start"], tw["duration"], ease_fn(tw.get("ease"))
    xs = np.linspace(0, 1, 601)
    p = np.array([f(x) for x in xs])
    land = s + d * xs[np.argmax(p >= 0.95)]
    fast = s + d * xs[np.argmax(np.gradient(p))]
    return {"start": s, "land": land, "fast": fast, "end": s + d, "duration": d}


def load_tweens(piece):
    """Real tweens from the running timeline (tools/timeline_events.js writes sound/timeline.json)."""
    subprocess.run(["node", str(Path(__file__).parent / "timeline_events.js"), str(piece)], check=True)
    by = {}
    for tw in json.loads((Path(piece) / "sound" / "timeline.json").read_text()):
        if tw["duration"] > 0:
            by.setdefault(tw["target"], []).append(tw)
    return by


def resolve(cue, tweens):
    if "on" not in cue:
        return cue["t"], None
    tws = tweens.get(cue["on"])
    if not tws or len(tws) < cue.get("n", 1):
        sys.exit(f"cue {cue.get('what')}: no tween #{cue.get('n', 1)} on {cue['on']} (have {len(tws or [])})")
    ev = tween_events(tws[cue.get("n", 1) - 1])
    return ev[cue.get("event", "start")] + cue.get("nudge", 0.0), ev


def main(piece):
    piece = Path(piece)
    spec = json.loads((piece / "sound" / "cues.json").read_text())
    length = float(re.search(r'data-composition-id="main"[^>]*?data-duration="([\d.]+)"', (piece / "index.html").read_text()).group(1))
    spec["length"] = length
    fps, n = spec.get("fps", 30), int(length * SR)
    tweens = load_tweens(piece)
    out_dir = piece / "assets" / "audio"
    voice = decode(piece / spec["voice"])
    voice = np.pad(voice, ((0, max(0, n - len(voice))), (0, 0)))[:n]

    # music bed: source from 'from', base gain, ducking under the voice, automation, fades
    m = spec["music"]
    music = decode(piece / m["src"], trim=[m.get("from", 0.0), m.get("from", 0.0) + spec["length"] + 0.5])
    music = np.pad(music, ((0, max(0, n - len(music))), (0, 0)))[:n]
    pts = list(m.get("automation") or [])
    if m.get("automation_at"):
        t0, _ = resolve(m["automation_at"], tweens)
        pts = sorted(pts + [[t0 + dt, v] for dt, v in m["automation_at"]["points"]])
    g = m.get("gain_db", -9) + duck_gain(voice, n, m["duck"]) + automation_gain(pts, n)
    if m.get("fade_out_s"):
        m["fade_out"] = [length - m["fade_out_s"], length]
    music *= db(g)[:, None]
    fi = int(m.get("fade_in", 0.0) * SR)
    if fi:
        music[:fi] *= np.linspace(0, 1, fi)[:, None]
    if m.get("fade_out"):
        a, b = (int(x * SR) for x in m["fade_out"])
        music[a:b] *= np.linspace(1, 0, b - a)[:, None] ** 2
        music[b:] = 0

    # foley: each cue normalised, trimmed, pitched, placed so its anchor lands one frame after t
    sfx = np.zeros((n, 2), np.float32)
    rows = []
    for c in spec["cues"]:
        t, ev = resolve(c, tweens)
        x = decode(piece / c["src"], trim=c.get("trim"), rate=c.get("rate", 1.0))
        x /= max(1e-6, np.abs(x).max())
        align = c.get("align", c.get("anchor", "onset"))
        anc = anchor_of(x, align if align in ("onset", "peak") else float(align))
        hit = t + 1 / fps
        if align == "onset":                      # no lead-in: the sound starts at its onset
            cut = max(0, int((anc - 0.004) * SR))
            x, anc = x[cut:], anc - cut / SR
        if c.get("span") and ev:                  # last as long as the move (plus a short tail)
            c["dur"] = ev["duration"] + c.get("tail", 0.08)
        if c.get("dur"):
            x = x[: int((anc + c["dur"]) * SR)]
        start = hit - anc
        floor = (ev["start"] if ev else t) + 1 / fps - 0.004
        if start < floor:                         # never before the move starts
            drop = int((floor - start) * SR)
            x, start = x[drop:], floor
            x = fade(x, fin=0.02, fout=0.0)
        x = fade(x, fin=0.004, fout=c.get("fade", 0.03)) * db(c["db"])
        s = int(round(start * SR))
        e = min(n, s + len(x))
        sfx[s:e] += x[: e - s]
        a = np.abs(x).max(axis=1)
        audible = start + float(np.argmax(a > a.max() * 0.1)) / SR
        rows.append((t, hit, c["db"], c.get("what", ""), Path(c["src"]).name, s, e, ev, audible))
    bed = voice + music
    sb = env_db(bed)
    report, bad = [], 0
    frame = 1 / fps
    for t, hit, d_, what, name, s0, e0, ev, audible in rows:
        h = int(hit * SR)
        w = slice(max(0, h - int(0.05 * SR)), min(n, h + int(0.15 * SR)))
        over = env_db(sfx[w]).max() - sb[w].max()
        flag = ""
        if ev and audible < ev["start"] - 0.004:
            flag = f"  SOUND BEFORE MOVE ({(ev['start'] - audible) * 1000:.0f} ms)"
        mv = f"move {ev['start']:6.2f}-{ev['end']:6.2f}" if ev else "move   (typed time)  "
        bad += bool(flag)
        report.append(f"{t:6.2f}s  {mv}  sound {audible:6.2f}-{e0 / SR:6.2f}  {d_:5.1f} dB {over:+5.1f} vs bed  {name:24s} {what}{flag}")
    report.append(f"\nsync: {len(rows) - bad}/{len(rows)} cues start with their move and hit within a frame" + ("" if not bad else "  <-- FIX"))
    (piece / "sound" / "sync.json").write_text(json.dumps({"cues": len(rows), "bad": bad}))
    def write(x, name):
        p = out_dir / name
        raw = np.clip(x, -1, 1).astype(np.float32).tobytes()
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-c:a", "pcm_s24le", str(p)], input=raw, check=True)
        return p

    write(music, "music-bed.wav")
    write(sfx, "sfx-stem.wav")
    pre = write((voice + music + sfx) * 0.5, "_premix.wav")  # headroom before the loudness pass
    target = spec.get("target_lufs", -14.0)
    meas = subprocess.run(["ffmpeg", "-nostats", "-i", str(pre), "-af",
                           f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    j = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    final = out_dir / "soundtrack.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af",
                    f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
                    f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:"
                    f"linear=true,aresample={SR}", "-c:a", "pcm_s24le", str(final)], check=True)
    pre.unlink()
    i, p = loudness(final)
    print("\n".join(report))
    print(f"\nsoundtrack.wav  {length} s  integrated {i} LUFS  peak {p} dBFS  (target {target}, TP -1.5)")


if __name__ == "__main__":
    main(sys.argv[1])
