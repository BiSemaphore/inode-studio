"""Copy a finished video's files into videos/ and rebuild the index.

  .venv/bin/python tools/publish.py motion/<group>/<piece>     # one video
  .venv/bin/python tools/publish.py --all                     # every piece with a meta.json

Each piece has motion/<group>/<piece>/meta.json:
  {"group", "slug", "title", "date", "status", "series"?, "caption"?,
   "files": {"video.mp4": "out/<piece>.mp4", "cover-linkedin.png": ..., ...}}
videos/<group>/<slug>/ gets those files under their published names, plus
caption.txt; videos/INDEX.md lists every published video. videos/ holds only
what gets posted; sources stay in motion/.
"""
import json
import pathlib
import shutil
import sys

STUDIO = pathlib.Path(__file__).resolve().parent.parent
VIDEOS = STUDIO / "videos"


def publish(piece):
    piece = (STUDIO / piece).resolve() if not pathlib.Path(piece).is_absolute() else pathlib.Path(piece)
    m = json.loads((piece / "meta.json").read_text())
    dest = VIDEOS / m["group"] / m["slug"]
    dest.mkdir(parents=True, exist_ok=True)
    missing = []
    for name, src in m["files"].items():
        s = piece / src
        if s.exists():
            shutil.copy2(s, dest / name)
        else:
            missing.append(src)
    if m.get("caption"):
        (dest / "caption.txt").write_text(m["caption"] + "\n")
    meta = {k: v for k, v in m.items() if k != "files"}
    meta["source"] = str(piece.relative_to(STUDIO))
    (dest / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print(f"published {dest.relative_to(STUDIO)}" + (f"  (missing: {', '.join(missing)})" if missing else ""))


def index():
    rows = []
    for meta in sorted(VIDEOS.glob("*/*/meta.json")):
        m = json.loads(meta.read_text())
        d = meta.parent
        files = ", ".join(f.name for f in sorted(d.iterdir()) if f.name != "meta.json")
        rows.append((m["group"], m.get("date", ""), m["title"], m.get("status", ""), str(d.relative_to(VIDEOS)), files, m["source"]))
    out = ["# Videos", "", "Finished videos, ready to post. Sources are in `motion/` (see `source`).",
           "Regenerate with `.venv/bin/python tools/publish.py --all`.", ""]
    for group in sorted({r[0] for r in rows}):
        out += [f"## {group}", "", "| Date | Title | Status | Folder | Files | Source |", "|---|---|---|---|---|---|"]
        for g, date, title, status, folder, files, src in sorted((r for r in rows if r[0] == group), key=lambda r: r[1], reverse=True):
            out.append(f"| {date} | {title} | {status} | [{folder}]({folder}/) | {files} | `{src}` |")
        out.append("")
    (VIDEOS / "INDEX.md").write_text("\n".join(out))
    print(f"videos/INDEX.md: {len(rows)} videos")


if __name__ == "__main__":
    targets = sorted(p.parent for p in STUDIO.glob("motion/*/*/meta.json")) if sys.argv[1:] == ["--all"] else sys.argv[1:]
    for t in targets:
        publish(t)
    index()
