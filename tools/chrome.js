// Path to the Chrome that puppeteer-core drives: $CHROME_PATH if set, else the
// first usual install location that exists (macOS, then Linux).
const fs = require('fs');

const CANDIDATES = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/usr/bin/google-chrome',
  '/usr/bin/google-chrome-stable',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
];

module.exports = process.env.CHROME_PATH || CANDIDATES.find((p) => fs.existsSync(p)) || CANDIDATES[0];

if (require.main === module) {
  const found = fs.existsSync(module.exports);
  console.log(found ? module.exports : `no Chrome found; set CHROME_PATH (tried ${CANDIDATES.join(', ')})`);
  process.exit(found ? 0 : 1);
}
