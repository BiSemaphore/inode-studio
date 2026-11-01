"""The quality gate (process step 5): one command, PASS or FAIL per check, before the owner sees a video.

    .venv/bin/python tools/qa.py motion/<topic>/<part> [renders/<file>.mp4]     # default: the newest render

Checks, in order:
  1. voice      voice/verify.txt says OK (every line heard as written)
  2. compose    `npx hyperframes check` passes
  3. sync       sound/sync.json from tools/sound_mix.py: every cue starts with its move and hits within a frame
  4. frames     tools/check_video.py: 0 broken frames
  5. format     1080x1920, 30 fps, length matches index.html within a frame
  6. av-offset  the render's audio IS assets/audio/soundtrack.wav (correlation >= 0.99) with 0 offset (within 1 ms)
  7. loudness   integrated -14 LUFS (+/- 1), sample peak at most -1.0 dBFS
Then it reminds what is still manual: the video-reviewer agent and the owner's listen. Exit code 1 on any FAIL.
"""
import json, re, subprocess, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
HF = ["npx", "--yes", "hyperframes@0.8.222"]


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def decode(path, sr=8000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def main(piece, video=None):
    piece = (ROOT / piece) if not Path(piece).is_absolute() else Path(piece)
    if video is None:
        vids = sorted((piece / "renders").glob("*.mp4"), key=lambda p: p.stat().st_mtime)
        if not vids:
            sys.exit("no render in renders/")
        video = vids[-1]
    video = Path(video) if Path(video).is_absolute() else piece / video
    results = []

    def report(name, ok, detail):
        results.append(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {name:10s} {detail}")

    v = piece / "voice" / "verify.txt"
    first = v.read_text().splitlines()[0] if v.exists() else "missing"
    report("voice", first.startswith("OK"), first)

    run(HF + ["check", "--json"], cwd=piece)
    checks = sorted((piece / ".hyperframes" / "artifacts" / "checks").glob("*.json"), key=lambda p: p.stat().st_mtime)
    ok = bool(checks) and json.loads(checks[-1].read_text()).get("ok") is True
    report("compose", ok, "hyperframes check " + ("ok" if ok else "has errors (run it to see them)"))

    sj = piece / "sound" / "sync.json"
    if sj.exists():
        s = json.loads(sj.read_text())
        report("sync", s["bad"] == 0, f"{s['cues'] - s['bad']}/{s['cues']} cues start with their move, hit within a frame")
    else:
        report("sync", False, "no sound/sync.json: run tools/sound_mix.py")

    out = run([str(ROOT / ".venv/bin/python"), str(ROOT / "tools/check_video.py"), str(video)]).stdout.strip()
    m = re.search(r"(\d+) frames, (\d+) broken", out)
    report("frames", bool(m) and m.group(2) == "0", out.split(": ", 1)[-1] if out else "check_video gave no output")

    probe = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(video)]).stdout)
    st, dur = probe["streams"][0], float(probe["format"]["duration"])
    want = float(re.search(r'data-composition-id="main"[^>]*?data-duration="([\d.]+)"', (piece / "index.html").read_text()).group(1))
    fmt_ok = st["width"] == 1080 and st["height"] == 1920 and st["r_frame_rate"] == "30/1" and abs(dur - want) <= 1 / 30 + 0.01
    report("format", fmt_ok, f"{st['width']}x{st['height']} {st['r_frame_rate']} fps, {dur:.2f} s (film {want} s)")

    st_wav = piece / "assets" / "audio" / "soundtrack.wav"
    if st_wav.exists():
        a, b = decode(video), decode(st_wav)
        n = min(len(a), len(b))
        a, b = a[:n], b[:n]
        lag = max(range(-400, 401), key=lambda k: float(np.dot(a[max(0, k):n + min(0, k)], b[max(0, -k):n - max(0, k)])))
        ms = lag / 8
        x, y = a[max(0, lag):n + min(0, lag)], b[max(0, -lag):n - max(0, lag)]
        r = float(np.corrcoef(x, y)[0, 1])
        report("av-offset", abs(ms) <= 1 and r >= 0.99, f"render audio vs soundtrack.wav: {ms:+.1f} ms, match {r:.3f} (need 0.99)")
    else:
        report("av-offset", False, "no assets/audio/soundtrack.wav")

    err = run(["ffmpeg", "-nostats", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    i = float([l for l in err.splitlines() if l.strip().startswith("I:")][-1].split()[1])
    p = float([l for l in err.splitlines() if l.strip().startswith("Peak:")][-1].split()[1])
    report("loudness", abs(i + 14) <= 1 and p <= -1.0, f"{i} LUFS, peak {p} dBFS")

    passed = all(results)
    print(f"\n{'PASSED' if passed else 'FAILED'}: {sum(results)}/{len(results)} checks on {video.relative_to(ROOT)}")
    print("Still manual: run the video-reviewer agent on this render, then ask the owner to listen (phone + headphones).")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
