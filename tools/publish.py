"""Put finished videos where they are posted from, in posting order, and write the queue.

  .venv/bin/python tools/publish.py motion/<group>/<piece>       copy one finished video in, then arrange
  .venv/bin/python tools/publish.py --arrange                    only arrange and rewrite the queue
  .venv/bin/python tools/publish.py --posted <slug> [YYYY-MM-DD] mark a video posted (default today), then arrange

videos/ after arranging (by topic, then part, then version):
  POSTING.md                              the queue in posting order, with status and folder (generated)
  <topic>/<part>/<version>/               for a series, e.g. math-behind-llms/2-embeddings/v2/
  <topic>/<version>/                      for a single video, e.g. prompt-injection/v2/
Each version folder: instagram.mp4, instagram-cover.png, linkedin.mp4, linkedin-cover.png (when there is a 16:9
version), caption.txt, subtitles.srt, and a hidden .meta.json. Posting never moves a folder.

The source of truth is motion/<group>/<piece>/meta.json: "title", "topic", "part" (optional), "version",
"status" (draft | posted | dropped), "order" (place in the queue; new videos go to the end), "posted" (date). Arranging only moves and renames folders and files
in videos/, it never deletes one: some older videos exist only there.
"""
import datetime
import json
import pathlib
import re
import shutil
import sys

STUDIO = pathlib.Path(__file__).resolve().parent.parent
VIDEOS = STUDIO / "videos"
NAMES = {"video.mp4": "instagram.mp4", "video-linkedin.mp4": "linkedin.mp4", "cover-reel.png": "instagram-cover.png",
         "cover-linkedin.png": "linkedin-cover.png", "captions.srt": "subtitles.srt"}


def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower().replace("'", "")).strip("-")


def source_meta(source):
    p = STUDIO / source / "meta.json"
    return (json.loads(p.read_text()), p) if p.exists() else (None, p)


def publish(piece):
    """Copy a piece's finished files into videos/ (under their platform names) with a hidden .meta.json."""
    piece = (STUDIO / piece).resolve()
    m = json.loads((piece / "meta.json").read_text())
    if "order" not in m:   # a new video goes to the end of the queue
        orders = [json.loads(p.read_text()).get("order", 0) for p in STUDIO.glob("motion/*/*/meta.json")]
        m["order"] = max(orders + [0]) + 1
        (piece / "meta.json").write_text(json.dumps(m, indent=1, ensure_ascii=False))
    dest = VIDEOS / "incoming" / m["slug"]
    dest.mkdir(parents=True, exist_ok=True)
    missing = []
    for name, src in m["files"].items():
        s = piece / src
        if s.exists():
            shutil.copy2(s, dest / NAMES.get(name, name))
        else:
            missing.append(src)
    if m.get("caption"):
        (dest / "caption.txt").write_text(m["caption"] + "\n")
    meta = {k: v for k, v in m.items() if k != "files"}
    meta["source"] = str(piece.relative_to(STUDIO))
    (dest / ".meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print(f"published {m['slug']}" + (f"  (missing: {', '.join(missing)})" if missing else ""))


def arrange():
    """Move every video folder to to-post/NN-title or posted/date-title, rename legacy files, write POSTING.md."""
    found = []
    for meta in list(VIDEOS.rglob(".meta.json")) + list(VIDEOS.rglob("meta.json")):
        d = meta.parent
        if meta.name == "meta.json":   # an older folder: hide its meta
            meta = meta.rename(d / ".meta.json")
        m = json.loads(meta.read_text())
        src, _ = source_meta(m["source"])
        if src:   # the source is the truth for status, order, posted date and title
            for k in ("status", "order", "posted", "title", "series", "topic", "part", "version"):
                if k in src:
                    m[k] = src[k]
            meta.write_text(json.dumps(m, indent=1, ensure_ascii=False))
        for old, new in NAMES.items():
            if (d / old).exists():
                (d / old).rename(d / new)
        found.append((m, d))
    queue = sorted((x for x in found if x[0].get("status") not in ("posted", "dropped")), key=lambda x: (x[0].get("order", 999), x[0].get("date", "")))
    posted = sorted((x for x in found if x[0].get("status") == "posted"), key=lambda x: x[0].get("posted", ""), reverse=True)
    place = lambda m: VIDEOS / m.get("topic", slugify(m["title"])) / (m.get("part") or "") / m.get("version", "v1")
    rows_q = [(i, m, move(d, place(m))) for i, (m, d) in enumerate(queue, 1)]
    rows_p = [(m, move(d, place(m))) for m, d in posted]
    for d in sorted(VIDEOS.rglob("*"), key=lambda p: -len(p.parts)):   # folders left empty by the moves
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    write_queue(rows_q, rows_p)
    print(f"videos/: {len(rows_q)} to post, {len(rows_p)} posted (see videos/POSTING.md)")


def move(d, target):
    if d.resolve() != target.resolve():
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            sys.exit(f"cannot move {d} to {target}: it already exists")
        d.rename(target)
    return target


def write_queue(rows_q, rows_p):
    def files(d):
        li = "yes (16:9)" if (d / "linkedin.mp4").exists() else "no: post instagram.mp4 there or skip"
        return li
    rel = lambda d: str(d.relative_to(VIDEOS))
    out = ["# Posting queue", "",
           "Post one a day, top first. Each folder has instagram.mp4 + instagram-cover.png, linkedin.mp4 +",
           "linkedin-cover.png (when there is a 16:9 version) and caption.txt (same caption on both).",
           "After posting, run `.venv/bin/python tools/publish.py --posted <slug>` (or tell Claude); this file is",
           "rewritten. Generated by tools/publish.py from each video's meta.json; do not edit by hand.", "",
           "## To post", "", "| # | Video | Folder | LinkedIn version |", "|---|---|---|---|"]
    out += [f"| {i} | {m['title']} | `{rel(d)}` | {files(d)} |" for i, m, d in rows_q]
    out += ["", "## Posted", "", "| Date | Video | Folder |", "|---|---|---|"]
    out += [f"| {m.get('posted', '')} | {m['title']} | `{rel(d)}` |" for m, d in rows_p]
    (VIDEOS / "POSTING.md").write_text("\n".join(out) + "\n")


def mark_posted(name, date):
    for meta in VIDEOS.rglob(".meta.json"):
        m = json.loads(meta.read_text())
        if name in (m["slug"], str(meta.parent.relative_to(VIDEOS))):
            src, p = source_meta(m["source"])
            target = src if src else m
            target["status"], target["posted"] = "posted", date
            (p if src else meta).write_text(json.dumps(target, indent=1, ensure_ascii=False))
            print(f"marked posted {date}: {m['title']}")
            return
    sys.exit(f"no video called {name!r} in videos/")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--posted"]:
        mark_posted(args[1], args[2] if len(args) > 2 else datetime.date.today().isoformat())
    elif args[:1] != ["--arrange"]:
        for t in args:
            publish(t)
    arrange()
