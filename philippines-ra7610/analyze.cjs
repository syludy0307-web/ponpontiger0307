// §23/§26 テンポ自動検査
//   完成動画を解析して「2秒以上、実質的な視覚変化がない箇所」を検出する。
//   隣接フレーム差分（tblend=difference）を blackframe に通し、
//   差分がほぼ真っ黒＝動きなし のフレームが連続する区間を報告する。
//
//   使い方: node analyze.cjs out/RA7610_Bongalon_TikTok_FINAL.mp4
const { spawnSync } = require('child_process');
const path = require('path');

const file = process.argv[2] || path.join(__dirname, 'out', 'RA7610_Bongalon_TikTok_FINAL.mp4');
const FPS = 30;
const STATIC_PBLACK = 99.4;   // 差分画像の黒率がこれ以上なら「変化なし」
const MIN_RUN_SEC = 2.0;      // 指示書のしきい値

const r = spawnSync('ffmpeg', [
  '-hide_banner', '-i', file,
  '-vf', 'scale=400:-2,format=gray,tblend=all_mode=difference,blackframe=amount=0:threshold=14',
  '-f', 'null', '-',
], { encoding: 'utf8', maxBuffer: 1 << 28 });

const lines = (r.stderr || '').split('\n').filter(l => l.includes('blackframe'));
const stat = [];
for (const l of lines) {
  const f = /frame:(\d+)/.exec(l), p = /pblack:(\d+)/.exec(l);
  if (f && p) stat.push({ f: +f[1], p: +p[1] });
}
if (!stat.length) { console.log('解析データなし（ffmpegのblackframe出力が取れませんでした）'); process.exit(0); }

// 連続する「変化なし」区間を抽出
const runs = [];
let start = null, prev = null;
for (const s of stat) {
  const isStatic = s.p >= STATIC_PBLACK;
  if (isStatic) { if (start === null) start = s.f; }
  else if (start !== null) { runs.push([start, prev]); start = null; }
  prev = s.f;
}
if (start !== null) runs.push([start, prev]);

const bad = runs
  .map(([a, b]) => ({ a: a / FPS, b: b / FPS, d: (b - a + 1) / FPS }))
  .filter(x => x.d >= MIN_RUN_SEC);

console.log(`解析: ${path.basename(file)}  総フレーム ${stat.length}`);
console.log(`静止判定しきい値: pblack>=${STATIC_PBLACK} / 検出下限 ${MIN_RUN_SEC}s`);
if (!bad.length) {
  console.log('✅ 2秒以上の無変化区間なし（§23クリア）');
} else {
  console.log(`⚠ ${bad.length}箇所の無変化区間:`);
  for (const x of bad) console.log(`   ${x.a.toFixed(2)}s 〜 ${x.b.toFixed(2)}s （${x.d.toFixed(2)}s）`);
}
// 参考：最長の準静止区間トップ5
const top = runs.map(([a, b]) => ({ a: a / FPS, d: (b - a + 1) / FPS }))
  .sort((x, y) => y.d - x.d).slice(0, 5);
console.log('参考・準静止の長い順:', top.map(x => `${x.a.toFixed(1)}s(${x.d.toFixed(2)}s)`).join(' '));
