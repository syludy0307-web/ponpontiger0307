// Wikimedia Commons からライセンス安全な写真を取得し、リサイズ→base64で photos.js に埋め込む
// 使い方: node fetch_photos.cjs
// - 各keyに複数クエリのフォールバック / DL後にマジックバイト検証 / CC・PDのみ採用
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, 'assets', 'img');
fs.mkdirSync(OUT, { recursive: true });

// key ごとに候補クエリを順に試す
const WANTS = [
  { key: 'phone',  qs: ['smartphone lying on table', 'smartphone black screen desk', 'mobile phone on wooden table'] },
  { key: 'keypad', qs: ['ATM keypad numeric', 'PIN pad keypad numbers', 'door access keypad'] },
  { key: 'server', qs: ['server room data center', 'datacenter servers racks', 'computer server rack'] },
  { key: 'cable',  qs: ['network cables patch panel', 'ethernet cables switch', 'fiber optic cables'] },
  { key: 'court',  qs: ['Supreme Court of the Philippines building'] },
  { key: 'prison', qs: ['prison cell bars', 'jail cell bars corridor', 'barbed wire fence prison'] },
  { key: 'sky',    qs: ['Makati skyline night', 'Manila skyline night'] },
  { key: 'cuffs',  qs: ['handcuffs', 'handcuffs metal police'] },
];

// ONLY=phone,keypad で一部だけ取り直す（credits.json はマージ）
const ONLY = (process.env.ONLY || '').split(',').filter(Boolean);
const TARGETS = ONLY.length ? WANTS.filter(w => ONLY.includes(w.key)) : WANTS;

const api = q => 'https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search'
  + `&gsrsearch=${encodeURIComponent(q)}&gsrnamespace=6&gsrlimit=25`
  + '&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize&iiurlwidth=1600';

const strip = s => (s || '').replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();

// 実体が JPEG/PNG かマジックバイトで検証
function isImage(f) {
  if (!fs.existsSync(f) || fs.statSync(f).size < 20000) return false;
  const b = fs.readFileSync(f, { start: 0, end: 8 });
  return (b[0] === 0xFF && b[1] === 0xD8) || (b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4E && b[3] === 0x47);
}

const CRED_PATH = path.join(OUT, 'credits.json');
const credits = fs.existsSync(CRED_PATH) ? JSON.parse(fs.readFileSync(CRED_PATH, 'utf8')) : {};
for (const w of TARGETS) {
  let done = false;
  for (const q of w.qs) {
    if (done) break;
    let json;
    try {
      json = JSON.parse(execFileSync('curl', ['-sS', '-m', '40', api(q)], { encoding: 'utf8' }));
    } catch (e) { continue; }
    const pages = Object.values((json.query || {}).pages || {}).sort((a, b) => a.index - b.index);
    for (const p of pages) {
      const ii = (p.imageinfo || [])[0];
      if (!ii || !ii.thumburl) continue;
      const md = ii.extmetadata || {};
      const lic = strip((md.LicenseShortName || {}).value);
      if (!/\.(jpe?g|png)$/i.test(p.title)) continue;
      if (!/^(CC|Public domain|CC0|No restrictions)/i.test(lic)) continue;
      if (ii.thumbwidth < 800) continue;
      const file = path.join(OUT, `${w.key}.jpg`);
      try {
        execFileSync('curl', ['-sS', '-f', '-L', '-m', '90', '-o', file, ii.thumburl]);
      } catch (e) { continue; }
      if (!isImage(file)) { try { fs.unlinkSync(file); } catch (e) {} continue; }
      credits[w.key] = { title: p.title, license: lic, artist: strip((md.Artist || {}).value) };
      const kb = Math.round(fs.statSync(file).size / 1024);
      console.log('OK  ', w.key.padEnd(7), `${String(kb).padStart(4)}KB`, '|', lic.padEnd(14), '|',
        strip((md.Artist || {}).value).slice(0, 30).padEnd(30), '|', p.title.replace(/^File:/, '').slice(0, 52));
      done = true;
      break;
    }
  }
  if (!done) console.log('MISS', w.key);
}
fs.writeFileSync(CRED_PATH, JSON.stringify(credits, null, 2));

// ---- リサイズ(長辺<=1600) → base64 → photos.js ----
const photos = {};
for (const key of Object.keys(credits)) {
  const src = path.join(OUT, `${key}.jpg`);
  const dst = path.join(OUT, `_${key}_s.jpg`);
  try {
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', src,
      '-vf', "scale='if(gt(iw,ih),min(1600,iw),-2)':'if(gt(iw,ih),-2,min(1600,ih))'",
      '-q:v', '4', dst], { stdio: ['ignore', 'ignore', 'pipe'] });
  } catch (e) { console.log('CONVERR', key); continue; }
  photos[key] = 'data:image/jpeg;base64,' + fs.readFileSync(dst).toString('base64');
  fs.unlinkSync(dst);
}
fs.writeFileSync(path.join(OUT, 'photos.js'), 'window.PHOTOS=' + JSON.stringify(photos) + ';\n');
const mb = (fs.statSync(path.join(OUT, 'photos.js')).size / 1048576).toFixed(2);
console.log(`\nphotos.js: ${Object.keys(photos).length}枚 / ${mb}MB`);
