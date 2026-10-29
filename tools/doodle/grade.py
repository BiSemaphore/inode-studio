"""Match one photo's colour grade onto others, and save it as a reusable preset (.cube LUT).

  .venv/bin/python tools/doodle/grade.py match <reference> <out.cube> [--from <photo> ...] [--strength 0.7]
  .venv/bin/python tools/doodle/grade.py apply <in> <out> <preset.cube>

match: measures the reference in Lab (per-channel mean and spread, plus its tone curve per channel) and writes a
33-point 3D LUT that moves any neutral, average photo toward that look. The LUT is built against a broad neutral
target, so it works as a preset on new photos too (not only on the ones it was fitted with). apply: runs a .cube
on an image (HEIC is converted first). The same .cube works in Lightroom, CapCut, VN, DaVinci and ffmpeg (lut3d).
"""
import argparse
import pathlib
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageOps

N = 33


def load(path, max_side=1600):
    path = pathlib.Path(path)
    if path.suffix.lower() in (".heic", ".heif"):
        tmp = pathlib.Path(tempfile.mkdtemp()) / "in.jpg"
        subprocess.run(["sips", "-s", "format", "jpeg", str(path), "--out", str(tmp)], check=True, capture_output=True)
        path = tmp
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    if max_side:
        im.thumbnail((max_side, max_side))
    return np.asarray(im, dtype=np.float64) / 255


# sRGB <-> Lab (D65)
M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
WP = np.array([0.95047, 1.0, 1.08883])


def to_lab(rgb):
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    xyz = c @ M.T / WP
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def from_lab(lab):
    fy = (lab[..., 0] + 16) / 116
    fx, fz = fy + lab[..., 1] / 500, fy - lab[..., 2] / 200
    f = np.stack([fx, fy, fz], -1)
    xyz = np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) / (24389 / 27)) * WP
    c = xyz @ np.linalg.inv(M).T
    c = np.clip(c, 0, 1)
    return np.clip(np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055), 0, 1)


# a neutral, average photo: what the preset is fitted against, so it transfers to new pictures
NEUTRAL = {"mean": np.array([55.0, 2.0, 8.0]), "std": np.array([22.0, 8.0, 12.0])}


def stats(lab):
    flat = lab.reshape(-1, 3)
    return {"mean": flat.mean(0), "std": flat.std(0) + 1e-6,
            "q": np.percentile(flat[:, 0], np.linspace(0, 100, 33))}


def build_lut(ref_lab, strength, src=None):
    """3D LUT: map each Lab colour from the neutral statistics to the reference statistics, with the reference's
    own tone curve on lightness, blended by strength."""
    r = stats(ref_lab)
    src = src or NEUTRAL
    # chroma spread never grows past the source by more than 25 percent (avoids the colour blowing out)
    r["std"] = np.minimum(r["std"], src["std"] * np.array([1.6, 1.25, 1.25]))
    g = np.linspace(0, 1, N)
    b_, g_, r_ = np.meshgrid(g, g, g, indexing="ij")
    rgb = np.stack([r_, g_, b_], -1)                       # .cube order: red changes fastest
    lab = to_lab(rgb)
    out = (lab - src["mean"]) / src["std"] * r["std"] + r["mean"]
    # lightness: the reference's percentile curve, so blacks, mids and highlights land where the reference has them
    z = np.clip((lab[..., 0] - src["mean"][0]) / src["std"][0], -2.5, 2.5)
    pct = 50 * (1 + np.tanh(z * 0.85))                      # smooth position of each lightness in a neutral photo
    out[..., 0] = np.interp(pct, np.linspace(0, 100, 33), r["q"])
    out = lab + strength * (out - lab)
    out[..., 0] = np.clip(out[..., 0], 0, 100)
    return from_lab(out)


def write_cube(lut, path, title):
    with open(path, "w") as f:
        f.write(f'TITLE "{title}"\nLUT_3D_SIZE {N}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        for row in lut.reshape(-1, 3):
            f.write(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}\n")


def read_cube(path):
    rows = [l.split() for l in open(path) if l[:1].isdigit() or l[:1] == "-" or (l[:1] == "." )]
    rows = [r for r in rows if len(r) == 3]
    return np.array(rows, dtype=np.float64).reshape(N, N, N, 3)


def apply_lut(img, lut):
    """Trilinear lookup; lut indexed [b, g, r]."""
    x = img * (N - 1)
    i0 = np.clip(np.floor(x).astype(int), 0, N - 2)
    d = x - i0
    r0, g0, b0 = i0[..., 0], i0[..., 1], i0[..., 2]
    dr, dg, db = d[..., 0:1], d[..., 1:2], d[..., 2:3]
    c = lambda bb, gg, rr: lut[b0 + bb, g0 + gg, r0 + rr]
    c00 = c(0, 0, 0) * (1 - dr) + c(0, 0, 1) * dr
    c01 = c(0, 1, 0) * (1 - dr) + c(0, 1, 1) * dr
    c10 = c(1, 0, 0) * (1 - dr) + c(1, 0, 1) * dr
    c11 = c(1, 1, 0) * (1 - dr) + c(1, 1, 1) * dr
    return (c00 * (1 - dg) + c01 * dg) * (1 - db) + (c10 * (1 - dg) + c11 * dg) * db


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("match"); m.add_argument("reference"); m.add_argument("out"); m.add_argument("--strength", type=float, default=.7); m.add_argument("--from", dest="src", nargs="*", default=[])
    a = sub.add_parser("apply"); a.add_argument("src"); a.add_argument("out"); a.add_argument("cube")
    args = ap.parse_args()
    if args.cmd == "match":
        src = None
        if args.src:   # fit the source look on the photos the preset will mostly be used on
            labs = np.concatenate([to_lab(load(f, 800)).reshape(-1, 3) for f in args.src])
            src = {"mean": labs.mean(0), "std": labs.std(0) + 1e-6}
        lut = build_lut(to_lab(load(args.reference)), args.strength, src)
        write_cube(lut, args.out, pathlib.Path(args.out).stem)
        print(args.out)
    else:
        img = load(args.src, max_side=None)
        out = apply_lut(img, read_cube(args.cube))
        Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8)).save(args.out, quality=94)
        print(args.out)


if __name__ == "__main__":
    main()
