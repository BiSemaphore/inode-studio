"""The theme catalogue: every look a video can use, read from explainer/frames/themes/*/theme.json.

  .venv/bin/python tools/themes.py              list the themes (ask the owner which one before a new video)
  .venv/bin/python tools/themes.py show card    one theme: what it is for, components, variants, load order
  .venv/bin/python tools/themes.py open         open every theme's preview image (macOS)
  .venv/bin/python tools/themes.py check        every listed file exists and every template loads exactly its theme

A theme is a folder with theme.json, its CSS/JS/assets and template.html. It extends one other theme
(base at the bottom) and never reaches into a theme it does not extend.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FRAMES = ROOT / "explainer/frames"
THEMES = FRAMES / "themes"


def themes():
    return {p.parent.name: json.loads(p.read_text()) for p in sorted(THEMES.glob("*/theme.json"))}


def lst(T):
    print(f"{'theme':10s} {'status':45s} use for")
    for name, t in T.items():
        print(f"{name:10s} {t['status'][:44]:45s} {t['use_for']}")
        if t.get("example"):
            print(f"{'':10s} {'':45s} example: {t['example']}   preview: {t.get('preview')}")


def show(t):
    print(f"{t['title']} ({t['name']}): {t['status']}\n{t['use_for']}\nextends: {t['extends']}")
    print("load:", " -> ".join([*t["load"]["css"], *t["load"]["js_before_runtime"], "runtime.js", *t["load"]["js_after_runtime"]]))
    for k, v in t["components"].items():
        print(f"  {k:8s} {v}")
    for k, v in t["variants"].items():
        print(f"  variant {k}: {v}")
    print("template:", t["template"], "  example:", t["example"])


def check(T):
    bad = []
    for name, t in T.items():
        L = t["load"]
        for f in [*L["css"], *L["js_before_runtime"], *L["js_after_runtime"]]:
            if not (FRAMES / f).exists():
                bad.append(f"{name}: missing {f}")
        if t["extends"] and t["extends"] not in T:
            bad.append(f"{name}: extends unknown theme {t['extends']}")
        if t["template"]:
            html = (FRAMES / t["template"]).read_text()
            got = re.findall(r'(?:href|src)="\.\./\.\./\.\./explainer/frames/([^"]+\.(?:css|js))"', html)
            want = [*L["css"], *L["js_before_runtime"], "runtime.js", *L["js_after_runtime"]]
            if got != want:
                bad.append(f"{name}: template loads {got}, theme.json says {want}")
    print("\n".join(bad) if bad else f"ok: {len(T)} themes, files and templates consistent")
    return not bad


if __name__ == "__main__":
    T = themes()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        lst(T)
    elif cmd == "show":
        show(T[sys.argv[2]])
    elif cmd == "open":
        subprocess.run(["open", *[str(ROOT / t["preview"]) for t in T.values() if t.get("preview")]])
    elif cmd == "check":
        sys.exit(0 if check(T) else 1)
    else:
        sys.exit(__doc__)
