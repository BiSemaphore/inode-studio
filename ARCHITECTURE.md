# inode-studio architecture

Narrated vertical videos (Instagram 1080x1920) with a 16:9 twin (LinkedIn 1920x1080), made from code.

## The pipeline

```
choose a theme      tools/themes.py                     list the looks; the owner picks one
start a piece       tools/new_piece.py <group>/<slug> --theme <name>
facts               motion/<group>/<slug>/run/          local measurement script + log (fact-checker agent re-runs it)
script              beats.json                          one beat per idea: "show" (screen/subtitles), "say" (voice, [[word|phonemes]])
voice               explainer/voice.py                  Kokoro TTS -> voice/voice.wav + voice/timings.json (word times)
verify voice        tools/verify_voice.py               transcribes each beat; every phoneme-marked term must be heard
page                page.html                           the theme's template + content; every frame is a pure function of time t
stills + review     render.js <piece> <t...>            then the video-reviewer agent
render              explainer/frames/render.js          4 Chromes draw PNG frames -> ffmpeg -> out/<slug>.mp4 (+ --landscape)
sound               explainer/mix.py                    cues from the page (pen, taps, cuts) + ambient bed -> audio.wav
check               tools/check_video.py                every frame decoded and checked for breaks
cover + caption     cover.html, meta.json               clean covers in both shapes; layered caption
publish (local)     tools/publish.py                    copies the finished files into videos/<group>/<slug>/ (nothing goes online)
post                videos/POSTING.md                   the queue: what to post next, which file per platform
```

## Folders

| Folder | What lives there |
|---|---|
| `explainer/frames/runtime.js` | the timeline engine: frames, appear/fade, pens, subtitles; `window.renderFrame(t)` |
| `explainer/frames/render.js` | render command line; modules in `explainer/frames/render/` |
| `explainer/frames/render/` | `capture.js` (Chrome, frames, settle wait, profiling), `encode.js` (ffmpeg settings), `workers.js` (parallel ranges + join), `progress.js` |
| `explainer/frames/themes/<name>/` | one folder per theme: `theme.json`, CSS, JS, assets, `template.html` |
| `explainer/voice.py`, `explainer/mix.py` | narration and sound |
| `explainer/*` (build.py, kit.js, scenes.py, ...) | the older whiteboard kit, used only by the first inode episodes |
| `tools/` | small single-purpose scripts (themes, new piece, verify, check, publish, status, surface/leaf bakers) |
| `motion/<group>/<slug>/` | a video's sources (not in git): beats, page, voice, run, out |
| `videos/<group>/<slug>/` | finished files to post (not in git); `videos/POSTING.md` is the queue |
| `archive/` | compressed old or replaced pieces; `archive/INDEX.md` says what each is and how to restore it |
| `brand/references/` | the owner's references and study cards (`studies/`) |
| `.claude/` | the playbook skill, the reviewer and fact-checker agents, hooks |

## Themes

A theme is a package. `theme.json` is its single source of truth: what it is for, what it extends, the files to load in
order (`css`, `js_before_runtime`, `js_after_runtime`), its components with usage, its variants, an example piece and a
preview image. Themes form a short chain and never reach sideways:

```
base  ── field ── notebook
   │         └─ punch
   └─ card
```

- **base**: frames, element timing, subtitle structure, the 16:9 stage. No colours, fonts or figures.
- **field**: forest green, leaf light, cream ink people (`#stand #think #point #work #hold`), brush capitals.
- **notebook**: field + one notebook sheet the camera zooms into (the default explainer format).
- **punch**: field + one huge lowercase punchline and tiny flat figures.
- **card**: one idea per card on a plain page (white, or `data-page="green"` paper); thin coloured stick people,
  line icons, vectors in JetBrains Mono, math in STIX Two.

Add a theme: make `themes/<name>/` with `theme.json`, its files and `template.html` (load lines in the order the json
gives), then run `tools/themes.py check`. Never edit an approved theme's look for one video; add a variant instead.

## Rendering, measured (2026-10-24, 16 GB Mac)

Per frame at `--scale=2`: screenshot about 260 ms (the bottleneck), settle wait about 65 ms, drawing 1 ms, encoder wait
under 10 ms. 4 workers by default (9.2 frames/s; 6 gives only 10.4). A 65 s video takes about 5 minutes per shape.
The settle wait stays at the proven `full` setting; see `render/capture.js` for what each faster setting broke.
Only delivery files are written: no masters.

## Rules that are enforced, not remembered

- `.claude/hooks/prepublish.sh`: no publish without verified narration, 0 broken frames and a minimal caption.
- `.claude/hooks/no-dashes.sh`: no em or en dashes.
- `tools/verify_voice.py`: a beat fails if any phoneme-marked term is not heard (small and medium Whisper models).
- `tools/themes.py check`: themes, files and templates agree.
