// 音声ミックス + 最終MP4（§2/§15/§16）
//  narration : loudnorm -15 LUFS（絶対基準・一切加工しない）
//  BGM       : 2セグメント構成で「1段変更」を作る
//                A: 0〜16.019   こもった軽い緊張感（HPF/LPF）・-19.5dB
//                --- 16.019〜16.252 完全無音（台本指定の黒）---
//                B: 16.252〜末尾 フルバンド・-16.5dB＋区間オートメーション
//                   「10日」で一瞬落とす／「意図」は静かに／オチで上げる
//  SFX       : timeline.js のキューを adelay で配置（13種）
const { execFileSync } = require('child_process');
const path = require('path');
const TL = require('./timeline.js');

const A = p => path.join(__dirname, 'assets', p);
const O = p => path.join(__dirname, 'out', p);

// 入力インデックス： 0=video 1=narration 2..=SFX 15=bgm
const SFX_FILES = [
  ['decision', 'sfx_decision.mp3'], ['ashika', 'sfx_ashika.mp3'], ['boyon', 'sfx_boyon.mp3'],
  ['thump', 'sfx_thump.wav'], ['shatter', 'sfx_shatter.wav'], ['shutter', 'sfx_shutter.wav'],
  ['whoosh', 'sfx_whoosh.wav'], ['riser', 'sfx_riser.wav'], ['scratch', 'sfx_scratch.wav'],
  ['gavel', 'sfx_gavel.wav'], ['stamp', 'sfx_stamp.wav'], ['tick', 'sfx_tick.wav'],
  ['paper', 'sfx_paper.wav'],
];
const BGM_IDX = 2 + SFX_FILES.length;
const BK = TL.BLACK;

let fc = '[1:a]loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[voice];';

// BGM セグメントA（黒の直前で切る）
fc += `[${BGM_IDX}:a]atrim=0:${BK.s},asetpts=PTS-STARTPTS,`
  + 'highpass=f=220,lowpass=f=2800,volume=-19.5dB,'
  + `afade=t=in:st=0:d=1.6,afade=t=out:st=${(BK.s - 0.18).toFixed(3)}:d=0.18[bgmA];`;
// BGM セグメントB（黒の直後から。区間ごとに音量オートメーション）
const vexpr = [
  `if(between(t,33.85,34.55),0.045,`,           // 「10日」で一瞬落とす
  `if(lt(t,35.40),1.0,`,                        // Bongalon
  `if(lt(t,40.50),0.52,`,                       // 「意図」＝低く静かに
  `if(lt(t,45.72),0.80,1.45))))`,               // オチ＝impact
].join('');
fc += `[${BGM_IDX}:a]atrim=${BK.e}:${TL.DUR},asetpts=PTS-STARTPTS,adelay=${Math.round(BK.e * 1000)}:all=1,`
  + `volume='${vexpr}':eval=frame,volume=-16.5dB,`
  + `afade=t=in:st=${BK.e}:d=0.30,afade=t=out:st=51.10:d=0.85[bgmB];`;
fc += '[bgmA][bgmB]amix=inputs=2:normalize=0[bgm];';

const mixIns = ['[voice]', '[bgm]'];
SFX_FILES.forEach(([key], i) => {
  const list = TL.sfx.filter(s => s.k === key);
  const g = TL.sfxGain[key];
  if (!list.length || !g) return;
  const idx = 2 + i;
  const outs = list.map((_, j) => `[${key}${j}]`).join('');
  fc += `[${idx}:a]volume=${g},aresample=48000,asplit=${list.length}${outs};`;
  list.forEach((s, j) => {
    fc += `[${key}${j}]adelay=${Math.round(s.t * 1000)}:all=1[${key}${j}d];`;
    mixIns.push(`[${key}${j}d]`);
  });
});
fc += `${mixIns.join('')}amix=inputs=${mixIns.length}:normalize=0,alimiter=limit=0.95[aout]`;

const audioIns = ['-i', A('narration.mp3')];
for (const [, f] of SFX_FILES) audioIns.push('-i', A(f));
audioIns.push('-i', A('bgm.mp3'));

console.log('SFX cues:', TL.sfx.length, '/ inputs:', SFX_FILES.length);

// 高品質マスター（映像は再エンコードしない）
execFileSync('ffmpeg', [
  '-y', '-v', 'error', '-i', O('video_silent.mp4'), ...audioIns,
  '-filter_complex', fc, '-map', '0:v', '-map', '[aout]',
  '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
  '-movflags', '+faststart', '-t', String(TL.DUR), O('master.mp4'),
], { stdio: 'inherit' });
console.log('done -> out/master.mp4');

// 納品用（TikTok/Reels/Shorts へそのまま投稿できる状態・30MiB以下）
execFileSync('ffmpeg', [
  '-y', '-v', 'error', '-i', O('master.mp4'),
  '-c:v', 'libx264', '-profile:v', 'high', '-level', '4.0', '-preset', 'slow',
  '-crf', '20', '-maxrate', '3600k', '-bufsize', '7200k',
  '-pix_fmt', 'yuv420p', '-r', String(TL.FPS), '-g', '60',
  '-c:a', 'copy', '-movflags', '+faststart',
  O('RA7610_Bongalon_TikTok_FINAL.mp4'),
], { stdio: 'inherit' });
console.log('done -> out/RA7610_Bongalon_TikTok_FINAL.mp4');
