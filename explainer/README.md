# Explainer videos

Sketch-on-a-whiteboard explainers: a narrated story, hand-drawn diagrams that
draw themselves, terminal scenes, plain subtitles. Every video uses this kit,
so they all look and sound the same.

## Make a new video

```bash
npm run new     --piece=explainers/ep01-topic   # script.md + story.py from the template
npm run preview --piece=explainers/ep01-topic   # opens Chrome: play with sound, scrub, step frames
npm run check   --piece=explainers/ep01-topic   # timeline, layout lint, sync (no render)
npm run video   --piece=explainers/ep01-topic   # render (skips still frames), frame check, QA
npm run publish --piece=explainers/ep01-topic   # copy finished files to videos/, update INDEX.md
```

**`script.md`** is the one file to read and edit for the words: front matter
(title, slug, series, date, status, theme, voice, intro card, `pronounce`
dictionary, post caption) and one `## id` section per beat with the subtitle
text, optional `say:` (spoken form) and `pause:`. The build compiles it to
`beats.json` and `meta.json`; editing a line re-records only that line.

**`story.py`** holds the pictures, built from scene templates (`scenes.py`):

```python
t = Terminal(s, at=0, prompt="leonard@lab:~$ ", title=("the fix", W("fix1", "fix")))
t.cmd("git show 4bf5", start=W("fix1", "Leonard's"), by=W("fix1", "stops,"))
t.out('Error: ...', mark=(W("fix1", "stops,"), GREEN))
t.done()                                   # places it, frames the camera

b = Board(s, at=B("why"), title=("short IDs", W("why", "why.")))
b.op("write", W("uuid", "random"), x=100, y=320, text="...", size=56, font="mono")
b.done()                                   # camera frames what was drawn

Statement(s, at=B("rule"), lines=[(W("rule", "refuse"), "refuse to guess", 110, BLUE)])
```

Coordinates inside a scene are local (a 1920x1080 frame); scenes get their own
area of the world and frame their own camera with room for subtitles.
`by=` and `mark=` are deadlines: the build fails if typing or output would lag
the word. Fix it with more time (start earlier, a longer `pause`), never by
typing faster.

**Themes** (`themes/*.json`): colours and fonts (`"dark": true` picks the
logo's dark files). Brand colours in `brand.json` override the theme's. `theme:` in
script.md picks one; `THEME=blackboard npm run preview ...` tries another
without editing. Colours in stories are roles (`"ink"`, `"accent"`, `"red"`,
`"green"`, `"paper"`), so a theme recolours everything. Themes:
`whiteboard` (house style), `blackboard` (dark), `clean` (no hand-drawn
strokes, UI cards).

## Checks (all must pass before anyone sees a video)

| Check | When | What |
|---|---|---|
| timeline | build | every `by=`/`mark=` deadline met |
| `lint_layout.js` | before render | per shot: nothing cut by the frame, under the subtitles or the watermark; no text overlap |
| `check_sync.js` | before render | every typed character appears on the frame of its key sound |
| `tools/check_video.py` | render | no blinking or black frames (bad frames are recaptured) |
| `qa.py` | after render | loudness -17..-14 LUFS, true peak under -1 dBTP, audio/video lengths, SRT |

## House rules

These came out of reviewing real videos. They are why the videos look
calm and readable; break them on purpose, not by accident.

Pronunciation
- LLM is said fast, the way people say it: `LLM=/ɛləlˈɛm/`, `LLMs=/ɛləlˈɛmz/`
  (0.3 s; the engine's default /ˌɛl ˌɛl ˈɛm/ stresses every letter and was
  judged too slow). Never spell acronyms with spaces ("L L M").
- Where the default is wrong, give exact phonemes in `pronounce`:
  `Ollama=/oʊlˈɑːmə/` (the default says "ah-LAH-muh").
- Listen to every new term once (`npm run preview`), or transcribe the clip
  and confirm the word is heard as written.

Story
- Real commands and real output; anything illustrative is still plausible.

Picture
- No visible pen or hand. Lines draw themselves.
- Never speed anything up to catch the voice. If a scene does not fit, draw
  less or add a pause to the beat (`"pause"` in beats.json).
- Rings are smooth loops (`ring`, `ellipse`); never rings on single terminal
  lines (they cross the lines around them): underline those with `line`.
- Arrows always end in a visible head; use `gap` when a dot sits at the target.
- Dashed means dashed (`dashed=True` is kept while drawing).
- Handwriting is written in one pass (`write`); code is typed (`typed=True`)
  with a human rhythm.
- Labels must end inside their box or map.
- Camera frames must not cut into other text.

Type and brand
- Handwriting: Virgil. Code and terminals: Ubuntu Mono. Subtitles and end
  card: Overused Grotesk.
- Subtitles: plain, one whole sentence at a time, timed to the voice. No word
  highlighting or zoom effects.
- Thumbnail (approved style): typography only, no frames or diagrams.
  `node explainer/thumbnail-type.js out.png "<line 1>" "<line 2>"`. Instagram
  Reel cover: 1080x1920 (9:16), white 16:9 block in the middle, black above and
  below; all content inside the block, so it survives the 9:16 Reel, 4:5 feed
  and 3:4 profile-grid crops. (A 4:5 cover had its sides cropped.)
  A short title about the topic (no character names), bold sans at display
  size, tight leading and tracking, in `brand-ink`, ending in a round
  `brand-dot` (both from `brand.json` colors); headline and lockup share one
  left margin, equal top and bottom margins.
- No tool credits in the video. Credit the keyboard recordings (eklee,
  qubodup, CC BY 3.0) in the post caption: the license requires it
  (`NOTICE.md`).

Sound
- Voice (Kokoro, local), quiet music bed ducked under it, keyboard on typing,
  small pops and whooshes. No drawing sounds. Ask before adding any new sound.

Quality
- Rendered at 2x internally, delivered as 1080p.
- No SVG masks in the kit. Large masks made Chrome drop parts of zoomed frames
  (missing strokes, text, whole boxes), differently from run to run.
- `tools/record.js` captures with 6 Chrome processes, prints progress (also in
  `out/progress.txt`, or `npm run -s progress`), checks the encoded video with
  `tools/check_video.py` and recaptures broken frames.
- The checker only catches single-frame blinks and black frames. After a
  render, also look at a contact sheet of the final MP4 before showing it.
- Before showing anyone: run `review.sh` and look at every sheet. Fix, rebuild,
  review again until a full pass is clean.

## Files

| File | What |
|---|---|
| `build.py` | `Story`: script, voice, word times, timeline deadlines, sessions, page, soundtrack |
| `scenes.py` | scene templates: `Terminal`, `Board`, `Statement` (layout + camera) |
| `script.py` | compiles `script.md` to `beats.json` + `meta.json` |
| `themes/*.json` | colours, fonts, logo files per look |
| `preview.js` | `?preview` player: sound, scrubber, frame stepping |
| `template/`, `new.sh` | starting point for a new video |
| `kit.js` | drawing engine (rough.js shapes, reveal, handwriting, typing, camera, subtitles) |
| `vendor/rough.js` | rough.js 4.6.6 (MIT), kept in the repo so renders work offline |
| `style.css` | the house look |
| `voice.py` | Kokoro narration per beat + word times by forced alignment (torchaudio MMS_FA). Measured against the audio: 21 ms median error at sentence starts, vs 41 ms for Whisper |
| `check.sh`, `qa.py`, `lint_layout.js`, `check_sync.js` | the checks above |
| `mix.py` | soundtrack: voice, keys, pops, whooshes, music (uses `tools/sound.py`) |
| `review.sh` | contact sheets for review |
| `compare_frames.py` | compares two folders of `tools/peek.js` snapshots (did a kit change move anything?) |
| `thumbnail.js` | frame thumbnail: a real frame of the video with the title and logo |
| `thumbnail-type.js` | typographic thumbnail (the approved Reel cover style) |
