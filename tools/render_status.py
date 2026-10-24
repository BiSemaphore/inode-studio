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


def bar(pct, width=30):
    """The same bar the renderer draws: [=========>          ]"""
    full = int(pct / 100 * width)
    return "[" + ("=" * width if full >= width else "=" * max(0, full - 1) + (">" if full else "") + " " * (width - full)) + "]"


def line(d, age, bar_view=False):
    eta = d.get("eta_s")
    tail = (f"ETA {eta // 60}:{eta % 60:02d}, done about {d['finish_at']}" if eta is not None and d["state"] == "rendering"
            else "joining chunks" if d["state"] == "joining" else d["state"])
    stale = f"  (no update for {int(age)} s: stopped?)" if d["state"] == "rendering" and age > 120 else ""
    fps = f"  render speed {d['fps']} frames/s" if d.get("fps") else ""
    workers = f"  {d['workers']} workers" if d.get("workers", 1) > 1 else ""
    if not bar_view:
        return f"{d['piece']}: {d['state']} {d['pct']}% ({d['frame']}/{d['frames']} frames{workers}){fps}, {tail}{stale}"
    return f"{d['piece']}  {bar(d['pct'])} {d['pct']:3d}%  {d['frame']}/{d['frames']} frames{fps}{workers}\n  {tail}{stale}"


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
                print(line(d, age, bar_view=True) + "\n")
            if not found:
                print("no render in progress")
            if not any(d["state"] in ("rendering", "encoding", "joining") for d, _ in found):
                break
            time.sleep(2)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
