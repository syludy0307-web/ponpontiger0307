// typography：巨大テロップ・スタンプ・チップ・カウンタ
(function () {
'use strict';
const C = window.CORE, W = C.W, H = C.H;

// 巨大テロップ。in: 'slam'(叩き込み) | 'punch'(急接近) | 'pop' | 'rise'
// L: {txt,size,y,fill:'white|red|gold|blue',rot,font}
function mega(lines, o) {
  const ctx = C.ctx;
  const baseX = o.x !== undefined ? o.x : W / 2;
  const t = o.t, t0 = o.t0, kind = o.in || 'slam';
  const dur = o.dur || (kind === 'slam' ? .13 : kind === 'punch' ? .22 : .3);
  const sp = (t - t0) / dur;
  if (sp < 0) return;
  let s = 1, al = 1;
  if (kind === 'slam') { const k = sp >= 1 ? 1 : C.easeOutQuint(C.clamp(sp, 0, 1)); s = 2.6 - 1.6 * k; al = C.clamp(sp * 3, 0, 1); }
  else if (kind === 'punch') { const k = sp >= 1 ? 1 : C.easeOutCubic(C.clamp(sp, 0, 1)); s = 0.55 + 0.45 * k; al = C.clamp(sp * 4, 0, 1); }
  else if (kind === 'pop') { s = sp >= 1 ? 1 : C.easeOutBack(C.clamp(sp, 0, 1), 1.6); al = C.clamp(sp * 3, 0, 1); }
  else { s = 1; al = C.clamp(sp * 2, 0, 1); }
  if (o.outT !== undefined) { const os = C.outSc(t, o.outT, o.outDur || .16); if (os <= 0) return; s *= os; al *= os; }
  const breathe = o.still ? 1 : 1 + 0.012 * Math.sin(t * 2.1);
  for (const L of lines) {
    ctx.save();
    ctx.translate(baseX + (L.dx || 0), L.y + (o.still ? 0 : Math.sin(t * 2.3 + L.y) * 3));
    ctx.rotate(L.rot || 0);
    ctx.scale(s * breathe, s * breathe);
    ctx.globalAlpha = al * (o.alpha !== undefined ? o.alpha : 1);
    ctx.font = `900 ${L.size}px ${L.font || C.SANS}`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    // はみ出し防止（セーフゾーン内に収める）
    const tw = ctx.measureText(L.txt).width;
    const maxW = (o.maxW || 850);
    if (tw > maxW) ctx.scale(maxW / tw, 1);
    ctx.strokeStyle = C.COL.ink; ctx.lineWidth = L.size * .23; ctx.strokeText(L.txt, 0, 0);
    if (L.fill !== 'white') { ctx.strokeStyle = '#fff'; ctx.lineWidth = L.size * .075; ctx.strokeText(L.txt, 0, 0); }
    ctx.fillStyle = L.fill === 'red' ? C.COL.r
      : L.fill === 'gold' ? C.goldGrad(-L.size * .55, L.size * .55)
      : L.fill === 'blue' ? C.COL.b : '#fff';
    ctx.fillText(L.txt, 0, 0);
    ctx.restore();
  }
}

// ハンコ風スタンプ（tone: 'red'|'white'|'blue'|'gold'）
function stamp(t, t0, x, y, w, h, txt, size, tone, outT) {
  const ctx = C.ctx;
  const p = C.popIn(t, t0, .14); if (p <= 0) return;
  const sc = (2.3 - 1.3 * C.clamp(p, 0, 1)) * C.outSc(t, outT === undefined ? 1e9 : outT);
  if (sc <= 0) return;
  const col = tone === 'white' ? '#EFF3FF' : tone === 'blue' ? C.COL.b : tone === 'gold' ? C.COL.g : C.COL.r;
  const bg = tone === 'red' ? 'rgba(120,10,15,0.30)' : 'rgba(6,9,22,0.42)';
  ctx.save(); ctx.translate(x, y); ctx.rotate(-.075); ctx.scale(sc, sc);
  ctx.globalAlpha = C.clamp((t - t0) * 7, 0, 1) * .97;
  ctx.fillStyle = bg; C.rr(-w / 2, -h / 2, w, h, 16); ctx.fill();
  ctx.strokeStyle = col; ctx.lineWidth = 9; C.rr(-w / 2, -h / 2, w, h, 16); ctx.stroke();
  ctx.strokeStyle = col.replace(')', ',0.5)').replace('#', 'rgba(') === col ? col : col;
  ctx.globalAlpha *= .55; ctx.lineWidth = 4; C.rr(-w / 2 + 12, -h / 2 + 12, w - 24, h - 24, 11); ctx.stroke();
  ctx.globalAlpha = C.clamp((t - t0) * 7, 0, 1) * .97;
  ctx.font = `900 ${size}px ${C.SERIF}`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  const tw = ctx.measureText(txt).width;
  if (tw > w - 44) ctx.scale((w - 44) / tw, 1);
  ctx.strokeStyle = C.COL.ink; ctx.lineWidth = size * .15; ctx.strokeText(txt, 0, 3);
  ctx.fillStyle = col; ctx.fillText(txt, 0, 3);
  ctx.restore();
}

// ピル（角丸ラベル）
function pill(t, t0, x, y, txt, size, border, fill, opt) {
  const ctx = C.ctx; opt = opt || {};
  const p = C.popIn(t, t0, .18); if (p <= 0) return;
  const o = C.outSc(t, opt.outT === undefined ? 1e9 : opt.outT); if (o <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(p * o, p * o);
  ctx.font = `900 ${size}px ${opt.font || C.SANS}`;
  const pw = ctx.measureText(txt).width + (opt.pad || 100);
  ctx.fillStyle = opt.bg || 'rgba(6,9,22,0.86)';
  C.rr(-pw / 2, -size * 1.02, pw, size * 2.04, size * 1.02); ctx.fill();
  ctx.strokeStyle = border; ctx.lineWidth = 6;
  C.rr(-pw / 2, -size * 1.02, pw, size * 2.04, size * 1.02); ctx.stroke();
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  ctx.strokeStyle = C.COL.ink; ctx.lineWidth = size * .15; ctx.strokeText(txt, 0, 2);
  ctx.fillStyle = fill === 'gold' ? C.goldGrad(-size, size) : fill;
  ctx.fillText(txt, 0, 2); ctx.restore();
}

// 条件チップ（✓ / × 付き）: state 'none'|'ok'|'ng'
function condChip(t, o) {
  const ctx = C.ctx;
  const p = C.popIn(t, o.tIn, .18); if (p <= 0) return;
  const s = (o.scale || 1) * p * C.outSc(t, o.outT === undefined ? 1e9 : o.outT);
  if (s <= 0) return;
  const w = o.w || 360, h = 108;
  const ng = o.tNg !== undefined && t > o.tNg;
  const ok = o.tOk !== undefined && t > o.tOk;
  ctx.save(); ctx.translate(o.x, o.y); ctx.scale(s, s);
  ctx.globalAlpha = ng ? C.lerp(1, .62, C.clamp((t - o.tNg) / .3, 0, 1)) : 1;
  ctx.fillStyle = 'rgba(8,11,24,0.82)'; C.rr(-w / 2, -h / 2, w, h, 22); ctx.fill();
  ctx.strokeStyle = ng ? 'rgba(255,66,52,0.9)' : ok ? 'rgba(70,224,160,0.9)' : 'rgba(220,228,255,0.5)';
  ctx.lineWidth = 5; C.rr(-w / 2, -h / 2, w, h, 22); ctx.stroke();
  ctx.font = `900 44px ${C.SANS}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
  ctx.lineJoin = 'round'; ctx.strokeStyle = C.COL.ink; ctx.lineWidth = 8;
  ctx.strokeText(o.txt, -w / 2 + 92, 2);
  ctx.fillStyle = ng ? 'rgba(255,255,255,0.55)' : '#fff'; ctx.fillText(o.txt, -w / 2 + 92, 2);
  // ✓
  if (ok) {
    const cp = C.clamp((t - o.tOk) / .2, 0, 1);
    ctx.save(); ctx.translate(-w / 2 + 50, 0); ctx.scale(cp, cp);
    ctx.globalAlpha = ng ? .45 : 1;
    ctx.strokeStyle = C.COL.ok; ctx.lineWidth = 11; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(-19, 2); ctx.lineTo(-5, 18); ctx.lineTo(21, -18); ctx.stroke();
    ctx.restore();
  }
  // ×：文字を潰さないよう「取り消し線＋右端の×バッジ」で表現
  if (ng) {
    const xp = C.clamp((t - o.tNg) / .2, 0, 1);
    ctx.save();
    ctx.strokeStyle = C.COL.r; ctx.lineWidth = 9; ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(-w / 2 + 22, 14);
    ctx.lineTo(-w / 2 + 22 + (w - 44) * C.easeOutCubic(xp), -14);
    ctx.stroke();
    // 右端の×バッジ（叩き込み）
    const bs = (2.0 - 1.0 * C.easeOutQuad(xp));
    ctx.translate(w / 2 - 34, 0); ctx.scale(bs, bs); ctx.globalAlpha = xp;
    ctx.fillStyle = C.COL.r; ctx.beginPath(); ctx.arc(0, 0, 25, 0, 7); ctx.fill();
    ctx.strokeStyle = '#12060A'; ctx.lineWidth = 8;
    ctx.beginPath(); ctx.moveTo(-10, -10); ctx.lineTo(10, 10); ctx.moveTo(10, -10); ctx.lineTo(-10, 10); ctx.stroke();
    ctx.restore();
  }
  ctx.restore();
}

// 大きな赤×（単体）
function bigX(t, t0, x, y, size, outT) {
  const ctx = C.ctx;
  const sp = (t - t0) / .12; if (sp < 0) return;
  const k = sp >= 1 ? 1 : C.easeOutQuint(C.clamp(sp, 0, 1));
  const sc = (2.7 - 1.7 * k) * C.outSc(t, outT === undefined ? 1e9 : outT);
  if (sc <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(-.05 + Math.sin(t * 2) * .01); ctx.scale(sc, sc);
  ctx.globalAlpha = C.clamp(sp * 3, 0, 1); ctx.lineCap = 'round';
  ctx.strokeStyle = C.COL.ink; ctx.lineWidth = size * .32;
  ctx.beginPath(); ctx.moveTo(-size / 2, -size / 2); ctx.lineTo(size / 2, size / 2);
  ctx.moveTo(size / 2, -size / 2); ctx.lineTo(-size / 2, size / 2); ctx.stroke();
  ctx.strokeStyle = C.COL.r; ctx.lineWidth = size * .2;
  ctx.beginPath(); ctx.moveTo(-size / 2, -size / 2); ctx.lineTo(size / 2, size / 2);
  ctx.moveTo(size / 2, -size / 2); ctx.lineTo(-size / 2, size / 2); ctx.stroke();
  ctx.restore();
}

// 数値カウンタ（減少演出用）。fmt(v)で文字列化
function counter(t, t0, dur, from, to, x, y, size, fill, fmt, ease) {
  const p = C.clamp((t - t0) / dur, 0, 1);
  const e = ease === 'out' ? C.easeOutCubic(p) : p;
  const v = C.lerp(from, to, e);
  mega([{ txt: fmt(v), size, y, fill }], { t, t0, in: 'rise', x, still: true });
  return v;
}

// 小さな注記（法的な誤解防止の補助字幕）
function note(t, t0, txt, y, alpha) {
  const a = C.fadeIn(t, t0, .45) * (alpha === undefined ? 1 : alpha);
  if (a <= 0) return;
  const ctx = C.ctx;
  ctx.save(); ctx.globalAlpha = a * .85;
  ctx.font = `600 26px ${C.SANS}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  const tw = ctx.measureText(txt).width;
  ctx.fillStyle = 'rgba(5,7,16,0.7)'; C.rr(W / 2 - tw / 2 - 22, y - 22, tw + 44, 44, 22); ctx.fill();
  ctx.fillStyle = 'rgba(226,232,248,0.92)'; ctx.fillText(txt, W / 2, y + 1);
  ctx.restore();
}

window.TYPO = { mega, stamp, pill, condChip, bigX, counter, note };
})();
