"""Show every frames render in progress: percent, frames, time left, expected finish.

  .venv/bin/python tools/render_status.py           print once
  .venv/bin/python tools/render_status.py --watch   live view, redraws in place every 2 s (like top), stops when all are done

A render whose progress file has not changed for 10 minutes is shown once, at the bottom, as stopped.
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


STALE = 600


def split(found):
    live = [(d, a) for d, a in found if not (d["state"] == "rendering" and a > STALE)]
    dead = [d for d, a in found if d["state"] == "rendering" and a > STALE]
    return live, dead


def main():
    if "--watch" not in sys.argv:
        live, dead = split(rows())
        for d, age in live:
            print(line(d, age))
        if not live:
            print("no render in progress")
        if dead:
            print("stopped: " + ", ".join(f"{d['piece']} ({d['pct']}%)" for d in dead))
        return
    tty = sys.stdout.isatty()
    if tty:
        sys.stdout.write("\033[?1049h\033[?25l")   # alternate screen (like top), hide the cursor
    last = None
    try:
        while True:
            live, dead = split(rows())
            body = [time.strftime("%H:%M:%S") + "  renders (Ctrl-C to stop)", ""]
            for d, age in live:
                body += line(d, age, bar_view=True).split("\n") + [""]
            if not live:
                body.append("no render in progress")
            if dead:
                body.append("stopped: " + ", ".join(f"{d['piece']} ({d['pct']}%)" for d in dead))
            if tty:   # redraw in place: cursor home, each line cleared to its end, then clear below
                sys.stdout.write("\033[H" + "".join(l + "\033[K\n" for l in body) + "\033[J")
                sys.stdout.flush()
            elif body[1:] != last:   # piped (not a terminal): print only when something changed
                print("\n".join(body), flush=True)
                last = body[1:]
            if not any(d["state"] in ("rendering", "encoding", "joining") for d, _ in live):
                break
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        if tty:
            sys.stdout.write("\033[?25h\033[?1049l")   # back to the normal screen, cursor visible
            live, dead = split(rows())
            for d, age in live:
                print(line(d, age))


if __name__ == "__main__":
    main()
