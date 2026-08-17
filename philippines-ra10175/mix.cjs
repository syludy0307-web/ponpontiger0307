// 音声ミックス + 最終MP4作成（RA10175 不正アクセス版）
// 演出:
//   - BGM は 14.85(黒0.3秒明け)で1段上げる（台本「BGM 1段変更」）
//   - 42.30-44.35 は BGM 完全無音（赤フラッシュ→静寂→唯一の低音ドンで復帰）
//   - thump は 44.35 の1回だけ
const { execFileSync } = require('child_process');
const path = require('path');
const TL = require('./timeline.js');

const A = p => path.join(__dirname, 'assets', p);
const O = p => path.join(__dirname, 'out', p);

const types = ['decision', 'ashika', 'boyon', 'thump', 'shatter', 'shutter'];
const byType = Object.fromEntries(types.map(k => [k, TL.sfx.filter(s => s.k === k)]));

// ---- BGM のゲイン曲線（段変更 + 無音窓、境界は短いランプでプチノイズ回避） ----
const B = TL.bgm;
const db = d => Math.pow(10, d / 20);
const g1 = db(B.db1).toFixed(5), g2 = db(B.db2).toFixed(5);
const [s0, s1] = B.silence;
const st = B.stepT, R = 0.06, D = 0.08, U = 0.10;
const gainExpr =
  `if(lt(t,${st}),${g1},` +
  `if(lt(t,${(st + R).toFixed(3)}),${g1}+(${g2}-${g1})*(t-${st})/${R},` +
  `if(lt(t,${(s0 - D).toFixed(3)}),${g2},` +
  `if(lt(t,${s0}),${g2}*(1-(t-${(s0 - D).toFixed(3)})/${D}),` +
  `if(lt(t,${s1}),0,` +
  `if(lt(t,${(s1 + U).toFixed(3)}),${g2}*(t-${s1})/${U},${g2}))))))`;

let fc = '[1:a]loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[voice];'
  + `[8:a]atrim=0:${TL.DUR},aresample=48000,`
  + `volume='${gainExpr}':eval=frame,`
  + `afade=t=in:st=0:d=${B.fadeIn},afade=t=out:st=${(TL.DUR - B.fadeOut).toFixed(2)}:d=${B.fadeOut}[bgm];`;

const mixIns = ['[voice]', '[bgm]'];
types.forEach((k, ti) => {
  const list = byType[k];
  if (!list.length || !TL.sfxGain[k]) return;
  const inIdx = 2 + ti;
  const g = TL.sfxGain[k];
  const splitOuts = list.map((_, i) => `[${k}${i}]`).join('');
  fc += `[${inIdx}:a]volume=${g},aresample=48000,asplit=${list.length}${splitOuts};`;
  list.forEach((s, i) => {
    fc += `[${k}${i}]adelay=${Math.round(s.t * 1000)}:all=1[${k}${i}d];`;
    mixIns.push(`[${k}${i}d]`);
  });
});
fc += `${mixIns.join('')}amix=inputs=${mixIns.length}:normalize=0,alimiter=limit=0.95[aout]`;

const audioIns = [
  '-i', A('narration.mp3'),    // 1
  '-i', A('sfx_decision.mp3'), // 2
  '-i', A('sfx_ashika.mp3'),   // 3
  '-i', A('sfx_boyon.mp3'),    // 4
  '-i', A('sfx_thump.wav'),    // 5
  '-i', A('sfx_shatter.wav'),  // 6
  '-i', A('sfx_shutter.wav'),  // 7
  '-i', A('bgm.mp3'),          // 8
];
console.log('SFX:', types.map(k => `${k}=${byType[k].length}`).join(' '), '| total', TL.sfx.length);
console.log(`BGM: ${B.db1}dB -> ${B.db2}dB @${st}s / silence ${s0}-${s1}s`);

execFileSync('ffmpeg', [
  '-y', '-v', 'error', '-i', O('video_silent.mp4'), ...audioIns,
  '-filter_complex', fc, '-map', '0:v', '-map', '[aout]',
  '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
  '-movflags', '+faststart', '-t', String(TL.DUR), O('philippines_ra10175_final.mp4'),
], { stdio: 'inherit' });
console.log('done -> philippines_ra10175_final.mp4');

execFileSync('ffmpeg', [
  '-y', '-v', 'error', '-i', O('philippines_ra10175_final.mp4'),
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '21',
  '-maxrate', '3600k', '-bufsize', '7200k', '-pix_fmt', 'yuv420p',
  '-c:a', 'copy', '-movflags', '+faststart', O('philippines_ra10175_tiktok.mp4'),
], { stdio: 'inherit' });
console.log('done -> philippines_ra10175_tiktok.mp4');
