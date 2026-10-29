// A few seconds of a piece as a quick motion preview (for the owner's yes before a full render), with motion blur.
//   node tools/preview_clip.js <piece> <t0> <t1> <out.mp4> [--landscape] [--scale=1]
// Draws 60 frames per second and blends pairs to 30 (the same blur as render.js); the narration for that span is
// muxed in (no effects or music; the full render mixes those).
const path = require('path'), fs = require('fs'), { spawn, execFileSync } = require('child_process');
const root = path.resolve(__dirname, '..');
const { openPage } = require(path.join(root, 'explainer/frames/render/capture'));

(async () => {
  const args = process.argv.slice(2);
  const [piece, a, b, out] = args;
  const landscape = args.includes('--landscape');
  const dsf = +((args.find((x) => x.startsWith('--scale=')) || '=1').split('=')[1]);
  const dir = path.resolve(root, piece);
  const page = [landscape ? 'page-linkedin.html' : 'page-instagram.html', 'page.html'].find((f) => fs.existsSync(path.join(dir, f)));
  const { browser, frame } = await openPage(dir, { landscape, dsf, page });
  const t0 = +a, t1 = +b, W = landscape ? 1920 : 1080, H = landscape ? 1080 : 1920;
  const tmp = out + '.video.mp4';
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', '60', '-c:v', 'png', '-i', '-',
    '-filter_complex', `[0:v]tmix=frames=2:weights='1 1',select='mod(n\\,2)',setpts=N/(30*TB),scale=${W}:${H}:flags=lanczos,format=yuv420p`,
    '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', tmp], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let t = t0; t < t1; t += 1 / 60) {
    const png = await frame(t);
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  await browser.close();
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', tmp, '-ss', String(t0), '-t', String(t1 - t0), '-i', path.join(dir, 'voice/voice.wav'),
    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', out]);
  fs.unlinkSync(tmp);
  console.log(out);
})().catch((e) => { console.error(e.message); process.exit(1); });
