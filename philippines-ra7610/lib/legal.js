// legal：法律資料・判例資料のレイヤー
// §18 長文をそのまま出さない。重要部分だけをズーム／マーカー／枠で読ませる。
(function () {
'use strict';
const C = window.CORE, W = C.W, H = C.H;

// RA 7610 条文カード（Sec.10(a) の該当箇所に蛍光ペン）
// o:{t,t0,x,y,scale,hlT(ハイライト開始),zoomT}
function ra7610Doc(t, o) {
  const ctx = C.ctx;
  const p = C.popIn(t, o.t0, .22); if (p <= 0) return;
  const s = (o.scale || 1) * p * C.outSc(t, o.outT === undefined ? 1e9 : o.outT);
  if (s <= 0) return;
  const w = 700, h = 470;
  ctx.save(); ctx.translate(o.x, o.y); ctx.rotate(o.rot || -.012); ctx.scale(s, s);
  ctx.fillStyle = 'rgba(0,0,0,0.55)'; C.rr(-w / 2 + 8, -h / 2 + 10, w, h, 12); ctx.fill();
  ctx.fillStyle = '#F3EFE2'; C.rr(-w / 2, -h / 2, w, h, 12); ctx.fill();
  // ヘッダ
  ctx.fillStyle = '#20263C'; C.rr(-w / 2, -h / 2, w, 82, 12); ctx.fill();
  ctx.fillRect(-w / 2, -h / 2 + 60, w, 22);
  C.label('REPUBLIC ACT NO. 7610', 0, -h / 2 + 30, 30, '#fff', 'center', 900);
  C.label('Special Protection of Children Against Abuse', 0, -h / 2 + 62, 18, 'rgba(255,255,255,0.72)', 'center', 600);
  // 本文（読ませない。塊で見せる）
  ctx.fillStyle = '#9AA0B4';
  const rows = [[.94, 1], [.72, 1], [.88, 1], [.55, 1]];
  let yy = -h / 2 + 108;
  for (const [rw] of rows) { C.rr(-w / 2 + 40, yy, (w - 80) * rw, 13, 6); ctx.fill(); yy += 30; }
  // Section 10(a) 行（ここだけ読ませる）
  const hl = o.hlT !== undefined ? C.clamp((t - o.hlT) / .5, 0, 1) : 0;
  const lineY = yy + 22;
  if (hl > 0) {
    ctx.fillStyle = 'rgba(255,207,63,0.55)';
    ctx.fillRect(-w / 2 + 36, lineY - 26, (w - 72) * C.easeOutCubic(hl), 56);
  }
  C.label('SEC. 10 (a)  Other Acts of Child Abuse', -w / 2 + 44, lineY, 27, '#1A2033', 'left', 900);
  yy = lineY + 46;
  ctx.fillStyle = '#9AA0B4';
  for (const rw of [.9, .66]) { C.rr(-w / 2 + 40, yy, (w - 80) * rw, 13, 6); ctx.fill(); yy += 30; }
  // 刑（枠で囲う）
  const pen = o.penT !== undefined ? C.popIn(t, o.penT, .2) : 0;
  if (pen > 0) {
    ctx.save(); ctx.globalAlpha = pen;
    ctx.strokeStyle = C.COL.r; ctx.lineWidth = 5;
    C.rr(-w / 2 + 36, yy + 6, w - 72, 66, 10); ctx.stroke();
    C.label('prisión mayor  in its minimum period', 0, yy + 40, 26, '#B3261E', 'center', 900);
    ctx.restore();
  }
  ctx.restore();
}

// CASE FILE カード（左上）＋事件情報を順に出す
// o:{t, tFile, tName, tGr, tDate, outT}
function caseFile(t, o) {
  const ctx = C.ctx;
  const a = C.fadeIn(t, o.tFile, .2) * C.outSc(t, o.outT === undefined ? 1e9 : o.outT, .2);
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a;
  // タグ
  const bl = .55 + .45 * Math.sin(t * 6);
  ctx.fillStyle = 'rgba(255,66,52,0.92)'; C.rr(90, 250, 232, 56, 8); ctx.fill();
  C.label('CASE FILE', 206, 279, 30, '#fff', 'center', 900);
  ctx.globalAlpha = a * bl;
  ctx.fillStyle = C.COL.r; ctx.beginPath(); ctx.arc(348, 278, 9, 0, 7); ctx.fill();
  ctx.globalAlpha = a;
  ctx.restore();
  // 事件名・番号・日付（1行ずつ）
  const rows = [
    { tt: o.tName, txt: 'Bongalon v. People', size: 52, y: 372, col: '#fff', font: C.SERIF },
    { tt: o.tGr, txt: 'G.R. No. 169533', size: 36, y: 434, col: 'rgba(226,232,248,0.9)' },
    { tt: o.tDate, txt: 'March 20, 2013', size: 32, y: 484, col: 'rgba(226,232,248,0.68)' },
  ];
  for (const r of rows) {
    if (r.tt === undefined) continue;
    const p = C.clamp((t - r.tt) / .22, 0, 1); if (p <= 0) continue;
    ctx.save(); ctx.globalAlpha = a * p;
    ctx.font = `900 ${r.size}px ${r.font || C.SANS}`;
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.translate(96 + (1 - C.easeOutCubic(p)) * -28, r.y);
    ctx.lineJoin = 'round'; ctx.strokeStyle = C.COL.ink; ctx.lineWidth = r.size * .16;
    ctx.strokeText(r.txt, 0, 0); ctx.fillStyle = r.col; ctx.fillText(r.txt, 0, 0);
    ctx.restore();
  }
}

// 判決書（木槌の後に出す紙）
function judgment(t, t0, x, y, s, titleTxt, outT) {
  const ctx = C.ctx;
  const p = C.popIn(t, t0, .2); if (p <= 0) return;
  const sc = s * p * C.outSc(t, outT === undefined ? 1e9 : outT);
  if (sc <= 0) return;
  const w = 500, h = 320;
  ctx.save(); ctx.translate(x, y); ctx.rotate(.02); ctx.scale(sc, sc);
  ctx.fillStyle = 'rgba(0,0,0,0.5)'; C.rr(-w / 2 + 7, -h / 2 + 9, w, h, 10); ctx.fill();
  ctx.fillStyle = '#F3EFE2'; C.rr(-w / 2, -h / 2, w, h, 10); ctx.fill();
  ctx.fillStyle = '#20263C'; C.rr(-w / 2, -h / 2, w, 62, 10); ctx.fill(); ctx.fillRect(-w / 2, -h / 2 + 44, w, 18);
  C.label(titleTxt, 0, -h / 2 + 28, 30, '#fff', 'center', 900);
  ctx.fillStyle = '#9AA0B4';
  let yy = -h / 2 + 92;
  for (const rw of [.88, .6, .8]) { C.rr(-w / 2 + 34, yy, (w - 68) * rw, 12, 6); ctx.fill(); yy += 28; }
  ctx.restore();
}

// 木槌（判決の合図）。t0で振り下ろす
function gavel(t, t0, x, y, s) {
  const ctx = C.ctx;
  const p = C.popIn(t, t0 - .35, .25); if (p <= 0) return;
  let ang;
  const T1 = t0;
  if (t < T1) ang = C.lerp(-.66, .04, C.easeInQuad(C.clamp((t - (T1 - .3)) / .3, 0, 1)));
  else ang = .04 + .3 * Math.pow(2.71, -(t - T1) * 4.5) * Math.cos((t - T1) * 17);
  ctx.save(); ctx.translate(x, y); ctx.scale(s * p, s * p);
  ctx.fillStyle = '#6E441F'; C.rr(-300, 110, 190, 26, 8); ctx.fill();
  ctx.fillStyle = '#8A5A2B'; C.rr(-268, 80, 124, 32, 8); ctx.fill();
  ctx.save(); ctx.rotate(ang);
  ctx.fillStyle = '#8A5A2B'; C.rr(-190, -10, 182, 20, 10); ctx.fill();
  ctx.save(); ctx.translate(-208, 0);
  ctx.fillStyle = '#A9743C'; C.rr(-40, -70, 80, 140, 16); ctx.fill();
  ctx.fillStyle = '#C08A4C'; C.rr(-40, -70, 80, 24, 12); ctx.fill();
  ctx.fillStyle = '#7C4E22'; C.rr(-40, 46, 80, 24, 12); ctx.fill();
  ctx.restore();
  ctx.fillStyle = '#C08A4C'; ctx.beginPath(); ctx.arc(0, 0, 14, 0, 7); ctx.fill();
  ctx.restore(); ctx.restore();
}

// 刑期レンジバー（6年1日〜8年 → 10日 に縮む演出用）
// o:{t,t0, from:'6年1日', to:'8年', shrinkT, w}
function penaltyBar(t, o) {
  const ctx = C.ctx;
  const p = C.popIn(t, o.t0, .25); if (p <= 0) return;
  let k = 1; // 1=満幅
  if (o.shrinkT !== undefined && t > o.shrinkT) k = C.lerp(1, .045, C.easeInOut(C.clamp((t - o.shrinkT) / .95, 0, 1)));
  const w = (o.w || 780) * k;
  const a = C.outSc(t, o.outT === undefined ? 1e9 : o.outT); if (a <= 0) return;
  ctx.save(); ctx.translate(W / 2, o.y); ctx.globalAlpha = a; ctx.scale(p, p);
  ctx.fillStyle = 'rgba(255,255,255,0.10)'; C.rr(-390, -26, 780, 52, 26); ctx.fill();
  const grd = ctx.createLinearGradient(-w / 2, 0, w / 2, 0);
  grd.addColorStop(0, '#FF4234'); grd.addColorStop(1, '#FF8A3D');
  ctx.fillStyle = k > .3 ? grd : C.COL.b;
  C.rr(-w / 2, -26, w, 52, 26); ctx.fill();
  if (k > .5) {
    C.label(o.from, -w / 2 + 8, -58, 30, 'rgba(255,255,255,0.85)', 'left', 900);
    C.label(o.to, w / 2 - 8, -58, 30, 'rgba(255,255,255,0.85)', 'right', 900);
  }
  ctx.restore();
}

window.LEGAL = { ra7610Doc, caseFile, judgment, gavel, penaltyBar };
})();
