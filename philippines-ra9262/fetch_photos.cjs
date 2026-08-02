// Wikimedia Commons からライセンス安全な写真を取得し、クレジット情報を保存する
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, 'assets', 'img');
fs.mkdirSync(OUT, { recursive: true });

const WANTS = [
  { key: 'flag',    q: 'Philippine flag waving sky photograph' },
  { key: 'court',   q: 'Supreme Court of the Philippines building' },
  { key: 'skyline', q: 'Makati skyline night' },
  { key: 'fence',   q: 'barbed wire fence silhouette sky' },
  { key: 'law',     q: 'law books gavel' },
];

const api = q => 'https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search'
  + `&gsrsearch=${encodeURIComponent(q)}&gsrnamespace=6&gsrlimit=8`
  + '&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize&iiurlwidth=1500';

const strip = s => (s || '').replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
const credits = {};

for (const w of WANTS) {
  const json = JSON.parse(execFileSync('curl', ['-sS', '-m', '30', api(w.q)], { encoding: 'utf8' }));
  const pages = Object.values((json.query || {}).pages || {}).sort((a, b) => a.index - b.index);
  let picked = null;
  for (const p of pages) {
    const ii = (p.imageinfo || [])[0];
    if (!ii) continue;
    const md = ii.extmetadata || {};
    const lic = strip((md.LicenseShortName || {}).value);
    const isJpg = /\.(jpe?g|png)$/i.test(p.title);
    if (!isJpg) continue;
    if (!/^(CC|Public domain|CC0|No restrictions)/i.test(lic)) continue;
    if (ii.thumbwidth < 900) continue;
    picked = { title: p.title, url: ii.thumburl, lic, artist: strip((md.Artist || {}).value) };
    break;
  }
  if (!picked) { console.log('MISS', w.key); continue; }
  const file = path.join(OUT, `${w.key}.jpg`);
  execFileSync('curl', ['-sS', '-L', '-m', '60', '-o', file, picked.url]);
  const kb = Math.round(fs.statSync(file).size / 1024);
  credits[w.key] = { title: picked.title, license: picked.lic, artist: picked.artist };
  console.log('OK', w.key, `${kb}KB`, '|', picked.lic, '|', picked.artist.slice(0, 40), '|', picked.title.slice(0, 60));
}
fs.writeFileSync(path.join(OUT, 'credits.json'), JSON.stringify(credits, null, 2));
