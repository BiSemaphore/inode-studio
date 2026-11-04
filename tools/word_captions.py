"""Word-by-word subtitles (owner 2026-11-04, the ref-87 style), timed from the real voice.

    .venv/bin/python tools/word_captions.py motion/<topic>/<part> [--chars 34]

Reads <piece>/voice/timings.json (every caption word with its spoken start and end) and the "keys" list of each beat in
<piece>/beats.json (the words that matter; matched without case or punctuation). Writes the block between
`/* WORD-CAPS */` and `/* END WORD-CAPS */` in <piece>/compositions/film.html:

    const WCAPS = [{"a": show, "b": hide, "lines": [[[word, spoken_at, is_key], ...], [...]]}, ...];

One group is at most two short lines (at most --chars characters each), never across a sentence end. A group appears
when its first word is spoken (all its words faint), each word turns full when it is spoken, and the group hides
exactly when the next one appears, so two groups never show at once. A line never ends on an opening quote.
The film builds the spans from WCAPS (see the hyperframes film template in motion/how-ai-works/02-hallucination).
Run it after every voice change, together with tools/sync_voice_times.py.
"""
import json, re, sys
from pathlib import Path


def norm(w):
    return re.sub(r"[^a-z0-9%-]", "", w.lower())


def groups_for(words, chars):
    """Split one beat's words into groups of up to two lines, breaking at sentence ends first."""
    sentences, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r'[.?!]["”]?$', w[0]):
            sentences.append(cur); cur = []
    if cur:
        sentences.append(cur)
    out = []
    for s in sentences:
        lines, line = [], []
        for w in s:
            if line and len(" ".join(x[0] for x in line + [w])) > chars:
                if line[-1][0].startswith(('"', "“")) and len(line) > 1:
                    lines.append(line[:-1]); line = [line[-1]]
                else:
                    lines.append(line); line = []
            line.append(w)
        if line:
            lines.append(line)
        while len(lines) >= 2 and len(" ".join(x[0] for x in lines[-1])) < len(" ".join(x[0] for x in lines[-2])) / 2 \
                and len(lines[-2]) > 1:                     # no orphan: move words down until the two lines balance
            lines[-1].insert(0, lines[-2].pop())
        for k in range(0, len(lines), 2):
            out.append(lines[k:k + 2])
    return out


def main(piece, chars=34):
    piece = Path(piece)
    tm = json.loads((piece / "voice" / "timings.json").read_text())
    beats = json.loads((piece / "beats.json").read_text())["beats"]
    groups = []
    for b, t in zip(beats, tm):
        keys = {norm(k) for k in b.get("keys", [])}
        for g in groups_for(t["words"], chars):
            lines = [[[w, round(s, 3), norm(w) in keys] for w, s, _ in ln] for ln in g]
            groups.append({"a": round(g[0][0][1] - 0.04, 3), "end": round(g[-1][-1][2], 3), "lines": lines})
    for k, g in enumerate(groups):
        nxt = groups[k + 1]["a"] if k + 1 < len(groups) else g["end"] + 0.6
        g["b"] = round(min(nxt, g.pop("end") + 0.7), 3)
    film = piece / "compositions" / "film.html"
    s = film.read_text()
    if "/* WORD-CAPS */" not in s:
        sys.exit("film.html needs a /* WORD-CAPS */ ... /* END WORD-CAPS */ block")
    s = re.sub(r"/\* WORD-CAPS \*/.*?/\* END WORD-CAPS \*/",
               lambda m: "/* WORD-CAPS */\n    const WCAPS = " + json.dumps(groups, ensure_ascii=False) + ";\n    /* END WORD-CAPS */",
               s, flags=re.S)
    film.write_text(s)
    print(f"{len(groups)} caption groups, {sum(len(l) for g in groups for l in g['lines'])} words")


if __name__ == "__main__":
    a = sys.argv[1:]
    chars = int(a[a.index("--chars") + 1]) if "--chars" in a else 34
    main(a[0], chars)
