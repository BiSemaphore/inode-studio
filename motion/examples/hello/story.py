"""Example: the smallest explainer, about how it is made.

  npm run preview --piece=examples/hello    # look at it in Chrome, no render
  npm run video   --piece=examples/hello    # render + QA

Narration, title, theme and caption live in script.md. Scenes use local
coordinates (a 1920x1080 frame each) and frame their own camera.
"""

import pathlib
import sys

# The kit is explainer/ at the repo root, however deep this piece sits.
root = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "explainer/build.py").exists())
sys.path.insert(0, str(root / "explainer"))
from build import BLUE, GREEN, Story  # noqa: E402
from scenes import Board, Terminal  # noqa: E402

s = Story(__file__)
B, W = s.B, s.W

# 1. the folder: two files
t = Terminal(s, at=0, prompt="you@desk:~$ ")
t.cmd("ls hello/", start=1.3, by=W("hook", "files."))
t.out("script.md  story.py", mark=(W("hook", "files."), GREEN))
t.done(appear=1.2)

# 2. what each file holds
b = Board(s, at=B("files", 0.0), title=("two files", W("files", "script.md", -0.3)))
b.op("rect", W("files", "script.md", 0.0), x=100, y=260, w=460, h=150)
b.op("write", W("files", "script.md", 0.2), x=150, y=350, text="script.md", size=56, font="mono")
b.op("write", W("files", "words.", -0.2), x=640, y=350, text="the words", size=56, color=BLUE)
b.op("rect", W("files", "story.py", 0.0), x=100, y=470, w=460, h=150)
b.op("write", W("files", "story.py", 0.2), x=150, y=560, text="story.py", size=56, font="mono")
b.op("write", W("files", "pictures.", -0.2), x=640, y=560, text="the pictures", size=56, color=BLUE)
b.done()

# 3. one command
r = Terminal(s, at=B("render", 0.0), prompt="you@desk:~$ ", title=("one command", W("render", "command", -0.2)))
r.cmd("npm run video --piece=examples/hello", start=W("render", "One"), paste=True, by=W("render", "renders"))
r.out("hello capturing: frames (100%)", mark=(W("render", "frame"), GREEN))
r.out("checked clean -> hello.mp4", by=W("render", "machine."))
r.done(appear=W("render", "One", -0.2))

# The last beat plays over the end card (brand.json "endcard").

s.build(title="Hello from inode-studio")
