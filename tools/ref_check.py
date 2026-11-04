"""Reference check: do my frames use the reference's colours, and do they look like it side by side?

    .venv/bin/python tools/ref_check.py <reference image> <frame.png|video.mp4> [more frames ...]
                     [--allow F7F3DA,FFFFFF,E8483B] [--times 2,20,40] [--out sheet.jpg] [--max-off 2.0]

1. Palette: the reference is reduced to its 16 main colours (k-means in Lab). Every pixel of every frame is matched
   to the nearest reference colour (or an allowed brand colour). A pixel is "off-palette" when it is more than
   deltaE 18 away from all of them and visibly coloured (chroma above 12). A frame FAILS when more than --max-off
   percent of it is off-palette (default 2%). The report lists the worst off-palette colours, so a lime pill on cobalt
   or a green card on blue shows up by name.
2. Side by side: the reference and the frames in one sheet (--out), to look at before showing anything to the owner.
Exit code 1 if any frame fails. Used by tools/qa.py when <piece>/BRIEF.md has a line "Reference: <path>".
"""
import subprocess, sys, tempfile
from pathlib import Path

import numpy as np
from PIL import Image


def to_lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def pixels(img, side=160):
    im = img.convert("RGB")
    im.thumbnail((side, side * 2))
    return np.asarray(im, dtype=float).reshape(-1, 3)


def palette(ref, k=16, iters=12):
    lab = to_lab(pixels(ref, 200))
    rng = np.random.default_rng(0)
    cent = lab[rng.choice(len(lab), k, replace=False)]
    for _ in range(iters):
        lab_d = ((lab[:, None, :] - cent[None]) ** 2).sum(-1)
        lbl = lab_d.argmin(1)
        cent = np.array([lab[lbl == j].mean(0) if (lbl == j).any() else cent[j] for j in range(k)])
    return cent


def frames_from(paths, times):
    out = []
    for p in paths:
        p = Path(p)
        if p.suffix.lower() in (".mp4", ".mov", ".webm"):
            for t in times:
                tmp = Path(tempfile.mkdtemp()) / f"f{t}.png"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(p), "-frames:v", "1", str(tmp)], check=True)
                out.append((f"{p.name}@{t}s", Image.open(tmp)))
        else:
            out.append((p.name, Image.open(p)))
    return out


def main(argv):
    args, opts, i = [], {}, 0
    while i < len(argv):
        if argv[i].startswith("--"):
            opts[argv[i][2:]] = argv[i + 1]; i += 2
        else:
            args.append(argv[i]); i += 1
    ref = Image.open(args[0])
    allow = [h for h in opts.get("allow", "F7F3DA,FFFFFF,E8483B").split(",") if h]
    times = [float(t) for t in opts.get("times", "2,20,40").split(",")]
    max_off = float(opts.get("max-off", 2.0))
    cent = palette(ref)
    allowed = to_lab(np.array([[int(h[i:i + 2], 16) for i in (0, 2, 4)] for h in allow], dtype=float))
    refs = np.vstack([cent, allowed])
    frames = frames_from(args[1:], times)
    bad = 0
    for name, img in frames:
        rgb = pixels(img)
        lab = to_lab(rgb)
        d = np.sqrt(((lab[:, None, :] - refs[None]) ** 2).sum(-1)).min(1)
        chroma = np.hypot(lab[:, 1], lab[:, 2])
        off = (d > 18) & (chroma > 12)
        share = 100 * off.mean()
        ok = share <= max_off
        bad += not ok
        worst = ""
        if off.any():
            q = (rgb[off] // 24 * 24).astype(int)
            vals, counts = np.unique(q, axis=0, return_counts=True)
            top = vals[np.argsort(-counts)[:3]]
            worst = "  off-palette: " + ", ".join("#%02X%02X%02X" % tuple(v) for v in top)
        print(f"{'PASS' if ok else 'FAIL'}  {name:28s} {share:5.1f}% off the reference palette{worst}")
    if "out" in opts:
        h = 960
        tiles = [ref.convert("RGB").resize((int(ref.width * h / ref.height), h))] + [im.convert("RGB").resize((int(im.width * h / im.height), h)) for _, im in frames]
        sheet = Image.new("RGB", (sum(t.width for t in tiles), h), (20, 20, 20))
        x = 0
        for t in tiles:
            sheet.paste(t, (x, 0)); x += t.width
        sheet.save(opts["out"], quality=90)
        print(f"side by side (reference first): {opts['out']}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
