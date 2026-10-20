// Brand settings for the thumbnail scripts, from brand.json (or
// brand.example.json when there is none). See README.md, "Your brand".
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

function load() {
  for (const name of ['brand.json', 'brand.example.json']) {
    const p = path.join(ROOT, name);
    if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf8'));
  }
  return {};
}

// The logo as HTML: mark and wordmark side by side, or whichever one is set,
// or '' when brand.json has no logo. `src` turns a repo-relative path into a URL.
function lockup(brand, src, cls = 'lockup') {
  const logo = brand.logo;
  if (!logo || (!logo.mark && !logo.word)) return '';
  const off = logo.word_offset;
  const style = off != null ? ' style="align-items: flex-start"' : '';
  const word = off != null ? ` style="margin-top: ${off}em"` : '';
  return `<span class="${cls}"${style}>` +
    (logo.mark ? `<img class="logo-mark" src="${src(logo.mark)}" alt="">` : '') +
    (logo.word ? `<img class="logo-word" src="${src(logo.word)}"${word} alt="">` : '') +
    '</span>';
}

module.exports = { ROOT, load, lockup };
