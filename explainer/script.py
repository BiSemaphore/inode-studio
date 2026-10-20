"""script.md: one readable file per video, compiled into beats.json and meta.json.

    ---
    title: One character, wrong entry
    slug: ep02-one-character-wrong-entry      # folder name under videos/<group>/
    group: explainers
    series: learn by building · ep 2
    date: 2026-10-20
    status: approved
    theme: whiteboard
    voice: af_heart
    speed: 1.0
    lead: 1.4                                 # silence before the first line (intro card)
    intro: One character, | wrong entry       # the two headline lines of the opening card
    pronounce: inode=eye-node, Ollama=/oʊlˈɑːmə/   # respelling, or exact phonemes in slashes
    caption: |
      One character deleted the wrong entry.
      ...
    ---

    ## hook
    Sheldon meant to delete one old entry. He deleted Howard's production rollback runbook instead.
    pause: 0.6

    ## what
    He typed: note delete 3. It asked: delete note 3? He said yes.
    say: He typed: note delete three. It asked: delete note three? He said yes.

Each `## id` is a beat. Its text is the subtitle; the voice reads the same text
with `pronounce` applied, unless a `say:` line gives the spoken form (numbers
the voice should read as words, for example). `pause:` is the silence after the
beat (default 0.5 s).

    .venv/bin/python explainer/script.py motion/<group>/<piece>    # compile (story.py does this itself)
"""
import json
import pathlib
import re
import sys


def parse(text):
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise SystemExit("script.md must start with a --- front matter block")
    fm, body = m.groups()
    meta, key = {}, None
    for line in fm.split("\n"):
        if key and (line.startswith("  ") or not line.strip()):
            meta[key] += line[2:] + "\n"
            continue
        key = None
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        k, _, v = line.partition(":")
        v = re.sub(r"\s+#.*$", "", v).strip()
        if v == "|":
            key, meta[k.strip()] = k.strip(), ""
        else:
            meta[k.strip()] = v
    if "caption" in meta:
        meta["caption"] = meta["caption"].rstrip("\n")
    beats = []
    for block in re.split(r"^## ", body, flags=re.M)[1:]:
        lines = block.strip().split("\n")
        bid, rest = lines[0].strip(), [ln for ln in lines[1:] if ln.strip()]
        say = next((ln[4:].strip() for ln in rest if ln.startswith("say:")), None)
        pause = next((float(ln[6:]) for ln in rest if ln.startswith("pause:")), 0.5)
        show = " ".join(ln.strip() for ln in rest if not re.match(r"(say|pause):", ln))
        beats.append({"id": bid, "show": show, "say": say, "pause": pause})
    return meta, beats


def spoken(show, pronounce):
    """The text the voice reads. A pronounce value is either a respelling
    ("inode=eye-node") or exact phonemes between slashes ("Ollama=/oʊlˈɑːmə/"),
    which become a [[word|phonemes]] marker that voice.py speaks verbatim."""
    out = show
    for word, said in pronounce.items():
        rep = f"[[{word}|{said.strip('/')}]]" if said.startswith("/") and said.endswith("/") else said
        out = re.sub(rf"(?<![\w-]){re.escape(word)}(?![\w-])", lambda m: rep, out)
    return out


def compile_piece(piece):
    piece = pathlib.Path(piece)
    meta, beats = parse((piece / "script.md").read_text())
    pron = dict(p.split("=", 1) for p in (x.strip() for x in meta.get("pronounce", "").split(",")) if "=" in p)
    out = {"voice": meta.get("voice", "af_heart"), "speed": float(meta.get("speed", 1.0)), "lead": float(meta.get("lead", 1.0)),
           "beats": [{"id": b["id"], "say": b["say"] or spoken(b["show"], pron), "show": b["show"], "pause": b["pause"]} for b in beats]}
    (piece / "beats.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    name = piece.name
    files = {"video.mp4": f"out/{name}.mp4", "cover-linkedin.png": "out/cover-linkedin.png",
             "cover-reel.png": "out/cover-reel.png", "captions.srt": f"{name}.srt"}
    m = {k: meta[k] for k in ("group", "slug", "title", "series", "date", "status") if k in meta}
    m["files"] = files
    if "caption" in meta:
        m["caption"] = meta["caption"]
    (piece / "meta.json").write_text(json.dumps(m, indent=1, ensure_ascii=False))
    intro = [x.strip() for x in meta["intro"].split("|")] if "intro" in meta else None
    return {"theme": meta.get("theme", "whiteboard"), "title": meta.get("title", name), "series": meta.get("series", ""),
            "intro": intro, "lead": out["lead"]}


if __name__ == "__main__":
    print(json.dumps(compile_piece(sys.argv[1]), indent=1, ensure_ascii=False))
