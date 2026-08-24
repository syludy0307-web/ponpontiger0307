// illustration：再現イラスト（シルエット）
// ★方針：暴力を生々しく描かない。打撃の瞬間は描かず「手が上がる」まででCUT（§7/§12）。
(function () {
'use strict';
const C = window.CORE, W = C.W, H = C.H;

// 大人（立ち姿）。armAngle: 腕の角度（0=下ろす, -1.2=振り上げ）
function adult(t, x, y, s, armAngle, col) {
  const ctx = C.ctx;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = col || '#05070E';
  ctx.strokeStyle = 'rgba(190,210,255,0.20)'; ctx.lineWidth = 4; ctx.lineJoin = 'round';
  // 頭
  ctx.beginPath(); ctx.arc(0, -300, 52, 0, 7); ctx.fill();
  // 胴
  ctx.beginPath();
  ctx.moveTo(-66, 0); ctx.quadraticCurveTo(-58, -210, 0, -232);
  ctx.quadraticCurveTo(58, -210, 66, 0); ctx.closePath(); ctx.fill();
  // 脚
  ctx.beginPath(); C.rr(-56, -10, 44, 190, 20); ctx.fill();
  ctx.beginPath(); C.rr(12, -10, 44, 190, 20); ctx.fill();
  // 腕（振り上げる方）
  ctx.save(); ctx.translate(44, -206); ctx.rotate(armAngle || 0);
  ctx.beginPath(); C.rr(-18, -14, 176, 36, 18); ctx.fill();
  ctx.beginPath(); ctx.arc(158, 4, 26, 0, 7); ctx.fill();
  ctx.restore();
  // もう片方の腕
  ctx.save(); ctx.translate(-44, -206); ctx.rotate(.35);
  ctx.beginPath(); C.rr(-24, -12, 30, 150, 15); ctx.fill();
  ctx.restore();
  ctx.restore();
}

// 子ども（小さい・うつむき）※暗背景でも輪郭が読めるようリムライト付き
function child(t, x, y, s, col) {
  const ctx = C.ctx;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = col || '#28365C';
  ctx.strokeStyle = 'rgba(190,210,255,0.42)'; ctx.lineWidth = 5; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.arc(0, -168, 44, 0, 7); ctx.fill(); ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(-48, 0); ctx.quadraticCurveTo(-42, -116, 0, -130);
  ctx.quadraticCurveTo(42, -116, 48, 0); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.beginPath(); C.rr(-40, -8, 32, 118, 15); ctx.fill(); ctx.stroke();
  ctx.beginPath(); C.rr(8, -8, 32, 118, 15); ctx.fill(); ctx.stroke();
  ctx.restore();
}

// 【1】手が上がる → CUT（打撃は描かない）
// t0で腕が上がり始め、t0+0.45で最高点。それ以降は呼び出し側でCUTする。
function handRaise(t, t0) {
  const p = C.clamp((t - t0) / .45, 0, 1);
  const ang = C.lerp(0, -1.25, C.easeOutCubic(p));
  const push = C.lerp(1.0, 1.06, p);
  const ctx = C.ctx;
  ctx.save();
  ctx.translate(W / 2, H / 2); ctx.scale(push, push); ctx.translate(-W / 2, -H / 2);
  adult(t, 700, 1460, .92, ang);
  child(t, 380, 1470, .88);
  ctx.restore();
  // 手の軌跡（動きの示唆のみ）
  if (p > .25) {
    ctx.save(); ctx.globalAlpha = .35 * (1 - Math.abs(p - .6) * 2);
    ctx.strokeStyle = 'rgba(255,255,255,0.8)'; ctx.lineWidth = 7; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.arc(740, 1270, 190, -0.4, -1.25 * p - 0.4, true); ctx.stroke();
    ctx.restore();
  }
}

// 【4】再現カット：kind 'back'（背中）/ 'cheek'（頬）
// ※接触の瞬間は描かない。大人の腕は「向かう」ところで止め、対象部位をマーカーで示す。
function reenact(t, t0, kind) {
  const ctx = C.ctx;
  const p = C.clamp((t - t0) / .5, 0, 1);
  const zz = C.lerp(1.10, 1.0, C.easeOutCubic(p));
  ctx.save();
  ctx.translate(W / 2, 1050); ctx.scale(zz, zz); ctx.translate(-W / 2, -1050);
  // 子ども（左）と大人（右）の2人構図。footline = 1210
  child(t, 386, 1206, .96);
  ctx.save();
  ctx.translate(742, 1206); ctx.scale(.74, .74); ctx.translate(-742, -1206);
  adult(t, 742, 1206, 1.0, C.lerp(-1.15, -.62, C.easeOutCubic(p)), '#161E33');
  ctx.restore();
  // 対象部位のマーカー（円＋引き出し線＋ラベル）
  const mk = kind === 'back' ? { x: 392, y: 1142, txt: '背中' } : { x: 356, y: 1034, txt: '頬' };
  const mp = C.clamp((t - t0 - .2) / .3, 0, 1);
  if (mp > 0) {
    ctx.save(); ctx.globalAlpha = mp;
    ctx.strokeStyle = C.COL.r; ctx.lineWidth = 5; ctx.setLineDash([12, 9]);
    ctx.beginPath(); ctx.arc(mk.x, mk.y, 52 * (2 - mp), 0, 7); ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(mk.x - 46, mk.y - 30); ctx.lineTo(mk.x - 150, mk.y - 96); ctx.stroke();
    ctx.font = `900 40px ${C.SANS}`; ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round'; ctx.strokeStyle = C.COL.ink; ctx.lineWidth = 9;
    ctx.strokeText(mk.txt, mk.x - 162, mk.y - 100);
    ctx.fillStyle = C.COL.r; ctx.fillText(mk.txt, mk.x - 162, mk.y - 100);
    ctx.restore();
  }
  ctx.restore();
}

// 【3】言葉だけでも成立：吹き出し＋子どもシルエット
function words(t, t0) {
  const ctx = C.ctx;
  const p = C.popIn(t, t0, .24); if (p <= 0) return;
  const cx = 300, cy = 1300;
  // 波紋（言葉が届く）※子どもの頭部を中心に
  for (let i = 0; i < 3; i++) {
    const rp = C.fract((t - t0) * .8 + i / 3);
    ctx.save(); ctx.globalAlpha = (1 - rp) * .30;
    ctx.strokeStyle = C.COL.r; ctx.lineWidth = 5;
    ctx.beginPath(); ctx.arc(cx, cy - 168, 60 + rp * 230, 0, 7); ctx.stroke(); ctx.restore();
  }
  child(t, cx, cy, 1.0);
  ctx.save(); ctx.translate(672, 930); ctx.scale(p, p);
  ctx.fillStyle = 'rgba(0,0,0,0.45)'; C.rr(-218, -92, 452, 196, 42); ctx.fill();
  ctx.fillStyle = '#F2F5FF'; C.rr(-224, -100, 452, 196, 42); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-142, 88); ctx.lineTo(-260, 214); ctx.lineTo(-46, 92); ctx.closePath(); ctx.fill();
  // 言葉＝棘のある線（内容は描かない）
  ctx.fillStyle = '#FF4234';
  for (let i = 0; i < 3; i++) { C.rr(-170, -58 + i * 50, [336, 246, 296][i], 22, 11); ctx.fill(); }
  ctx.restore();
}

// 【5】DEBASE / DEGRADE / DEMEAN
const DEG = [
  { w: 'DEBASE', x: 250, y: 780 },
  { w: 'DEGRADE', x: 790, y: 900 },
  { w: 'DEMEAN', x: 300, y: 1080 },
];
function degradeWords(t, times) {
  const ctx = C.ctx;
  for (let i = 0; i < DEG.length; i++) {
    const tt = times[i]; if (t < tt) continue;
    const p = C.popIn(t, tt, .2);
    ctx.save(); ctx.translate(DEG[i].x, DEG[i].y); ctx.scale(p, p);
    ctx.rotate(Math.sin(t * 1.5 + i) * .02);
    ctx.font = `900 46px ${C.SANS}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round'; ctx.strokeStyle = C.COL.ink; ctx.lineWidth = 10;
    ctx.strokeText(DEG[i].w, 0, 0);
    ctx.fillStyle = 'rgba(255,207,63,0.92)'; ctx.fillText(DEG[i].w, 0, 0);
    ctx.restore();
  }
}

// 【5】繰り返し：1回→2回→3回 が積み上がる
function repeatStack(t, times) {
  const ctx = C.ctx;
  for (let i = 0; i < times.length; i++) {
    const tt = times[i]; if (t < tt) continue;
    const p = C.popIn(t, tt, .18);
    const y = 1230 - i * 118;
    ctx.save(); ctx.translate(W / 2, y); ctx.scale(p, p);
    ctx.fillStyle = 'rgba(8,11,24,0.86)'; C.rr(-190, -46, 380, 92, 20); ctx.fill();
    ctx.strokeStyle = i === 2 ? C.COL.r : 'rgba(255,255,255,0.55)'; ctx.lineWidth = 5;
    C.rr(-190, -46, 380, 92, 20); ctx.stroke();
    ctx.font = `900 50px ${C.SANS}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round'; ctx.strokeStyle = C.COL.ink; ctx.lineWidth = 9;
    ctx.strokeText(`${i + 1}回目`, 0, 2);
    ctx.fillStyle = i === 2 ? C.COL.r : '#fff'; ctx.fillText(`${i + 1}回目`, 0, 2);
    ctx.restore();
  }
}

window.ILLUST = { adult, child, handRaise, reenact, words, degradeWords, repeatStack };
})();
