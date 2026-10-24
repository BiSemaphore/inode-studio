"""Bake the green paper surface for the card theme's V2 page (owner 2026-10-24: the surface of the
"nobody is coming to save you. get up." pin, brand/references/18-green-get-up-brand.png).

  .venv/bin/python tools/make_surface.py

Our own texture, not the pin's pixels: fine grain, short paper fibres (mostly sideways), and soft
and broad mottle, on the pin's measured colour.
The amplitudes are a least-squares fit so that, measured at the pin's scale (the standard
deviation left after Gaussian blurs of 1, 3, 8, 20 and 50 px), the texture matches it. Writes explainer/frames/themes/card/surface-green.png (1080x1920) and
surface-green-wide.png (1920x1080), and prints both fits.
"""
import pathlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
REF = ROOT / "brand/references/18-green-get-up-brand.png"
OUT = ROOT / "explainer/frames/themes/card"
BLURS = [1, 3, 8, 20, 50]
# layers: fine grain (cell 1 px), paper fibres, soft mottle (90 x 60 px cells), broad mottle (300 x 220)
SCALES = [(1, 1), "fibre", (90, 60), (300, 220)]
PIN_PER_PX = 736 / 1080          # the pin is 736 px wide where our screen is 1080: same grain size on screen


def profile(lum, gain=1.0):
    """Std left after each blur, measured at the pin's scale. gain lifts sub-level detail above 8-bit rounding."""
    w = round(lum.shape[1] * PIN_PER_PX); h = round(lum.shape[0] * PIN_PER_PX)
    img = Image.fromarray(np.clip(128 + (lum - lum.mean()) * gain, 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    return np.array([np.asarray(img.filter(ImageFilter.GaussianBlur(r)), float).std() for r in BLURS]) / gain


def layers(w, h, seed=11):
    rng = np.random.default_rng(seed)
    out = []
    for spec in SCALES:
        if spec == "fibre":
            # short thin strokes like the pin's paper: sideways or up-down (few at other angles), half lighter, half darker
            img = Image.new("L", (w, h), 128); d = ImageDraw.Draw(img)
            n = w * h // 22
            xs, ys = rng.uniform(0, w, n), rng.uniform(0, h, n)
            r = rng.random(n)
            ang = np.where(r < 0.5, rng.normal(0, 0.2, n), np.where(r < 0.85, rng.normal(np.pi / 2, 0.2, n), rng.uniform(0, np.pi, n)))
            ln, val = rng.uniform(3, 9, n), rng.choice([-1.0, 1.0], n)
            for x, y, a, l, v in zip(xs, ys, ang, ln, val):
                dx, dy = np.cos(a) * l / 2, np.sin(a) * l / 2
                d.line((x - dx, y - dy, x + dx, y + dy), fill=int(128 + 60 * v), width=1)
            a = np.asarray(img.filter(ImageFilter.GaussianBlur(0.6)), np.float32)
            out.append((a - a.mean()) / a.std())
            continue
        sx, sy = spec
        small = rng.standard_normal((max(2, h // sy + 2), max(2, w // sx + 2))).astype(np.float32)
        img = Image.fromarray(small, mode="F").resize((w, h), Image.BICUBIC if sx > 1 else Image.NEAREST)
        a = np.asarray(img, np.float32)
        out.append((a - a.mean()) / a.std())
    return out


ref = np.asarray(Image.open(REF).convert("RGB"), float)[20:420, 20:716]   # plain surface: no text, no figure
colour = ref.reshape(-1, 3).mean(0)
target = np.array([np.asarray(Image.fromarray(ref.mean(2).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), float).std() for r in BLURS])


def bake(w, h, name):
    L = layers(w, h)
    # variances add across independent layers: target^2 = M @ amp^2. Solve for amp^2 >= 0 by exact coordinate
    # descent, each blur weighted by 1/target^2 so every scale counts the same (relative error)
    M = np.stack([profile(l, gain=12) ** 2 for l in L], axis=1) / (target ** 2)[:, None]
    y, a2 = np.ones(len(BLURS)), np.zeros(len(L))
    for _ in range(5000):
        for k in range(len(L)):
            r = y - M @ a2 + M[:, k] * a2[k]
            a2[k] = max(0.0, M[:, k] @ r / (M[:, k] @ M[:, k]))
    amp = np.sqrt(a2)
    dither = np.random.default_rng(3).uniform(-.5, .5, (h, w, 1))
    make = lambda amp: np.clip(colour[None, None, :] + sum(a * l for a, l in zip(amp, L))[..., None] + dither, 0, 255).astype(np.uint8)
    amp *= np.exp(np.mean(np.log(target / profile(make(amp).mean(2).astype(float)))))   # one pass on the real 8-bit output
    rgb = make(amp)
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb).save(OUT / name, optimize=True)
    got = profile(rgb.mean(2).astype(float))
    print(f"{name}: colour #{''.join(f'{round(c):02X}' for c in colour)}  amps {np.round(amp, 2)}\n   pin  {np.round(target, 2)}\n   ours {np.round(got, 2)}")


bake(1080, 1920, "surface-green.png")
bake(1920, 1080, "surface-green-wide.png")
