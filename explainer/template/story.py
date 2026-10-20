"""Explainer: <topic>.

  npm run preview --piece=<group>/<piece>    # look at it in Chrome, no render
  npm run check   --piece=<group>/<piece>    # timeline, layout, sync
  npm run video   --piece=<group>/<piece>    # render + QA
  npm run publish --piece=<group>/<piece>    # copy to videos/

Narration, title, theme and caption live in script.md. Scenes below use local
coordinates (a 1920x1080 frame each) and frame their own camera.
"""

import pathlib
import sys

# The kit is explainer/ at the repo root, however deep this piece sits.
root = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "explainer/build.py").exists())
sys.path.insert(0, str(root / "explainer"))
from build import BLUE, GREEN, RED, Story  # noqa: E402,F401
from scenes import Board, Statement, Terminal  # noqa: E402,F401

s = Story(__file__)
B, W = s.B, s.W

# A terminal session: commands typed at a human pace, output with deadlines.
t = Terminal(s, at=0, prompt="leonard@lab:~$ ")
t.cmd("git --version", start=1.5, by=W("hook", "happened."))
t.out("git version 2.47.0", mark=(W("hook", "surprising"), GREEN))
t.done(appear=1.2)

# A whiteboard: drawing tied to the words that explain it.
b = Board(s, at=B("idea", 0.0), title=("the idea", W("idea", "idea")))
b.op("write", W("idea", "explains", 0.0), x=100, y=320, text="draw the idea here", size=56)
b.done()

Statement(s, at=B("end", -0.2), lines=[(B("end", 0.0), "the takeaway", 96, BLUE)])

s.build(title="<topic>")
