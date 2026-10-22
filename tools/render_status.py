"""Show every frames render in progress: percent, frames, time left, expected finish.

  .venv/bin/python tools/render_status.py           print once
  .venv/bin/python tools/render_status.py --watch   live view, redraws every 2 s, stops when all are done
"""
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent


def rows():
    out = []
    for p in sorted(ROOT.glob("motion/*/*/out/render-progress.json")):
        try:
            d = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue   # being rewritten this instant
        age = time.time() - p.stat().st_mtime
        if d["state"] == "done" and age > 600:
            continue
        out.append((d, age))
    return out


def line(d, age, bar=False):
    left = (f"{d['eta_s'] // 60} min {d['eta_s'] % 60:02d} s left, done about {d['finish_at']}"
            if d.get("eta_s") is not None and d["state"] == "rendering" else "")
    stale = f"  (no update for {int(age)} s: stopped?)" if d["state"] == "rendering" and age > 120 else ""
    workers = f", {d['workers']} workers" if d.get("workers", 1) > 1 else ""
    head = f"{d['piece']}: {d['state']} {d['pct']}% ({d['frame']}/{d['frames']} frames{workers})"
    if not bar:
        return f"{head}, {left}{stale}" if left else head + stale
    filled = int(d["pct"] / 100 * 30)
    return f"{head}\n  [{'#' * filled}{'.' * (30 - filled)}] {left}{stale}"


def main():
    if "--watch" not in sys.argv:
        found = rows()
        for d, age in found:
            print(line(d, age))
        if not found:
            print("no render in progress")
        return
    try:
        while True:
            found = rows()
            sys.stdout.write("\033[2J\033[H")   # clear the terminal, cursor home
            print(time.strftime("%H:%M:%S"), " renders (Ctrl-C to stop)\n")
            for d, age in found:
                print(line(d, age, bar=True) + "\n")
            if not found:
                print("no render in progress")
            if not any(d["state"] in ("rendering", "encoding", "joining") for d, _ in found):
                break
            time.sleep(2)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
