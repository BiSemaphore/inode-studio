// ffmpeg settings: lossless PNG frames in, one delivery MP4 out (Instagram 1080x1920 or LinkedIn 1920x1080).
// Standard colour (limited range, BT.709, tagged), high bitrate, 2 s keyframes, tuned for flat animation.
// With blur, frames are drawn at 60 fps and each output frame blends two of them (motion blur).
const FPS = 30;   // Reels play at 30; a 60 fps upload gets half its frames thrown away
const SCALE = 'scale=out_range=tv:out_color_matrix=bt709:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p';
const BLEND = "tmix=frames=2:weights='1 1',select='mod(n\\,2)',setpts=N/(30*TB),";
const AUDIO_ARGS = ['-c:a', 'aac', '-b:a', '256k', '-ar', '48000'];
// tune animation: flat colour and hard edges (more B-frames, softer deblocking)
const ENCODE = [
  '-c:v', 'libx264', '-preset', 'slow', '-tune', 'animation', '-crf', '14', '-maxrate', '16M', '-bufsize', '32M',
  '-profile:v', 'high', '-level', '4.2', '-r', String(FPS), '-fps_mode', 'cfr',   // constant 30 fps: chunks join without drift
  '-x264-params', 'aq-mode=3:colorprim=bt709:transfer=bt709:colormatrix=bt709', '-g', String(FPS * 2),
  '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv'];

// PNG frames arrive on stdin
const pngIn = (blur) => ['-f', 'image2pipe', '-framerate', String(blur ? 2 * FPS : FPS), '-c:v', 'png', '-i', '-'];

// output options after the inputs. cfg: { w, h, dsf, blur }. Frames drawn at dsf > 1 are shrunk to w x h.
function outputs(cfg, out, withAudio) {
  const a = withAudio ? ['-map', '1:a', ...AUDIO_ARGS, '-shortest', '-movflags', '+faststart'] : ['-an'];
  if (cfg.dsf === 1) return [...(withAudio ? ['-map', '0:v'] : []), '-vf', (cfg.blur ? BLEND : '') + SCALE, ...ENCODE, ...a, out];
  const fc = `[0:v]${cfg.blur ? BLEND : ''}${SCALE.replace('scale=', `scale=${cfg.w}:${cfg.h}:`)}[do]`;
  return ['-filter_complex', fc, '-map', '[do]', ...ENCODE, ...a, out];
}

// the times to draw for output frames [a, b): one each, or with blur the 60 fps pair behind each one
const times = (a, b, blur) => blur
  ? [...Array(2 * (b - a)).keys()].map((k) => Math.max(0, 2 * a - 1 + k) / (2 * FPS))
  : [...Array(b - a).keys()].map((k) => (a + k) / FPS);

module.exports = { FPS, AUDIO_ARGS, pngIn, outputs, times };
