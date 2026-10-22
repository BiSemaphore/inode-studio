"""Bake the field theme's leaf light into PNGs (studies/21): soft sunlit patches through leaves.

  .venv/bin/python tools/make_leaf.py      -> explainer/frames/themes/field/leaf-<n>.png

Each image is larger than the frame so it can drift. Smooth noise at a few scales is turned
into patches with a soft threshold, then blurred; colour is the sunlit yellow-green.
"""
import pathlib
import numpy as np
from PIL import Image, ImageFilter

OUT = pathlib.Path(__file__).resolve().parent.parent / "explainer/frames/themes/field"
W, H = 1320, 2240

for n, seed in enumerate([11, 23, 37, 41, 53, 67, 79, 83], 1):
    rng = np.random.default_rng(seed)
    field = np.zeros((H, W))
    for scale, weight in ((420, 1.0), (210, 0.5), (105, 0.25)):
        small = rng.random((H // scale + 3, W // scale + 3))
        img = Image.fromarray((small * 255).astype(np.uint8)).resize((W + 3 * scale, H + 3 * scale), Image.BICUBIC)
        field += weight * (np.asarray(img, dtype=float)[:H, :W] / 255)
    field = (field - field.min()) / (field.max() - field.min())
    alpha = 1 / (1 + np.exp(-(field - 0.6) * 14))                      # soft threshold: few, large patches
    a = Image.fromarray((alpha * 200).astype(np.uint8)).filter(ImageFilter.GaussianBlur(30))
    rgba = Image.new("RGBA", (W, H), (116, 178, 102, 0))   # sage, sampled from the approved style frame
    rgba.putalpha(a)
    rgba.save(OUT / f"leaf-{n}.png")
    print(OUT / f"leaf-{n}.png")
