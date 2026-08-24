// Wikimedia Commons からライセンス確認済みの素材のみを取得し、credits.json を作る
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, 'assets', 'img');
fs.mkdirSync(OUT, { recursive: true });

const WANTS = [
  { key: 'courtroom', q: 'courtroom interior judge bench Philippines' },
  { key: 'street', q: 'Manila street night jeepney' },
  { key: 'lawbooks', q: 'law books shelf legal library' },
  { key: 'sc_interior', q: 'Supreme Court of the Philippines session hall' },
];

const api = q => 'https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search'
  + `&gsrsearch=${encodeURIComponent(q)}&gsrnamespace=6&gsrlimit=10`
  + '&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize&iiurlwidth=1500';
const strip = s => (s || '').replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();

// 既存の流用素材（過去プロジェクトからコピー済み）
const credits = {
  court2: { title: 'Supreme Court facade (Padre Faura, Manila)', license: 'CC BY-SA 4.0', artist: 'Patrickroque01' },
  flag: { title: 'Philippine Flag at Manila City Hall', license: 'CC BY-SA 4.0', artist: 'Roel Balingit' },
  skyline: { title: 'Skyline of Makati at night', license: 'CC0', artist: 'Red marquis' },
};

for (const w of WANTS) {
  let json;
  try { json = JSON.parse(execFileSync('curl', ['-sS', '-m', '30', api(w.q)], { encoding: 'utf8' })); }
  catch (e) { console.log('ERR', w.key, e.message.slice(0, 60)); continue; }
  const pages = Object.values((json.query || {}).pages || {}).sort((a, b) => a.index - b.index);
  let picked = null;
  for (const p of pages) {
    const ii = (p.imageinfo || [])[0];
    if (!ii) continue;
    const md = ii.extmetadata || {};
    const lic = strip((md.LicenseShortName || {}).value);
    if (!/\.(jpe?g|png)$/i.test(p.title)) continue;
    if (!/^(CC|Public domain|CC0|No restrictions)/i.test(lic)) continue;
    if (ii.thumbwidth < 900) continue;
    picked = { title: p.title, url: ii.thumburl, lic, artist: strip((md.Artist || {}).value) };
    break;
  }
  if (!picked) { console.log('MISS', w.key); continue; }
  const file = path.join(OUT, `${w.key}.jpg`);
  execFileSync('curl', ['-sS', '-L', '-m', '60', '-o', file, picked.url]);
  credits[w.key] = { title: picked.title.replace(/^File:/, ''), license: picked.lic, artist: picked.artist };
  console.log('OK', w.key, `${Math.round(fs.statSync(file).size / 1024)}KB`, '|', picked.lic, '|',
    picked.artist.slice(0, 34), '|', picked.title.slice(0, 60));
}
fs.writeFileSync(path.join(OUT, 'credits.json'), JSON.stringify(credits, null, 2));
console.log('credits ->', Object.keys(credits).join(', '));
