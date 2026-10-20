"""Compare two folders of peek snapshots (t<sec>.png); report frames that differ
beyond Chrome's own rendering noise (a few pixels).
  .venv/bin/python explainer/compare_frames.py <before> <after>"""
import glob, os, sys
import numpy as np
from PIL import Image
a_dir, b_dir = sys.argv[1:3]
bad = 0
for a in sorted(glob.glob(os.path.join(a_dir, "t*.png"))):
    b = os.path.join(b_dir, os.path.basename(a))
    if not os.path.exists(b):
        print(f"  missing {os.path.basename(b)}"); bad += 1; continue
    x = np.asarray(Image.open(a).convert("L"), dtype=np.int16); y = np.asarray(Image.open(b).convert("L"), dtype=np.int16)
    n = int((np.abs(x - y) > 8).sum()) if x.shape == y.shape else -1
    if n < 0 or n > 40:
        print(f"  DIFFERENT {os.path.basename(a)}: {n} pixels"); bad += 1
print(f"compare: {len(glob.glob(os.path.join(a_dir, 't*.png')))} frames, {bad} different")
sys.exit(1 if bad else 0)
