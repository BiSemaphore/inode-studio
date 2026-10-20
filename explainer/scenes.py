"""Scene templates: each scene lays itself out and frames its own camera.

    from scenes import Board, Terminal, Statement
    t = Terminal(s, at=1.2, prompt="sheldon@lab:~$ ", title=None)   # a session, see build.Session
    t.cmd("ls", start=1.5); t.out(...)
    t.done()                                   # places the terminal, frames the camera

    b = Board(s, at=s.B("why", 0.3), title=("short IDs", s.width("why", "why.")))
    b.op("write", s.width("uuid", "random"), x=80, y=320, text=..., size=56, font="mono")
    b.done()                                   # frames the camera on what was drawn

    Statement(s, at=s.B("rule"), lines=[(s.width("rule", "destructive"), "destructive + ambiguous", 84, "ink"), ...])

Coordinates inside a scene are local: (0, 0) is the scene's top left, and a
scene is laid out for a 1920x1080 frame. Scenes get their own area of the
world in order, so stories never place things in world coordinates. The
camera frames the scene's content with padding and room for the subtitles;
explainer/lint_layout.js checks the result.
"""
import math

from build import TERM

COLS = 3                                   # scenes per row in the world


def _frame(x0, y0, x1, y1, aspect, pad=70, below=150, above=0):
    """Camera rectangle (frame aspect W/H) around a box, padded, with room
    underneath for the subtitles and above for the watermark."""
    y0 -= above
    w, h = x1 - x0, y1 - y0 + below
    cw, ch = w + 2 * pad, h + 2 * pad
    if cw / ch < aspect:
        cw = ch * aspect
    else:
        ch = cw / aspect
    cx, cy = x0 + w / 2, y0 + h / 2
    return cx - cw / 2, cy - ch / 2, cw, ch


def _text_w(text, size, font):
    # Ubuntu Mono advances exactly 0.5em; Virgil averages about 0.52em.
    return len(text) * size * (0.5 if font == "mono" else 0.52)


class _Scene:
    def __init__(self, s, at):
        self.s, self.at = s, at
        n = getattr(s, "_scene_count", 0)
        s._scene_count = n + 1
        cell_w, cell_h = s.width + 480, s.height + 420          # world area per scene
        self.ox, self.oy = (n % COLS) * cell_w, (n // COLS) * cell_h
        s.world = (max(getattr(s, "world", (0, 0))[0], self.ox + cell_w), max(getattr(s, "world", (0, 0))[1], self.oy + cell_h))
        self.box = None                      # content bounds, local coordinates

    def _grow(self, x0, y0, x1, y1):
        b = self.box
        self.box = (x0, y0, x1, y1) if b is None else (min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1))

    def _cam(self, dur=1.3):
        x0, y0, x1, y1 = self.box
        vertical = self.s.format == "vertical"
        x, y, w, h = _frame(x0 + self.ox, y0 + self.oy, x1 + self.ox, y1 + self.oy, self.s.width / self.s.height,
                            below=470 if vertical else 150, above=150 if vertical else 0)
        self.s.cam(self.at, x, y, w, h, dur=dur)


class Board(_Scene):
    """A whiteboard area: drawing ops in local coordinates."""

    def __init__(self, s, at, title=None):
        super().__init__(s, at)
        if title:
            text, when = title
            self.op("write", when, x=80, y=150, text=text, size=72)

    def op(self, kind, at, **kw):
        k = dict(kw)
        ox, oy = self.ox, self.oy
        if "x" in k:
            k["x"] += ox
        if "y" in k:
            k["y"] += oy
        if "pts" in k:
            k["pts"] = [[px + ox, py + oy] for px, py in k["pts"]]
        for key in ("from", "to"):
            if key in k:
                k[key] = [k[key][0] + ox, k[key][1] + oy]
        self._measure(kind, kw)
        return self.s.op(kind, at, **k)

    def _measure(self, kind, k):
        if kind == "write":
            size = k.get("size", 40)
            w = _text_w(k["text"], size, k.get("font"))
            x0 = k["x"] - (w / 2 if k.get("anchor") == "middle" else 0)
            self._grow(x0, k["y"] - size * 0.9, x0 + w, k["y"] + size * 0.3)
        elif kind in ("rect", "ring", "marker"):
            pad = k.get("pad", 22) if kind == "ring" else 0
            self._grow(k["x"] - pad, k["y"] - pad, k["x"] + k.get("w", 0) + pad, k["y"] + k.get("h", 0) + pad)
        elif kind in ("line", "polygon"):
            xs, ys = [p[0] for p in k["pts"]], [p[1] for p in k["pts"]]
            self._grow(min(xs), min(ys), max(xs), max(ys))
        elif kind == "arrow":
            self._grow(min(k["from"][0], k["to"][0]), min(k["from"][1], k["to"][1]), max(k["from"][0], k["to"][0]), max(k["from"][1], k["to"][1]))
        elif kind == "card":
            self._grow(k["x"], k["y"], k["x"] + k["w"], k["y"] + k.get("h", 160))
        elif kind == "flow":
            self._grow(min(k["from"][0], k["to"][0]), min(k["from"][1], k["to"][1]), max(k["from"][0], k["to"][0]), max(k["from"][1], k["to"][1]))
        elif kind == "lock":
            z = k.get("size", 120)
            self._grow(k["x"] - z / 2, k["y"] - z / 2, k["x"] + z / 2, k["y"] + z * 0.6)
        elif kind == "cross":
            r = k.get("r", 40)
            self._grow(k["x"] - r, k["y"] - r, k["x"] + r, k["y"] + r)
        elif kind == "cylinder":
            ry = k["h"] * 0.12
            self._grow(k["x"], k["y"] - ry, k["x"] + k["w"], k["y"] + k["h"] + ry)

    def done(self):
        self._cam()
        return self


class Terminal(_Scene):
    """A terminal session (build.Session) placed and framed automatically.
    Optional handwritten title above it."""

    WIDTH, CHARS, LINE, CHROME = 1100, 63, 46, 3 + 46 + 52 + 3

    def __init__(self, s, at, prompt="$ ", cps=10.0, title=None, x=120, y=120, width=None):
        super().__init__(s, at)
        if width:
            self.WIDTH, self.CHARS = width, int((width - 78) // 16)
        self.sess = s.session(prompt, cps)
        self.x, self.y, self.title = x, y, title
        for name in ("cmd", "out", "mark", "wait"):
            setattr(self, name, getattr(self.sess, name))

    def height(self):
        rows = sum(max(1, math.ceil(len(ln["text"]) / self.CHARS)) for ln in self.sess.lines)
        return self.CHROME + rows * self.LINE

    def done(self, appear=None):
        x, y = self.x, self.y
        top = y
        if self.title:
            text, when = self.title
            self.s.op("write", when, x=x + self.ox, y=y - 40 + self.oy, text=text, size=64)
            top = y - 110
        self.s.op("block", appear if appear is not None else self.at, x=x + self.ox, y=y + self.oy, w=self.WIDTH,
                  cls="term", html=TERM, lines=self.sess.lines)
        self._grow(x, top, x + self.WIDTH, y + self.height())
        self._cam()
        return self


class Statement(_Scene):
    """Centred lines of text, each written when its word is spoken:
    lines = [(at, text, size, colour), ...]; optional highlight under one line."""

    def __init__(self, s, at, lines, highlight=None):
        super().__init__(s, at)
        cx, cy = s.width / 2, s.height / 2 - (180 if s.format == "vertical" else 0)
        y = cy - sum(sz * 1.5 for _, _, sz, _ in lines) / 2
        for when, text, size, color in lines:
            y += size * 1.2
            s.op("write", when, x=cx + self.ox, y=y + self.oy, text=text, size=size, color=color, anchor="middle")
            if highlight and highlight[0] == text:
                w = _text_w(text, size, None) * 0.95
                s.op("marker", highlight[1], x=cx - w / 2 + self.ox, y=y - size * 0.3 + self.oy, w=w, h=size * 0.45)
            y += size * 0.3
        self.s.cam(at, self.ox, self.oy, s.width, s.height)
