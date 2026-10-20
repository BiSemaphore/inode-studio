# inode-studio

Narrated explainer videos from two text files, rendered on your own machine.

You write `script.md` (the words) and `story.py` (the pictures: terminals
that type, whiteboard drawings that draw themselves, statements). The build
synthesizes the voice locally, ties every drawing to the word it illustrates,
and renders an MP4 frame by frame from HTML in headless Chrome. Same input,
same video: no screen recording, no dropped frames, no hosted service.

It started as the video setup for [inode](https://github.com/BiSemaphore/inode)
explainers and was split out so other people can use it.

```
script.md + story.py  ->  voice (Kokoro)  ->  word times (forced alignment)
                      ->  piece.html      ->  checks  ->  frames  ->  MP4 + SRT
```

## Requirements

- macOS or Linux, Node 18+, ffmpeg, curl
- Google Chrome or Chromium (set `CHROME_PATH` if it is not in the usual place)
- [uv](https://docs.astral.sh/uv/) or Python 3.12

Everything is free and runs locally. Disk: about 340 MB for the voice model,
plus torch, plus about 1.2 GB for the alignment model, which torchaudio
downloads on the first build.

## Setup

```bash
git clone https://github.com/BiSemaphore/inode-studio
cd inode-studio
scripts/setup.sh      # npm install, .venv, voice model; safe to run again
```

## Make the example

```bash
npm run preview --piece=examples/hello    # opens Chrome: play with sound, scrub, step frames
npm run video   --piece=examples/hello    # checks, render, QA -> motion/examples/hello/out/hello.mp4
```

The first build is slow (it downloads the alignment model and records every
line). After that, editing one line of `script.md` re-records only that line.

## Make your own

```bash
npm run new     --piece=explainers/ep01-topic   # copies explainer/template/
npm run preview --piece=explainers/ep01-topic
npm run check   --piece=explainers/ep01-topic   # timeline, layout, sync, no render
npm run video   --piece=explainers/ep01-topic
npm run publish --piece=explainers/ep01-topic   # copies finished files to videos/
```

Your pieces live in `motion/<group>/<piece>/`. Everything under `motion/`
except `examples/` is gitignored, as are `videos/`, `brand/` and
`brand.json`, so pulling updates never touches your work.

`explainer/README.md` covers the kit: the `script.md` format, scene
templates, themes, and the house rules.

## Your brand

Copy `brand.example.json` to `brand.json` and edit it:

```json
{
 "endcard": { "mark": "your-project", "sub": "one line about it", "url": "github.com/you/your-project" },
 "logo": {
  "mark": "brand/mark.svg", "word": "brand/wordmark.svg",
  "mark_dark": "brand/mark-dark.svg", "word_dark": "brand/wordmark-dark.svg",
  "word_offset": 0.8
 },
 "colors": { "brand-ink": "#003554", "brand-dot": "#00a6fb" }
}
```

- `endcard`: the closing card. A story can override it with `s.build(endcard=...)`.
- `logo`: paths relative to the repo root (put the files in `brand/`). Give a
  mark, a wordmark, or both; the `_dark` files are used by dark themes.
  `word_offset` (em) drops the wordmark onto the mark's baseline; leave it out
  to centre them. `"logo": null` means no watermark.
- `colors`: override any theme colour (`explainer/themes/*.json`).

## Layout

```
explainer/       the explainer kit: script.md format, Story (build.py), scenes,
                 drawing engine (kit.js), themes, voice, mix, checks, thumbnails
tools/           piece-agnostic: recorder, frame snapshots, video checks, sound
                 synthesis, publish, Chrome lookup, brand.json loader
scripts/         setup and the npm script wrappers
motion/          your pieces (motion/<group>/<piece>/); only examples/ is tracked
fonts/, audio/   bundled fonts and keyboard sounds (NOTICE.md)
tts/             the voice model, downloaded by setup
```

Every Python script runs in `.venv` (Python 3.12), which `scripts/setup.sh`
creates. After setup, building and rendering need no network.

## How rendering works

A piece is an HTML page whose animations are CSS / Web Animations and which
sets `window.MOTION = { duration, fps }`. `tools/record.js` opens it in 6
headless Chrome processes, pauses every animation, seeks
`document.getAnimations()` to each frame time, screenshots `#stage`, and
encodes with ffmpeg. Frames where nothing can change (`tools/change_times.js`)
are copied instead of captured. The encoded video is checked for single-frame blinks and black
frames, and broken frames are recaptured.

Before rendering, `npm run check` fails the build if typing or output would
lag the word it belongs to, if anything is cut by the frame or sits under the
subtitles or watermark, or if a key sound misses its character's frame. After
rendering, `qa.py` checks loudness (-17 to -14 LUFS), true peak, audio and
video length, and the SRT.

## License

MIT for the code (`LICENSE`). Fonts and keyboard sounds keep their own
licenses; the keyboard sounds are CC BY 3.0 and need a credit in your post.
See `NOTICE.md`, which also covers the downloaded models.
