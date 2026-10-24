"""Start a new video from a theme (list them with tools/themes.py; ask the owner which one).

  .venv/bin/python tools/new_piece.py shorts/attention-01 --theme card --title "How each word looks at every word"

Creates motion/<group>/<slug>/ with page.html (the theme's template), beats.json (one placeholder beat),
meta.json (draft, both shapes: Instagram 1080x1920 and LinkedIn 1920x1080) and run/ for a local measurement.
Refuses to touch a folder that already exists.
"""
import argparse
import datetime
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
THEMES = ROOT / "explainer/frames/themes"

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("piece", help="<group>/<slug>, for example shorts/attention-01")
ap.add_argument("--theme", required=True, help="a folder in explainer/frames/themes with a template")
ap.add_argument("--title", default="")
a = ap.parse_args()

theme = json.loads((THEMES / a.theme / "theme.json").read_text())
if not theme.get("template"):
    sys.exit(f"theme {a.theme!r} has no template; pick another (tools/themes.py)")
group, slug = a.piece.split("/")
d = ROOT / "motion" / group / slug
if d.exists():
    sys.exit(f"{d} already exists")
(d / "run").mkdir(parents=True)

page = (ROOT / "explainer/frames" / theme["template"]).read_text().replace("<title>TITLE</title>", f"<title>{a.title or slug}</title>")
(d / "page.html").write_text(page)
(d / "beats.json").write_text(json.dumps({"voice": "af_heart", "speed": 1.0, "lead": 0.4, "beats": [
    {"id": "hook", "show": "One short active sentence.", "say": "One short active sentence.", "pause": 0.5}]}, indent=1))
(d / "meta.json").write_text(json.dumps({
    "group": group, "slug": slug, "title": a.title, "date": datetime.date.today().isoformat(), "status": "draft", "theme": a.theme,
    "files": {"video.mp4": f"out/{slug}.mp4", "video-linkedin.mp4": f"out/{slug}-landscape.mp4",
              "cover-reel.png": "out/cover-reel.png", "cover-linkedin.png": "out/cover-linkedin.png", "captions.srt": "captions.srt"},
    "caption": ""}, indent=1, ensure_ascii=False))
print(f"created {d.relative_to(ROOT)} with theme {a.theme!r}: page.html, beats.json, meta.json, run/")
print("next: write beats.json, voice it (explainer/voice.py), verify (tools/verify_voice.py), build page.html")
