// 音声ミックス + 最終MP4作成
// narration を -15 LUFS に正規化し、BGM(-28 LUFSベッド) + timeline.js の SFX キューを重ねて結合
const { execFileSync } = require('child_process');
const path = require('path');
const TL = require('./timeline.js');

const A = p => path.join(__dirname, 'assets', p);
const O = p => path.join(__dirname, 'out', p);

const types = ['decision', 'ashika', 'boyon'];
const byType = Object.fromEntries(types.map(k => [k, TL.sfx.filter(s => s.k === k)]));

// BGM実測 -10.9 LUFS → -17.1dB でナレーションの約13dB下のベッドに
let fc = '[1:a]loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[voice];'
  + `[5:a]atrim=0:${TL.DUR},volume=-17.1dB,aresample=48000,`
  + `afade=t=in:st=0:d=0.4,afade=t=out:st=${TL.DUR - 2.2}:d=2.2[bgm];`;
const mixIns = ['[voice]', '[bgm]'];
types.forEach((k, ti) => {
  const list = byType[k];
  if (!list.length) return;
  const inIdx = 2 + ti;
  const g = TL.sfxGain[k];
  const splitOuts = list.map((_, i) => `[${k}${i}]`).join('');
  fc += `[${inIdx}:a]volume=${g},aresample=48000,asplit=${list.length}${splitOuts};`;
  list.forEach((s, i) => {
    const ms = Math.round(s.t * 1000);
    fc += `[${k}${i}]adelay=${ms}:all=1[${k}${i}d];`;
    mixIns.push(`[${k}${i}d]`);
  });
});
fc += `${mixIns.join('')}amix=inputs=${mixIns.length}:normalize=0,alimiter=limit=0.95[aout]`;

// 高品質版(video_silent)と配信用(既存tiktok版の映像ストリーム)の両方に同じ音声を載せる
const targets = [
  ['video_silent.mp4', 'philippines_adultery_final.mp4'],
  ['philippines_adultery_tiktok.mp4', 'philippines_adultery_tiktok_new.mp4'],
];
console.log('SFX counts:', types.map(k => `${k}=${byType[k].length}`).join(' '));
for (const [vin, vout] of targets) {
  execFileSync('ffmpeg', [
    '-y', '-v', 'error',
    '-i', O(vin),
    '-i', A('narration.mp3'),
    '-i', A('sfx_decision.mp3'),
    '-i', A('sfx_ashika.mp3'),
    '-i', A('sfx_boyon.mp3'),
    '-i', A('bgm.mp3'),
    '-filter_complex', fc,
    '-map', '0:v', '-map', '[aout]',
    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
    '-movflags', '+faststart', '-t', String(TL.DUR),
    O(vout),
  ], { stdio: 'inherit' });
  console.log('done ->', vout);
}
