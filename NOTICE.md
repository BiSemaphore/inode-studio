# Third-party files

The MIT license in `LICENSE` covers the code. These files keep their own
licenses, which are included next to them.

| Files | What | License |
|---|---|---|
| `fonts/Virgil.woff2` | Virgil, the handwriting font, by Ellinor Rapp (Excalidraw) | SIL OFL 1.1, `fonts/Virgil-OFL.md` |
| `fonts/OverusedGrotesk-*.woff2` | Overused Grotesk, by Bao Nguyen / RandomMaerks | SIL OFL 1.1, `fonts/OverusedGrotesk-OFL.txt` |
| `fonts/UbuntuMono-*.ttf` | Ubuntu Mono, by Canonical | Ubuntu Font Licence 1.0, `fonts/UbuntuMono-UFL.txt` |
| `explainer/vendor/rough.js` | rough.js 4.6.6, by Preet Shihn | MIT, `explainer/vendor/rough.LICENSE` |
| `audio/keypresses-eklee/` | Keyboard recordings by eklee, single sounds extracted by qubodup | CC BY 3.0, `audio/keypresses-eklee/license.txt` |

**CC BY 3.0 means credit.** A video that uses the keyboard sounds (any video
with a terminal scene) has to credit the authors, for example in the post
caption: `Keyboard sounds: eklee, qubodup (CC BY 3.0)`. The template caption
already has that line.

Downloaded by `scripts/setup.sh`, not stored in this repo:

| Files | What | License |
|---|---|---|
| `tts/kokoro-v1.0.onnx`, `tts/voices-v1.0.bin` | Kokoro-82M voice model, ONNX export from [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) | Apache 2.0 |
| torchaudio `MMS_FA` (first render) | Forced-alignment model for word timings | CC BY-NC 4.0, see below |

The MMS_FA alignment model is published by Meta under CC BY-NC 4.0. It only
computes word timings on your machine and is not part of the videos you make,
but check its terms if you use this commercially.
