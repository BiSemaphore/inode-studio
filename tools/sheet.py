"""Tile peek snapshots into a labelled contact sheet.
Usage: .venv/bin/python tools/sheet.py <dir with t*.png> <out.png> [cols] [width]"""
import glob
import os
import sys

from PIL import Image, ImageDraw

d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 5
w = int(sys.argv[4]) if len(sys.argv) > 4 else 432
files = sorted(glob.glob(os.path.join(d, "t*.png")), key=lambda f: float(os.path.basename(f)[1:-4]))
ims = []
for f in files:
    im = Image.open(f).convert("RGB")
    im = im.resize((w, int(im.height * w / im.width)))
    dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, 52, 18], fill="white")
    dr.text((4, 3), os.path.basename(f)[1:-4] + "s", fill="red")
    ims.append(im)
h = ims[0].height
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (w + 4), rows * (h + 4)), "white")
for k, im in enumerate(ims):
    sheet.paste(im, ((k % cols) * (w + 4), (k // cols) * (h + 4)))
sheet.save(out)
print(out, len(ims), "frames")
