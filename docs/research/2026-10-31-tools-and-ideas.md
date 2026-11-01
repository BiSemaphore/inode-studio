# Tools and ideas worth adopting (research, 2026-10-31)

Sources: softgirlnocode.com (AI Edit Suite page, free resources), her reel De1xXtICvqs, and web research. Licences
below are as reported; confirm each on the project's own page before shipping anything with it.

## What softgirlnocode actually sells and teaches
- **AI Edit Suite** (opens early November, $89, preorder $71.20): lessons plus a "Video Editor Kit". Three tracks:
  creator-style reels from one prompt (templates named Dan Koe minimal line art, Kelsey blended captions, Live Plot
  3D line art, Giant Word Behind, Wall-to-One, Outline Draw, Profile Scroll, Prompt-to-Play, Done Wall,
  Folder-to-Carousel), B-roll matching for long-form cut into an editable CapCut draft (40 min to 6 min, cut on the
  last word), and faceless avatar explainers (pick a presenter, script, look, render).
- Her stack: Claude Code or Codex, HeyGen **HyperFrames** (HTML to MP4), ElevenLabs transcripts, ffmpeg, Suno music,
  CapCut, and GitHub effect libraries. Her workspace is ours: CLAUDE.md, references/brand.md, voice.md, skills.

## Lessons we should adopt (free guides)
1. **Brief before build** ("decisions, not adjectives"): BEATS (one message each), VISUAL SYSTEM (exact colours,
   fonts, video type sizes), MOTION (hero, support, background), TRANSITIONS (2 or 3 allowed, where the big one goes),
   AVOID, and **PROOF FRAMES** (the 3 paused frames that show it worked). Review the plan, not only the render.
2. **Six motion rules**: one beat one idea; design the paused frame first; video type is about 2x web size; graphics
   clarify, never decorate; motion hierarchy (hero moves first); transitions carry meaning (hard cut = emphasis,
   crossfade = related thought, push = momentum).
3. **Cinematic captions**: one hero word per sentence (number, place, result, stressed word) set large in a heavy
   display face; support lines short and mixed case; build a phrase in place; vary layout between ideas, not within;
   never cover face, hands or product; one special effect only on the biggest moment.
4. **Session handoff note** with fixed sections (where we started, decisions, done, in progress, open questions,
   pick up here). Our project-status memory plays this role; keep its sections fixed.

## Engines and libraries
| Project | What it gives us | Licence |
|---|---|---|
| [HyperFrames](https://github.com/heygen-com/hyperframes) (HeyGen) | HTML/CSS/GSAP/Lottie/Three.js to deterministic MP4, agent skills (`npx skills add heygen-com/hyperframes`). The same idea as our frames engine, production-hardened | Apache 2.0 |
| [Remotion skills](https://www.remotion.dev/docs/ai/skills) | React video; `npx skills add remotion-dev/skills` | Remotion needs a company licence |
| [Motion Canvas](https://motioncanvas.io) | procedural vector explainer animation, real open source | MIT |
| [GSAP](https://gsap.com) incl. SplitText, MorphSVG | the industry timeline; all plugins free since 2025 | free (Webflow standard licence; no no-code builders) |
| [vfx-js](https://github.com/fand/vfx-js) | WebGL effects on any HTML element: glitch, bloom, halftone, pixelate, scanline | MIT |
| [vgpu](https://github.com/vercel-labs/vgpu) (Vercel) | shader backgrounds: fluid, holographic, glass | MIT |
| [Thinking Orbs](https://github.com/Jakubantalik/Libraries.dev) | dot-orb loaders (Searching, Solving, Composing...): an "AI is thinking" visual | MIT |
| [Drawably](https://github.com/danielwh2/drawably) | hand-drawn underlines, circles, scribble buttons with animated pen strokes | MIT |
| [fogleman/ln](https://github.com/fogleman/ln) | 3D scenes rendered as clean line drawings (SVG) | MIT |
| [Pretext](https://github.com/chenglou/pretext) | fast text measurement: fit and break type exactly before layout | MIT |
| [Textify.js](https://github.com/MAGGIx1404/Textify-js) | split text into lines, words, characters for kinetic type (GSAP) | MIT |

## Claude skills for video (community; read the code before installing, skills can run anything)
- [video-creator-skills](https://github.com/jdjf39/video-creator-skills): bundle (watch and listen to footage, cut,
  caption, motion design) incl. cinetic, motionmaxxing, motion-director.
- [cinetic](https://github.com/Leonxlnx/cinetic) (MIT): cinematic launch films from code. [motionmaxxing](https://github.com/Tejashmakwana/motionmaxxing) (Apache 2.0): ten-step motion protocol.
- [motion-graphics](https://github.com/Barty-Bart/motion-graphics): B-roll timed to speech, object separation, SFX.
- [claude-motion-design](https://github.com/howseen-ai/claude-motion-design) (MIT): HTML + Playwright + ffmpeg, like ours.
- [claude-video-2](https://github.com/ItsssssJack/claude-video-2): 21 looks, checks its own rendered frames.
- [anthropics/skills](https://github.com/anthropics/skills) (official), [awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) (index).
- [blender-mcp](https://github.com/kiuber/blender-mcp): Claude drives Blender (3D scenes, scripted animation).

## Music and sound
- **Suno**: paid plans (Pro about $8 to $10 a month, Premier about $30) give commercial use of tracks made while
  subscribed; free plan is non-commercial. No public API (an invite-only partner programme since July 2026), so
  tracks are made by hand in the app. Terms changed after the Warner deal; read the current ToS.
- **Local, no subscription**: ACE-Step 1.5 (reported MIT/Apache, full songs incl. instrumental mode), Stable Audio
  Open / Stable Audio 3 (Stability Community Licence: free under $1M revenue a year; SFX and short loops), MusicGen
  weights (licence reports conflict: check).
- **SFX library**: Sonniss GDC bundles (free, royalty-free commercial, no attribution; check the AI-training clause).
