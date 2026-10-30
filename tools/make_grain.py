"""Bake a flat grain surface (owner 2026-10-29: the red of brand/references/62-font-prickly-pear-red-grain.png).
  .venv/bin/python tools/make_grain.py <out_dir> [--color A83A39] [--grain 13] [--name surface]
Our own texture, not the reference's pixels, fitted to its statistics: base #AB3D3C (median), a small per-pixel
jitter, and sparse sharp dark specks (#80 14 13, about 9 percent of pixels), no blur and no mottle. Writes <name>.png (1080x1920) and <name>-wide.png (1920x1080).
"""
import argparse
import pathlib

import numpy as np
from PIL import Image


def bake(w, h, rgb, grain, seed, specks=0.09, speck_rgb=(128, 20, 19)):
    """Flat base with a little per-pixel jitter, then sparse sharp DARK single-pixel specks (the reference's grain is
    skewed dark: about 9 percent of pixels sit 20+ levels under the base, almost none above it; no blur, no mottle)."""
    rng = np.random.default_rng(seed)
    jitter = rng.normal(0, grain * .45, (h, w))
    img = np.clip(np.array(rgb, float)[None, None, :] + jitter[..., None], 0, 255)
    m = rng.random((h, w)) < specks
    depth = rng.uniform(.55, 1.0, (h, w))[..., None]                   # specks vary from mid to full dark
    img = np.where(m[..., None], img * (1 - depth) + np.array(speck_rgb, float) * depth, img)
    return Image.fromarray(img.astype(np.uint8))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out"); ap.add_argument("--color", default="AB3D3C"); ap.add_argument("--grain", type=float, default=13)
    ap.add_argument("--name", default="surface")
    a = ap.parse_args()
    rgb = tuple(int(a.color[i:i + 2], 16) for i in (0, 2, 4))
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    bake(1080, 1920, rgb, a.grain, 1).save(out / f"{a.name}.png", optimize=True)
    bake(1920, 1080, rgb, a.grain, 2).save(out / f"{a.name}-wide.png", optimize=True)
    print(out / f"{a.name}.png", out / f"{a.name}-wide.png")


if __name__ == "__main__":
    main()
