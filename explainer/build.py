"""Shared pipeline for explainer videos. A video's story.py only writes scenes:

    import sys, pathlib; sys.path.insert(0, "<repo>/explainer")   # see template/story.py
    from build import Story
    s = Story(__file__)                   # synthesizes the voice from beats.json, loads word times
    s.cam(0, 0, 0, 1920, 1080)            # camera frames a world rectangle
    s.op("write", s.W("hook", "notes"), x=170, y=175, text="...", size=70)
    s.build(title="...")                  # page, sound, ready to record

Timing: s.B(beat, dt) is dt seconds after a beat starts; s.W(beat, word, dt)
is dt seconds after a caption word is spoken. Every visual should be tied to
the word it illustrates. Nothing is ever sped up to catch the voice: if a
scene does not fit, cut drawing, not time (see README.md).
"""

import html
import json
import math
import os
import pathlib
import random
import re
import subprocess
import sys

STUDIO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
TERM = '<div class="bar"><i></i><i></i><i></i></div><div class="body"></div>'
# Colours are theme roles, resolved by the kit from the theme (explainer/themes/*.json);
# a hex value still works for a one-off colour.
BLUE, RED, GREEN, INK, HIGHLIGHT = "accent", "red", "green", "ink", "highlight"
GREY = INK   # house rule: no grey text
DUR = {"rect": 0.9, "ellipse": 0.7, "line": 0.5, "arrow": 0.6, "cylinder": 1.2,
       "polygon": 0.8, "ring": 0.8, "check": 0.4, "marker": 0.5}


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def load_brand():
    """brand.json, or brand.example.json when there is none: end card text,
    logo files, colour overrides (README.md, "Your brand")."""
    for name in ("brand.json", "brand.example.json"):
        p = STUDIO / name
        if p.exists():
            return json.loads(p.read_text())
    return {}


def lockup(logo, src, cls="lockup", dark=False):
    """The logo as HTML: mark and wordmark side by side, or whichever one is
    set; "" without a logo. Dark themes use the *_dark files when given."""
    logo = logo or {}
    mark = (dark and logo.get("mark_dark")) or logo.get("mark")
    word = (dark and logo.get("word_dark")) or logo.get("word")
    if not mark and not word:
        return ""
    off = logo.get("word_offset")   # em: drops the wordmark onto the mark's baseline
    style = ' style="align-items: flex-start"' if off is not None else ""
    wstyle = f' style="margin-top: {off}em"' if off is not None else ""
    return (f'<span class="{cls}"{style}>'
            + (f'<img class="logo-mark" src="{src(mark)}" alt="">' if mark else "")
            + (f'<img class="logo-word" src="{src(word)}"{wstyle} alt="">' if word else "")
            + "</span>")


class Story:
    def __init__(self, story_file, seed=7, theme=None, format="landscape"):
        """format: "landscape" (1920x1080) or "vertical" (1080x1920, for
        Reels, Shorts and LinkedIn mobile: larger captions placed above the
        apps' bottom controls)."""
        self.here = pathlib.Path(story_file).resolve().parent
        self.format = format
        self.width, self.height = (1080, 1920) if format == "vertical" else (1920, 1080)
        # script.md (narration, title, theme, intro, caption) compiles to beats.json + meta.json.
        self.script = None
        if (self.here / "script.md").exists():
            import script as script_mod
            self.script = script_mod.compile_piece(self.here)
        theme = os.environ.get("THEME") or theme or (self.script or {}).get("theme") or "whiteboard"
        self.theme = json.loads((STUDIO / "explainer" / "themes" / f"{theme}.json").read_text())
        self.brand = load_brand()
        voice = self.here / "voice"
        subprocess.run([str(STUDIO / ".venv/bin/python"), str(STUDIO / "explainer/voice.py"),
                        str(self.here / "beats.json"), str(voice)], check=True)
        self.beats = json.loads((self.here / "beats.json").read_text())["beats"]
        self.timing = json.loads((voice / "timings.json").read_text())
        self.id = {b["id"]: i for i, b in enumerate(self.beats)}
        self.total = round(self.timing[-1]["end"] + 4.0, 1)
        self.rng = random.Random(seed)
        self.ops, self.cams = [], []
        self.constraints = []   # (label, ready, needed_by, slack): checked by build()
        self.sfx = {"total": self.total, "keys": [], "ticks": [], "pops": [], "whooshes": [],
                    "misses": [], "hits": [], "chord": [], "thumps": []}

    # ---------- timing ----------

    def B(self, beat, dt=0.0):
        return round(self.timing[self.id[beat]]["start"] + dt, 3)

    def W(self, beat, word, dt=0.0, nth=0):
        hits = [w for w in self.timing[self.id[beat]]["words"] if norm(w[0]) == norm(word)]
        if not hits:
            raise KeyError(f"word {word!r} not in beat {beat!r}")
        return round(hits[nth][1] + dt, 3)

    def typing(self, at, text, cps=10.0, start=0):
        """Per-character times for typing text[start:] at a human pace (about
        cps keys a second, uneven, a little longer after spaces). Characters
        before `start` (a shell prompt) appear at once. Every time is snapped
        to the 30 fps frame grid, and the kit shows each character on exactly
        that frame, so a key sound placed at the same time lands on the frame
        its character appears."""
        fps = 30
        snap = lambda x: math.ceil(x * fps - 1e-9) / fps
        t = snap(at)
        out = [t] * start
        mean = 1.0 / cps
        for ch in text[start:]:
            out.append(round(t, 6))
            d = self.rng.uniform(0.75 * mean, 1.35 * mean)
            if ch == " ":
                d += self.rng.uniform(0.02, 0.06)
            t = snap(t + max(d, 2 / fps))
        return out

    def _keys(self, times, text, enter=True, start=0):
        ev = [[t, "space" if c == " " else "key"] for t, c in list(zip(times, text))[start:]]
        if enter:
            ev.append([round(times[-1] + 0.18, 3), "enter"])
        return ev

    # ---------- scene ops ----------

    def op(self, kind, at, **kw):
        o = {"kind": kind, "at": at, **kw}
        if kind in DUR:
            o.setdefault("dur", DUR[kind])
        # Text on the whiteboard is written, never typed: only terminal
        # commands make key sounds.
        o.pop("typed", None)
        o.pop("speed", None)
        self.ops.append(o)
        if kind == "cross":
            self.sfx["misses"].append(at + 0.45)
        if kind == "card":
            self.sfx["ticks"].append(at)
            for st in o.get("states", []):
                self.sfx["misses" if st.get("tone") == "bad" else "hits" if st.get("tone") == "good" else "ticks"].append(st["at"])
        if kind == "lock":
            self.sfx["thumps"].append(at + 0.4)
        if kind == "stamp":
            self.sfx["thumps"].append(at + 0.18)
        if kind == "check":
            self.sfx["hits"].append(at + 0.3)
        if kind == "dot":
            self.sfx["pops"].append(at + (o.get("fly", 1.1) if "from" in o else 0))
        if kind == "block":
            self.sfx["pops"].append(at)
        if kind == "node":
            self.sfx["pops"].append(at)
            for ev in o.get("events", []):
                self.sfx["misses" if ev["kind"] == "fail" else "hits" if ev["kind"] == "ok" else "ticks"].append(ev["at"])
        if kind == "packet":
            self.sfx["ticks"].append(at + o.get("dur", 0.8))        # arrival
        if kind == "code":
            self.sfx["ticks"].append(at)
            for ln in o.get("lines", []):
                if ln.get("times"):
                    self.sfx["keys"] += self._keys(ln["times"], ln["text"], start=ln.get("prompt", 0))
                else:
                    self.sfx["ticks"].append(ln["at"])
        if kind == "bars":
            self.sfx["ticks"] += [round(at + k * o.get("step", 0.035), 3) for k in range(0, o["n"], 3)]
        return o

    def cam(self, at, x, y, w, h, dur=1.3, lift=0):
        if self.cams:
            self.sfx["whooshes"].append([at, 0.6])
        self.cams.append({"at": at, "x": x, "y": y, "w": w, "h": h, "dur": dur, "lift": lift})

    def line(self, at, text, typed=False, cps=10.0, cls="", marks=()):
        """One terminal line. Typed lines show the prompt (up to "$ ") at once
        and type the rest at a human pace; others print at once. `marks` are
        (time, colour) underlines. Returns the line; line["end"] is when it is
        complete."""
        ln = {"at": at, "text": text, "html": html.escape(text), "cls": cls,
              "marks": [{"at": t, "color": c} for t, c in marks]}
        if typed:
            p = text.find("$ ")
            ln["prompt"] = p + 2 if p >= 0 else 0
            ln["times"] = self.typing(at, text, cps, ln["prompt"])
            ln["end"] = ln["times"][-1]
        else:
            ln["end"] = at
        return ln

    # ---------- timeline ----------

    def need(self, label, ready, by, slack=0.4):
        """Record that `label` is ready at `ready` and must be by `by` (usually
        the moment a word is spoken). build() fails if any of these is late by
        more than `slack` seconds, so drift is caught before rendering."""
        self.constraints.append((label, round(ready, 3), round(by, 3), slack))

    def session(self, prompt="$ ", cps=10.0):
        return Session(self, prompt, cps)

    def check_timeline(self):
        late = [c for c in self.constraints if c[1] > c[2] + c[3]]
        for label, ready, by, slack in self.constraints:
            flag = "LATE" if (label, ready, by, slack) in late else "ok"
            print(f"  {flag:4} {label:42} ready {ready:7.2f}s  needed {by:7.2f}s")
        return late

    # ---------- output ----------

    def sentences(self):
        """Subtitles: whole sentences with the time span they are spoken in."""
        out = []
        for i, _ in enumerate(self.beats):
            cur = []
            for w in self.timing[i]["words"]:
                cur.append(w)
                if re.search(r'[.?!]["”]?$', w[0]):
                    out.append(cur)
                    cur = []
            if cur:
                out.append(cur)
        return [{"text": html.escape(" ".join(w[0] for w in s)), "start": s[0][1], "end": s[-1][2]} for s in out]

    def lines(self, max_chars=None):
        """Subtitle lines: words in speaking order, a new line at each sentence
        end or when the line would pass max_chars. Each word keeps its time, so
        the line builds up as it is spoken."""
        max_chars = max_chars or (26 if self.format == "vertical" else 52)
        out = []
        for i, _ in enumerate(self.beats):
            cur = []
            for w in self.timing[i]["words"]:
                if cur and len(" ".join(x[0] for x in cur + [w])) > max_chars:
                    out.append(cur)
                    cur = []
                cur.append(w)
                if re.search(r'[.?!]["”]?$', w[0]):
                    out.append(cur)
                    cur = []
            if cur:
                out.append(cur)
        return [[[html.escape(w), s, e] for w, s, e in ln] for ln in out]

    def write_srt(self, path):
        """Subtitles as an SRT file (LinkedIn, YouTube): one sentence per cue,
        the same text and timing as the burned-in subtitles."""
        def ts(t):
            ms = int(round(t * 1000))
            return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
        cues = [{"text": " ".join(w for w, _, _ in ln), "start": ln[0][1], "end": ln[-1][2]} for ln in self.lines()]
        out = []
        for k, c in enumerate(cues, 1):
            start = max(0.0, c["start"] - 0.1)
            end = c["end"] + 0.35
            if k < len(cues):
                end = min(end, cues[k]["start"] - 0.12)
            out.append(f"{k}\n{ts(start)} --> {ts(end)}\n{html.unescape(c['text'])}\n")
        pathlib.Path(path).write_text("\n".join(out))

    def build(self, title, world=None, endcard=None, end_at=None, intro=None, allow_late=False):
        world = world or getattr(self, "world", None) or (6400, 2500)   # scenes.py grows self.world
        if intro is None and self.script and self.script.get("intro"):
            l1, l2 = (self.script["intro"] + [""])[:2]
            intro = {"label": self.script["series"], "line1": l1, "line2": l2, "until": max(0.0, self.script["lead"] - 0.2)}
        late = self.check_timeline()
        if late and not allow_late:
            raise SystemExit(f"timeline: {len(late)} step(s) would lag the voice; give them more time "
                             "(start earlier, add a pause to the beat) instead of rushing")
        endcard = {"mark": "", "sub": "", "url": "", **(endcard or self.brand.get("endcard") or {})}
        end_at = end_at if end_at is not None else self.B(self.beats[-1]["id"], -0.3)
        self.sfx["chord"].append(end_at + 0.2)
        story = {"total": self.total, "ops": self.ops, "cams": sorted(self.cams, key=lambda c: c["at"]),
                 "lines": self.lines(), "overlays": [{"id": "endcard", "at": end_at, "dur": 0.9}]}
        # Asset paths relative to this video's folder, wherever it lives under motion/.
        R = os.path.relpath(STUDIO, self.here)
        th = self.theme
        logo = lockup(self.brand.get("logo"), lambda f: f"{R}/{f}", dark=th.get("dark", False))
        intro_html = ""
        if intro:
            # Opening card on frame 0: the hook as typography, the series label
            # and the lockup; fades out as the story starts.
            story["overlays"].append({"id": "introcard", "at": intro["until"], "dur": 0.4, "out": True})
            intro_html = (f'<div id="introcard"><div class="label">{html.escape(intro["label"])}</div>'
                          f'<h1>{html.escape(intro["line1"])}<br>{html.escape(intro["line2"])}<span class="brand-dot"></span></h1>'
                          f'{logo}</div>')
        (self.here / "sfx.json").write_text(json.dumps(self.sfx))
        self.write_srt(self.here / f"{self.here.name}.srt")
        ww, wh = world
        colors = {**th["colors"], **self.brand.get("colors", {})}
        root = "; ".join([f"--{k}: {v}" for k, v in colors.items()] +
                         [f'--font-{k}: "{v}"' for k, v in th["fonts"].items()])
        watermark = logo.replace('class="lockup"', 'id="watermark" class="lockup"', 1)
        byline = logo.replace('class="lockup"', 'class="by lockup"', 1)
        url = f'<div class="url">{html.escape(endcard["url"])}</div>' if endcard["url"] else ""
        page = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<link rel="stylesheet" href="{R}/explainer/style.css">
<style>:root {{ {root} }}</style>
<script src="{R}/explainer/vendor/rough.js"></script>
</head><body class="{self.format}">
<div id="stage" style="width:{self.width}px;height:{self.height}px">
  <div id="world" style="width:{ww}px;height:{wh}px"><svg id="board" width="{ww}" height="{wh}" viewBox="0 0 {ww} {wh}"><defs id="defs"></defs><g id="under"></g><g id="over"></g></svg>
    <svg id="inklayer" width="{ww}" height="{wh}" viewBox="0 0 {ww} {wh}"><g id="ink"></g></svg></div>
  <div id="subtitles"></div>
  {intro_html}
  {watermark}
  <div id="endcard"><div class="mark">{html.escape(endcard['mark'])}</div><div class="sub2">{html.escape(endcard['sub'])}</div>
    {url}
    {byline}</div>
</div>
<script>window.MOTION = {{ duration: {self.total}, fps: 30, width: {self.width}, height: {self.height}, scale: 2, ready: false,
  outputs: [{{ width: {self.width}, height: {self.height}, crf: 15 }}] }};
window.STORY = {json.dumps(story)};</script>
<script src="{R}/explainer/kit.js"></script>
<script src="{R}/explainer/preview.js"></script>
</body></html>
"""
        (self.here / "piece.html").write_text(page)
        subprocess.run([str(STUDIO / ".venv/bin/python"), str(STUDIO / "explainer/mix.py"), str(self.here)], check=True)
        print(f"{len(self.ops)} ops, {len(self.cams)} camera moves, {len(story['lines'])} subtitle lines, {self.total}s")


class Session:
    """A terminal session laid out in time. Commands are typed at a human pace
    after whatever came before; output follows its command. Each step can say
    which spoken word it has to be ready for (`by=`), and underline marks wait
    for their line to be printed, so nothing on screen runs ahead of or lags
    behind the voice without the build saying so.

        t = s.session("leonard@lab:~$ ", cps=11)
        t.cmd("git log --oneline -3", start=s.W("fix1", "Leonard's"), by=s.W("fix1", "stops,"))
        t.out('Error: ...', mark=(s.W("fix1", "stops,"), GREEN))
        op("block", ..., lines=t.lines)
    """

    def __init__(self, story, prompt, cps):
        self.s, self.prompt, self.cps = story, prompt, cps
        self.lines, self.t = [], None

    def cmd(self, text, start=None, by=None, gap=0.35, label=None, paste=False):
        """Type a command at a human pace; paste=True shows it at once (a long
        command an engineer would paste, not type), with no key sounds."""
        earliest = self.t + gap if self.t is not None else 0.0
        at = earliest if start is None else max(start, earliest)
        if start is not None and start < earliest - 0.05:
            self.s.need(f"cmd {text!r} starts", earliest, start, slack=0.4)
        ln = self.s.line(at, self.prompt + text) if paste else self.s.line(at, self.prompt + text, True, self.cps)
        self.lines.append(ln)
        self.t = ln["end"] + 0.3          # Enter, then the program answers
        self._printed = 0
        if by is not None:
            self.s.need(label or f"cmd {text!r} typed", ln["end"], by)
        return ln

    def out(self, text, mark=None, by=None, label=None, delay=None):
        """Print a line of output; `delay` overrides the default small gap
        after the previous line (for a program that pauses, like a prompt)."""
        at = self.t + (0.04 * self._printed if delay is None else delay)
        if delay is not None:
            self.t = at
            self._printed = 0
        self._printed += 1
        marks = []
        if mark is not None:
            word_t, color = mark
            marks = [(max(at + 0.3, word_t), color)]
            self.s.need(label or f"output {text[:30]!r} for its mark", at + 0.3, word_t)
        ln = self.s.line(at, text, marks=marks)
        self.lines.append(ln)
        if by is not None:
            self.s.need(label or f"output {text[:30]!r}", at, by)
        return ln

    def wait(self, until):
        """Nothing new before `until` (for example, let the voice catch up)."""
        self.t = max(self.t or 0.0, until)

    def mark(self, ln, word_t, color):
        """Underline an earlier line when a word is spoken."""
        ln["marks"].append({"at": max(ln["at"] + 0.3, word_t), "color": color})
