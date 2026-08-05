// 音声ミックス + 最終MP4作成（RA9995版）
// narration -15 LUFS + BGM + SFX 33発（合成thump/shatter含む）
// 演出: BGMは47.5秒から2秒でフェードアウト → ラスト約1.4秒は無音＋赤画面
const { execFileSync } = require('child_process');
const path = require('path');
const TL = require('./timeline.js');

const A = p => path.join(__dirname, 'assets', p);
const O = p => path.join(__dirname, 'out', p);

const types = ['decision', 'ashika', 'boyon', 'thump', 'shatter'];
const byType = Object.fromEntries(types.map(k => [k, TL.sfx.filter(s => s.k === k)]));

let fc = '[1:a]loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[voice];'
  + `[7:a]atrim=0:${TL.DUR},volume=-17.1dB,aresample=48000,`
  + 'afade=t=in:st=0:d=0.4,afade=t=out:st=47.5:d=2.0[bgm];';
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

const audioIns = [
  '-i', A('narration.mp3'),   // 1
  '-i', A('sfx_decision.mp3'),// 2
  '-i', A('sfx_ashika.mp3'),  // 3
  '-i', A('sfx_boyon.mp3'),   // 4
  '-i', A('sfx_thump.wav'),   // 5
  '-i', A('sfx_shatter.wav'), // 6
  '-i', A('bgm.mp3'),         // 7
];
console.log('SFX counts:', types.map(k => `${k}=${byType[k].length}`).join(' '));

execFileSync('ffmpeg', [
  '-y', '-v', 'error', '-i', O('video_silent.mp4'), ...audioIns,
  '-filter_complex', fc, '-map', '0:v', '-map', '[aout]',
  '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
  '-movflags', '+faststart', '-t', String(TL.DUR), O('philippines_ra9995_final.mp4'),
], { stdio: 'inherit' });
console.log('done -> philippines_ra9995_final.mp4');

execFileSync('ffmpeg', [
  '-y', '-v', 'error', '-i', O('philippines_ra9995_final.mp4'),
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '21',
  '-maxrate', '3600k', '-bufsize', '7200k', '-pix_fmt', 'yuv420p',
  '-c:a', 'copy', '-movflags', '+faststart', O('philippines_ra9995_tiktok.mp4'),
], { stdio: 'inherit' });
console.log('done -> philippines_ra9995_tiktok.mp4');
