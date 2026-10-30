"""Draw hand-made doodles on a photo from a small JSON plan (skill: .claude/skills/photo-doodle).

  .venv/bin/python tools/doodle/doodle.py <photo> <plan.json> [--out out.png] [--html-only]

The plan is {"elements": [...]} (optional "color", "accent", "stroke", "max_side", "palette", "shadow").
"palette": a name (crayon, pastel, mint, sunset, mono-white, mono-ink) or a list of colours; elements without their
own "color" take the palette colours in turn. Positions are fractions of the
photo (x of the width, y of the height); sizes are fractions of the width. Elements:

  text     {"text", "x", "y", "size", "font", "align", "rotate", "color", "behind"}
  arc      {"text", "cx", "cy", "r", "from", "to", "size", "font", "behind"}   text on a circle (degrees, 0 = up)
  label    {"text", "x", "y", "to": [x, y], "arrow": "curve|dotted|loop|straight", "bend", "size", "font"}
  outline  {"pad", "dashed", "overshoot", "round", "region": [x0, y0, x1, y1]}   a loose hand loop around the subject;
           "region" limits it to one object (the subject mask inside the box, or the box itself if the mask is empty)
  ornament {"shape": "star|sparkle|heart|flower|swirl|notes|leaves|dots", "x", "y", "size", "rotate", "color"}
  bubble   {"text", "x", "y", "size", "tail": "left|right"}   speech bubble
  capsule  {"text", "x", "y", "size", "dashed"}      a dashed rounded tag
  ground   {"x", "y", "w"}                           short strokes around the base of an object
  figure   {"pose": "sit|wave|peek", "x", "y", "size", "front"}   a monoline person; (x, y) = where it sits or stands
  wave     {"y", "amp", "notes"}                     a wavy staff line across the photo, optional music notes
  svg      {"content"}                               raw SVG markup in photo pixels; class="ln" draws a hand line

"behind": true puts text behind the subject (Vision subject mask, tools/subject_mask.swift, cached per photo).
Fonts: hand, marker, script, serif, italic, bold, caps, pen, doodle, scribble. Ornaments take "fill": true. Output defaults to <photo stem>-doodled.png next to the photo.
"""
import argparse
import hashlib
import html
import json
import math
import pathlib
import random
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter, ImageOps

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FONTS = {
    "hand": ("'Patrick Hand', cursive", 400, "normal", "none"),
    "marker": ("'Gochi Hand', cursive", 400, "normal", "none"),
    "caps": ("'Gochi Hand', cursive", 400, "normal", "uppercase"),
    "script": ("'Caveat', cursive", 700, "normal", "none"),
    "serif": ("'DM Serif Display', serif", 400, "normal", "none"),
    "italic": ("'Fraunces', serif", 400, "italic", "none"),
    "bold": ("'Inter Tight', sans-serif", 900, "normal", "none"),
    "pen": ("'Nanum Pen Script', cursive", 400, "normal", "none"),        # real pen handwriting (owner 2026-10-30)
    "doodle": ("'Gloria Hallelujah', cursive", 400, "normal", "none"),
    "scribble": ("'Reenie Beanie', cursive", 400, "normal", "none"),
}
PALETTES = {
    "crayon": ["#E8483B", "#2F6FD6", "#F2A93B", "#3FA34D", "#9B5DE5", "#F06BA8"],
    "pastel": ["#FFB5A7", "#A8D5BA", "#FFE29A", "#B8C0FF", "#F7C6E0", "#9ED8DB"],
    "mint": ["#5EE08C", "#FFFFFF", "#B9F5D0"],
    "sunset": ["#FF8A5B", "#FFD166", "#FF5D8F", "#FFF1D6"],
    "mono-white": ["#FFFFFF"],
    "mono-ink": ["#1B1A17"],
}
FONT_LINK = ("https://fonts.googleapis.com/css2?family=Patrick+Hand&family=Gochi+Hand&family=Caveat:wght@700"
             "&family=DM+Serif+Display&family=Fraunces:ital,opsz,wght@0,9..144,400;1,9..144,400&family=Inter+Tight:wght@900"
             "&family=Nanum+Pen+Script&family=Gloria+Hallelujah&family=Reenie+Beanie&display=swap")


def load_photo(src, work, max_side):
    """The photo upright (EXIF applied), HEIC converted, capped at max_side; cached in the work folder."""
    work.mkdir(parents=True, exist_ok=True)
    base = work / "base.jpg"
    if not base.exists():
        path = src
        if src.suffix.lower() in (".heic", ".heif"):
            path = work / "converted.jpg"
            subprocess.run(["sips", "-s", "format", "jpeg", str(src), "--out", str(path)], check=True, capture_output=True)
        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        im.thumbnail((max_side, max_side), Image.LANCZOS)
        im.save(base, quality=92)
    return base, Image.open(base).size


def subject_mask(base, work):
    """White-on-black mask of the foreground subjects, same size as base (Vision, on-device)."""
    mask = work / "mask.png"
    if not mask.exists():
        r = subprocess.run(["swift", str(ROOT / "tools" / "subject_mask.swift"), str(base), str(mask)], capture_output=True, text=True)
        if r.returncode != 0 or not mask.exists():
            sys.exit("subject mask failed: " + (r.stderr or r.stdout)[-400:])
    m = Image.open(mask).convert("L")
    size = Image.open(base).size
    return m if m.size == size else m.resize(size, Image.LANCZOS)


def cutout(base, mask, work):
    cut = work / "cut.png"
    if not cut.exists():
        im = Image.open(base).convert("RGB")
        im.putalpha(mask.filter(ImageFilter.GaussianBlur(1.2)))
        im.save(cut)
    return cut


def smooth_closed(pts):
    """Catmull-Rom through closed points, as an SVG cubic path."""
    n = len(pts)
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def outline_path(mask, W, pad, overshoot, rnd, region=None, round_=.6):
    """A loose loop around the subject: farthest mask pixel per angle from the centroid, padded, smoothed, wobbled."""
    small = mask.resize((200, round(200 * mask.size[1] / mask.size[0])))
    a = np.asarray(small, dtype=np.float32) / 255 > 0.5
    if region:                                                              # one object: keep the mask inside the box
        h, w = a.shape
        x0, y0, x1, y1 = int(region[0] * w), int(region[1] * h), int(region[2] * w), int(region[3] * h)
        box = np.zeros_like(a); box[y0:y1, x0:x1] = True
        a = (a & box) if (a & box).sum() > .2 * box.sum() else box          # mostly empty there: use the box itself
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        sys.exit("outline: no subject found in the photo")
    k = mask.size[0] / small.size[0]
    cx, cy = xs.mean(), ys.mean()
    ang = np.arctan2(ys - cy, xs - cx)
    dist = np.hypot(xs - cx, ys - cy)
    radii = []
    for i in range(36):
        lo = -math.pi + i * math.pi / 18
        sel = (ang >= lo) & (ang < lo + math.pi / 18)
        radii.append(dist[sel].max() if sel.any() else 0)
    radii = np.array(radii)
    radii = np.where(radii == 0, radii.max() * .6, radii)
    radii = (np.roll(radii, 1) + 2 * radii + np.roll(radii, -1)) / 4          # smooth
    ea, eb = (xs.max() - xs.min()) / 2 * 1.08, (ys.max() - ys.min()) / 2 * 1.08  # a hand loop is rounder than the object
    ts = -math.pi + (np.arange(36) + .5) * math.pi / 18
    ell = ea * eb / np.sqrt((eb * np.cos(ts)) ** 2 + (ea * np.sin(ts)) ** 2)
    radii = (1 - round_) * radii + round_ * ell
    pts = []
    for i, r in enumerate(radii):
        t = -math.pi + (i + .5) * math.pi / 18
        rr = (r * k + pad * W) * (1 + rnd.uniform(-.035, .035))
        pts.append((cx * k + rr * math.cos(t), cy * k + rr * math.sin(t)))
    d = smooth_closed(pts)
    if overshoot:                                                            # the pen runs past where it started
        x, y = pts[1]
        d += f" Q {pts[0][0] + .02 * W:.1f} {pts[0][1] - .01 * W:.1f} {x + .03 * W:.1f} {y + .015 * W:.1f}"
    return d


def arrow(x0, y0, x1, y1, kind, bend, W, sw):
    """A hand arrow from (x0, y0) to (x1, y1) with its head along the final tangent."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), (x1 - x0)
    L = math.hypot(nx, ny) or 1
    cx, cy = mx + nx / L * bend * W, my + ny / L * bend * W
    if kind == "straight":
        d = f"M {x0:.1f} {y0:.1f} L {x1:.1f} {y1:.1f}"
        tx, ty = x1 - x0, y1 - y0
    elif kind == "loop":
        r = .022 * W
        lx, ly = cx, cy
        d = (f"M {x0:.1f} {y0:.1f} Q {(x0 + lx) / 2:.1f} {(y0 + ly) / 2 - r:.1f} {lx:.1f} {ly:.1f} "
             f"c {r:.1f} {-r:.1f} {2 * r:.1f} {r * .2:.1f} {r * .6:.1f} {r:.1f} "
             f"c {-r * .6:.1f} {r * .5:.1f} {-r * 1.4:.1f} {-r * .3:.1f} {-r * .3:.1f} {-r * .9:.1f} "
             f"Q {(lx + x1) / 2:.1f} {(ly + y1) / 2 + r:.1f} {x1:.1f} {y1:.1f}")
        tx, ty = x1 - (lx + x1) / 2, y1 - ((ly + y1) / 2 + r)
    else:
        d = f"M {x0:.1f} {y0:.1f} Q {cx:.1f} {cy:.1f} {x1:.1f} {y1:.1f}"
        tx, ty = x1 - cx, y1 - cy
    t = math.atan2(ty, tx)
    h = max(.018 * W, 4 * sw)
    head = (f"M {x1 - h * math.cos(t - .5):.1f} {y1 - h * math.sin(t - .5):.1f} L {x1:.1f} {y1:.1f} "
            f"L {x1 - h * math.cos(t + .5):.1f} {y1 - h * math.sin(t + .5):.1f}")
    dash = f' stroke-dasharray="0.1 {2.6 * sw:.1f}"' if kind == "dotted" else ""
    return f'<path class="ln" d="{d}"{dash}/><path class="ln" d="{head}"/>'


ORNAMENTS = {   # unit box -1..1, drawn with the line style
    "star": "M 0 -1 L .25 -.3 L 1 -.3 L .4 .15 L .6 .9 L 0 .45 L -.6 .9 L -.4 .15 L -1 -.3 L -.25 -.3 Z",
    "sparkle": "M 0 -1 Q .1 -.1 1 0 Q .1 .1 0 1 Q -.1 .1 -1 0 Q -.1 -.1 0 -1 Z",
    "heart": "M 0 .85 C -1.1 .05 -.8 -.95 0 -.35 C .8 -.95 1.1 .05 0 .85 Z",
    "flower": ("M 0 -.2 C -.35 -1 .35 -1 0 -.2 M .2 0 C 1 -.35 1 .35 .2 0 M 0 .2 C .35 1 -.35 1 0 .2 "
               "M -.2 0 C -1 .35 -1 -.35 -.2 0 M .12 0 A .12 .12 0 1 1 -.12 0 A .12 .12 0 1 1 .12 0"),
    "swirl": "M 0 0 C .3 0 .3 -.4 0 -.4 C -.5 -.4 -.6 .3 0 .4 C .7 .5 .9 -.4 .5 -.8 C .2 -1.1 -.6 -1 -.9 -.4",
    "leaves": "M -.2 .8 C -.9 .2 -.6 -.6 -.1 -.9 C 0 -.3 .1 .3 -.2 .8 Z M .35 .7 C .2 .1 .5 -.4 .95 -.45 C .9 .1 .7 .5 .35 .7 Z",
    "dots": "M -.8 0 L -.79 0 M 0 0 L .01 0 M .8 0 L .81 0",
}
NOTES = ("M -.55 .55 L -.55 -.75 L .65 -.95 L .65 .35 M -.55 -.45 L .65 -.65 "
         "M -.87 .55 a .32 .22 -20 1 0 .64 0 a .32 .22 -20 1 0 -.64 0 M .33 .35 a .32 .22 -20 1 0 .64 0 a .32 .22 -20 1 0 -.64 0")



def figure(pose):
    """A monoline person in a 100-unit box; (0, 0) is the seat (sit) or the feet (wave, peek)."""
    if pose == "sit":
        return ("M 0 -62 m -11 0 a 11 11 0 1 0 22 0 a 11 11 0 1 0 -22 0 "              # head
                "M -12 -66 Q 0 -78 12 -66 L 20 -64 "                                   # cap
                "M 0 -51 L -2 -18 Q -1 -4 8 0 "                                        # back to the seat
                "M -1 -44 L -22 -30 L -26 -10 M 1 -44 L 18 -32 L 22 -14 "             # arms back on the edge
                "M 6 0 L 24 2 L 22 32 L 30 34 M -2 -4 L 10 6 L 6 34 L 14 36")         # legs over the edge, shoes
    if pose == "peek":
        return ("M 0 -22 m -12 0 a 12 12 0 1 0 24 0 a 12 12 0 1 0 -24 0 "
                "M -7 -24 L -6 -23 M 6 -24 L 7 -23 "
                "M -26 0 q 4 -10 10 -2 M 26 0 q -4 -10 -10 -2 M -40 0 L 40 0")
    return ("M 0 -88 m -11 0 a 11 11 0 1 0 22 0 a 11 11 0 1 0 -22 0 "                    # wave (standing)
            "M 0 -77 L 0 -36 M 0 -68 L -18 -48 M 0 -68 L 16 -86 L 22 -100 "
            "M 0 -36 L -12 0 M 0 -36 L 12 0 M -12 0 L -20 0 M 12 0 L 20 0")


def build(plan, W, H, base_url, cut_url, mask, rnd):
    col, acc = plan.get("color", "#FFFFFF"), plan.get("accent", "#B9D86A")
    sw = plan.get("stroke", .006) * W
    # "shadow": a soft drop shadow under every mark, as a fraction of the width (owner 2026-10-30), e.g. .004
    sh = plan.get("shadow", 0) * W
    drop = f"drop-shadow({sh * .5:.1f}px {sh:.1f}px {sh * .5:.1f}px rgba(0,0,0,.85))"   # firm, so it shows on dark grounds too
    shadow_css = f" .layer{{filter:{drop}}} .tx{{filter:url(#wob) {drop}}}" if sh else ""
    behind, front = [], []

    def font_css(key, size, color, extra=""):
        fam, wt, st, tt = FONTS.get(key, FONTS["hand"])
        return (f"font-family:{fam};font-weight:{wt};font-style:{st};text-transform:{tt};font-size:{size * W:.1f}px;"
                f"color:{color};{extra}")

    pal = plan.get("palette")
    pal = PALETTES.get(pal, [col]) if isinstance(pal, str) else (pal or [col])
    for i, e in enumerate(plan["elements"]):
        t, c = e["type"], e.get("color", pal[i % len(pal)])
        out = behind if e.get("behind") else front
        if t == "text":
            al = e.get("align", "center")
            tx = {"left": "0", "center": "-50%", "right": "-100%"}[al]
            out.append(f'<div class="tx" style="left:{e["x"] * W:.1f}px;top:{e["y"] * H:.1f}px;text-align:{al};'
                       f'transform:translate({tx},-50%) rotate({e.get("rotate", 0)}deg);'
                       f'{font_css(e.get("font", "script"), e.get("size", .08), c, "line-height:" + str(e.get("lh", 1.0)))}">'
                       f'{html.escape(e["text"]).replace(chr(10), "<br>")}</div>')
        elif t == "arc":
            cx, cy, r = e["cx"] * W, e["cy"] * H, e["r"] * W
            a0, a1 = math.radians(e.get("from", -60) - 90), math.radians(e.get("to", 60) - 90)
            pid = f"arc{len(behind) + len(front)}"
            fam, wt, st, tt = FONTS.get(e.get("font", "serif"))
            out.append(f'<svg class="layer" viewBox="0 0 {W} {H}"><defs><path id="{pid}" d="M {cx + r * math.cos(a0):.1f} '
                       f'{cy + r * math.sin(a0):.1f} A {r:.1f} {r:.1f} 0 0 1 {cx + r * math.cos(a1):.1f} {cy + r * math.sin(a1):.1f}"/>'
                       f'</defs><text style="font-family:{fam};font-weight:{wt};font-style:{st};font-size:{e.get("size", .12) * W:.1f}px" '
                       f'fill="{c}"><textPath href="#{pid}" startOffset="50%" text-anchor="middle">{html.escape(e["text"])}'
                       f'</textPath></text></svg>')
        elif t == "label":
            x, y = e["x"] * W, e["y"] * H
            size = e.get("size", .045)
            out.append(f'<div class="tx" style="left:{x:.1f}px;top:{y:.1f}px;transform:translate(-50%,-50%) rotate({e.get("rotate", 0)}deg);'
                       f'text-align:center;{font_css(e.get("font", "caps"), size, c, "line-height:1.05")}">'
                       f'{html.escape(e["text"]).replace(chr(10), "<br>")}</div>')
            tx, ty = e["to"][0] * W, e["to"][1] * H
            lines = e["text"].split("\n")
            hw = max(len(s) for s in lines) * size * W * .27 + .01 * W
            hh = len(lines) * size * W * .55 + .008 * W
            ang = math.atan2(ty - y, tx - x)                                    # leave the label box toward the target
            s = min(hw / (abs(math.cos(ang)) or 1e-6), hh / (abs(math.sin(ang)) or 1e-6))
            gap = .012 * W
            ex, ey = tx - (gap * math.cos(ang)), ty - (gap * math.sin(ang))
            front.append(f'<svg class="layer" viewBox="0 0 {W} {H}" style="color:{c}">'
                         f'{arrow(x + s * math.cos(ang), y + s * math.sin(ang), ex, ey, e.get("arrow", "curve"), e.get("bend", .05), W, sw)}</svg>')
        elif t == "outline":
            if mask is None:
                sys.exit("outline needs the subject mask")
            d = outline_path(mask, W, e.get("pad", .03), e.get("overshoot", True), rnd, e.get("region"), e.get("round", .6))
            dash = f' stroke-dasharray="{4 * sw:.1f} {3 * sw:.1f}"' if e.get("dashed") else ""
            out.append(f'<svg class="layer" viewBox="0 0 {W} {H}" style="color:{c}"><path class="ln" d="{d}"{dash}/></svg>')
        elif t == "svg":   # raw SVG in photo pixels (viewBox 0 0 W H); class "ln" gives the hand line and wobble
            out.append(f'<svg class="layer" viewBox="0 0 {W} {H}" style="color:{c}">{e["content"]}</svg>')
        elif t == "ornament":
            s = e.get("size", .025) * W
            shape = ORNAMENTS[e["shape"]] if e["shape"] != "notes" else NOTES   # notes used to draw nothing ("None")
            g = (f'<g transform="translate({e["x"] * W:.1f} {e["y"] * H:.1f}) rotate({e.get("rotate", 0)}) scale({s:.2f})">'
                 f'<path class="ln" style="stroke-width:{sw / s:.3f}{";fill:currentColor" if e.get("fill") else ""}" d="{shape}"/></g>')
            out.append(f'<svg class="layer" viewBox="0 0 {W} {H}" style="color:{c}">{g}</svg>')
        elif t in ("bubble", "capsule"):
            size = e.get("size", .045)
            radius = "999px" if t == "capsule" else "50%"
            border = f'{sw:.1f}px {"dashed" if e.get("dashed", t == "capsule") else "solid"} {c}'
            pad = f'{size * W * .45:.1f}px {size * W * .9:.1f}px'
            out.append(f'<div class="tx" style="left:{e["x"] * W:.1f}px;top:{e["y"] * H:.1f}px;transform:translate(-50%,-50%) '
                       f'rotate({e.get("rotate", 0)}deg);border:{border};border-radius:{radius};padding:{pad};text-align:center;'
                       f'{font_css(e.get("font", "caps" if t == "capsule" else "italic"), size, c, "line-height:1.05")}">'
                       f'{html.escape(e["text"]).replace(chr(10), "<br>")}</div>')
            if t == "bubble":
                bx, by = e["x"] * W, e["y"] * H
                side = -1 if e.get("tail", "left") == "left" else 1
                tl = size * W * 1.1
                front.append(f'<svg class="layer" viewBox="0 0 {W} {H}" style="color:{c}"><path class="ln" d="M {bx + side * tl * .55:.1f} '
                             f'{by + tl * .62:.1f} L {bx + side * tl * .3:.1f} {by + tl * 1.1:.1f} L {bx + side * tl * .1:.1f} {by + tl * .7:.1f}"/></svg>')
        elif t == "ground":
            x, y, w = e["x"] * W, e["y"] * H, e.get("w", .2) * W
            strokes = "".join(f'<path class="ln" d="M {x + w / 2 * math.cos(a):.1f} {y + w * .18 * math.sin(a):.1f} '
                              f'l {w * .05 * math.cos(a):.1f} {w * .05 * math.sin(a) * .6:.1f}"/>'
                              for a in [math.radians(v) for v in (20, 55, 90, 125, 160)])
            out.append(f'<svg class="layer" viewBox="0 0 {W} {H}" style="color:{c}">{strokes}</svg>')
        elif t == "figure":
            s = e.get("size", .2) * W / 100
            g = (f'<g transform="translate({e["x"] * W:.1f} {e["y"] * H:.1f}) scale({s:.3f})">'
                 f'<path class="ln" style="stroke-width:{sw / s:.3f}" d="{figure(e.get("pose", "sit"))}"/></g>')
            (front if e.get("front", True) else behind).append(f'<svg class="layer" viewBox="0 0 {W} {H}" style="color:{c}">{g}</svg>')
        elif t == "wave":
            y, amp = e.get("y", .1) * H, e.get("amp", .02) * W
            d = f"M 0 {y:.1f} " + " ".join(f"Q {(i + .5) * W / 6:.1f} {y + (amp if i % 2 else -amp):.1f} {(i + 1) * W / 6:.1f} {y:.1f}" for i in range(6))
            d2 = f"M 0 {y + amp * .8:.1f} " + " ".join(f"Q {(i + .5) * W / 5:.1f} {y + amp * .8 + (-amp if i % 2 else amp):.1f} {(i + 1) * W / 5:.1f} {y + amp * .8:.1f}" for i in range(5))
            notes = ""
            for k in range(e.get("notes", 3)):
                nx, ny, h = W * (.38 + .09 * k), y - amp * (1.5 + (k % 2)), amp * 2.4
                notes += (f'<path class="ln" d="M {nx:.1f} {ny:.1f} l 0 {-h:.1f} l {h * .5:.1f} {h * .2:.1f} l 0 {h * .3:.1f}"/>'
                          f'<ellipse class="ln" cx="{nx - amp * .35:.1f}" cy="{ny:.1f}" rx="{amp * .4:.1f}" ry="{amp * .28:.1f}"/>')
            front.append(f'<svg class="layer" viewBox="0 0 {W} {H}" style="color:{c}"><path class="ln" d="{d}"/>'
                         f'<path class="ln" style="color:{acc};stroke:{acc}" d="{d2}"/>{notes}</svg>')
        else:
            sys.exit(f"unknown element type: {t}")

    wob = .0018 * W
    cut_html = f'<img class="full" src="{cut_url}">' if cut_url else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{FONT_LINK}">
<style>*{{margin:0;box-sizing:border-box}} html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#000}}
.full{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}} .layer{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;overflow:visible}}
.tx{{position:absolute;white-space:nowrap;filter:url(#wob)}} .ln{{fill:none;stroke:currentColor;stroke-width:{sw:.2f};stroke-linecap:round;stroke-linejoin:round;filter:url(#wob)}}{shadow_css}</style>
</head><body><svg width="0" height="0" style="position:absolute"><filter id="wob"><feTurbulence type="fractalNoise" baseFrequency="{3 / W:.5f}" numOctaves="2" seed="4"/>
<feDisplacementMap in="SourceGraphic" scale="{wob:.1f}"/></filter></svg>
<img class="full" src="{base_url}">{''.join(behind)}{cut_html}{''.join(front)}</body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photo"); ap.add_argument("plan"); ap.add_argument("--out"); ap.add_argument("--html-only", action="store_true")
    a = ap.parse_args()
    src = pathlib.Path(a.photo).resolve()
    plan = json.loads(pathlib.Path(a.plan).read_text())
    key = hashlib.sha1(f"{src}:{src.stat().st_mtime}".encode()).hexdigest()[:10]
    work = src.parent / ".doodle" / f"{src.stem}-{key}"
    base, (W, H) = load_photo(src, work, plan.get("max_side", 2160))
    els = plan["elements"]
    need_mask = any(e.get("behind") or e["type"] == "outline" for e in els)
    mask = subject_mask(base, work) if need_mask else None
    cut = cutout(base, mask, work) if any(e.get("behind") for e in els) else None
    page = work / "page.html"
    page.write_text(build(plan, W, H, base.name, cut.name if cut else None, mask, random.Random(plan.get("seed", 7))))
    if a.html_only:
        print(page); return
    out = pathlib.Path(a.out).resolve() if a.out else src.with_name(src.stem + "-doodled.png")
    subprocess.run(["node", str(HERE / "shoot.js"), str(page), str(out), str(W), str(H)], check=True)
    print(f"{out}  ({W}x{H})")


if __name__ == "__main__":
    main()
