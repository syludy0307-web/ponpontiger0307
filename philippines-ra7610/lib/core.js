// core：数値ユーティリティ・カラー・テキストエンジン・インパクト・写真描画
// 依存なし。他の lib/*.js と render.html から window.CORE で参照する。
(function () {
'use strict';

const TL = window.TIMELINE;
const W = TL.W, H = TL.H;

// ---- 数値 ----
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, p) => a + (b - a) * p;
const fract = x => x - Math.floor(x);
const rnd = i => fract(Math.sin(i * 127.1 + 311.7) * 43758.5453);
const easeInQuad = p => p * p;
const easeOutQuad = p => 1 - (1 - p) * (1 - p);
const easeInOut = p => (p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2);
const easeOutCubic = p => 1 - Math.pow(1 - p, 3);
const easeOutQuint = p => 1 - Math.pow(1 - p, 5);
const easeOutBack = (p, s = 2.2) => { const c = s + 1; return 1 + c * Math.pow(p - 1, 3) + s * Math.pow(p - 1, 2); };
const easeOutElastic = p => (p <= 0 ? 0 : p >= 1 ? 1 : Math.pow(2, -10 * p) * Math.sin((p * 10 - 0.75) * (2 * Math.PI / 3)) + 1);

// 進行度ヘルパ（t0で開始し dur で1になる）
const prog = (t, t0, dur) => clamp((t - t0) / dur, 0, 1);
const popIn = (t, t0, dur = .2) => { const p = (t - t0) / dur; return p <= 0 ? 0 : p >= 1 ? 1 : easeOutBack(p); };
const fadeIn = (t, t0, dur = .4) => clamp((t - t0) / dur, 0, 1);
const outSc = (t, tEnd, dur = .16) => { if (t < tEnd) return 1; const p = (t - tEnd) / dur; return p >= 1 ? 0 : 1 - easeInQuad(p); };
// 窓：t0〜t1の間だけ1、前後でフェード
const win = (t, t0, t1, fi = .18, fo = .18) => clamp((t - t0) / fi, 0, 1) * clamp((t1 - t) / fo, 0, 1);

// ---- カラー（§22：黒白ベース＋金=法律／赤=刑罰／青=逆転）----
const COL = {
  w: '#FFFFFF', r: '#FF4234', g: '#FFCF3F', b: '#6FD2FF', k: '#0A0C14',
  ink: '#08090F', ok: '#46E0A0',
  phBlue: '#0E4BC3', phRed: '#D6203A', phYellow: '#FCD116',
};
const SANS = '"Noto Sans CJK JP"', SERIF = '"Noto Serif CJK JP"';

// ---- 描画プリミティブ ----
let ctx = null;
function bind(c) { ctx = c; }
function rr(x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}
function goldGrad(y0, y1) {
  const g = ctx.createLinearGradient(0, y0, 0, y1);
  g.addColorStop(0, '#FFF3B0'); g.addColorStop(.45, '#FFD34D');
  g.addColorStop(.55, '#F7A928'); g.addColorStop(1, '#FFCE45'); return g;
}
const mCache = new Map();
function chW(font, ch) {
  const k = font + '|' + ch; let v = mCache.get(k);
  if (v === undefined) { ctx.font = font; v = ctx.measureText(ch).width; mCache.set(k, v); }
  return v;
}

// ---- テキストエンジン（1文字ずつポップ／セグメント色分け）----
// segs: [{t:'文字列', c:'w|r|g|b'}] , o:{x,y,size,t,t0,stagger,popDur,alpha,strokeW,fixed,font,maxW}
function segText(segs, o) {
  const font = `900 ${o.size}px ${o.font || SANS}`;
  const chars = [];
  for (const s of segs) for (const ch of s.t) chars.push({ ch, c: s.c });
  let total = 0; for (const c of chars) total += chW(font, c.ch);
  let scaleX = 1;
  if (o.maxW && total > o.maxW) scaleX = o.maxW / total;   // はみ出し自動圧縮
  const t = o.t, t0 = o.t0;
  const st = o.stagger !== undefined ? o.stagger : .020, pd = o.popDur || .16;
  ctx.save();
  ctx.translate(o.x !== undefined ? o.x : W / 2, o.y);
  ctx.scale(scaleX, 1);
  ctx.textBaseline = 'middle'; ctx.textAlign = 'center'; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  let cx = -total / 2;
  for (let i = 0; i < chars.length; i++) {
    const c = chars[i], w = chW(font, c.ch);
    let sc = 1, al = 1;
    if (!o.fixed) {
      const p = (t - (t0 + i * st)) / pd;
      if (p <= 0) { cx += w; continue; }
      sc = p >= 1 ? 1 : easeOutBack(p); al = clamp(p * 2.5, 0, 1);
    }
    if (o.kwBounce !== false && c.c !== 'w') sc *= 1 + 0.035 * Math.sin(t * 6 + i * 1.3);
    ctx.save(); ctx.translate(cx + w / 2, 0); ctx.scale(sc, sc);
    ctx.globalAlpha = (o.alpha !== undefined ? o.alpha : 1) * al;
    ctx.font = font;
    ctx.strokeStyle = COL.ink; ctx.lineWidth = (o.strokeW !== undefined ? o.strokeW : o.size * .19);
    ctx.strokeText(c.ch, 0, 0);
    ctx.fillStyle = (c.c === 'g') ? goldGrad(-o.size * .55, o.size * .55) : (COL[c.c] || c.c || '#fff');
    ctx.fillText(c.ch, 0, 0);
    ctx.restore(); cx += w;
  }
  ctx.restore();
  return total * scaleX;
}
// 単純ラベル（アニメなし）
function label(txt, x, y, size, color, align, weight) {
  ctx.save();
  ctx.font = `${weight || 700} ${size}px ${SANS}`;
  ctx.textAlign = align || 'center'; ctx.textBaseline = 'middle';
  ctx.fillStyle = color; ctx.fillText(txt, x, y); ctx.restore();
}

// ---- インパクト（揺れ／フラッシュ／破片／集中線）----
// {t, amp, fl:{c,a}, zoom, bu:{x,y,cols,n,sp}}
const IMPACTS = [];
function addImpacts(list) { for (const im of list) IMPACTS.push(im); }
function shakeOffset(t) {
  let x = 0, y = 0;
  for (const im of IMPACTS) {
    const d = t - im.t;
    if (d > 0 && d < .5 && im.amp) {
      const k = im.amp * Math.pow(1 - d / .5, 2.2), f = Math.floor(t * 60);
      x += (rnd(f * 3.7 + im.t * 91) - .5) * 2 * k;
      y += (rnd(f * 5.3 + im.t * 57) - .5) * 2 * k;
    }
  }
  return { x, y };
}
function shakeZoom(t) {
  let z = 1;
  for (const im of IMPACTS) {
    if (!im.zoom) continue; const d = t - im.t;
    if (d > 0 && d < .55) z += im.zoom * Math.pow(1 - d / .55, 2);
  }
  return z;
}
function drawFlashes(t) {
  for (const im of IMPACTS) {
    if (!im.fl) continue; const d = t - im.t;
    if (d > 0 && d < (im.fl.d || .26)) {
      ctx.fillStyle = `rgba(${im.fl.c},${im.fl.a * (1 - d / (im.fl.d || .26))})`;
      ctx.fillRect(0, 0, W, H);
    }
  }
}
function drawBursts(t) {
  for (const im of IMPACTS) {
    if (!im.bu) continue; const b = im.bu, d = t - im.t;
    if (d > 0 && d < .7) {
      for (let i = 0; i < b.n; i++) {
        const a = rnd(i * 7 + im.t * 13) * Math.PI * 2;
        const sp = b.sp * (0.45 + rnd(i * 3 + 1) * 0.8);
        const pr = easeOutCubic(clamp(d / .7, 0, 1));
        const px = b.x + Math.cos(a) * sp * pr, py = b.y + Math.sin(a) * sp * pr * .85;
        const sz = (4 + rnd(i * 11) * 10) * (1 - pr);
        ctx.fillStyle = b.cols[i % b.cols.length]; ctx.globalAlpha = 1 - pr;
        ctx.save(); ctx.translate(px, py); ctx.rotate(a + pr * 6);
        ctx.fillRect(-sz, -sz * .45, sz * 2, sz * .9); ctx.restore();
      }
      ctx.globalAlpha = 1;
    }
  }
}

// ---- 写真（Ken Burns）----
const IMGS = {};
function setImages(m) { Object.assign(IMGS, m); }
function hasImg(k) { return !!IMGS[k]; }
// o:{fx,fy,z0,z1,t0,t1,rot}
function kb(key, dx, dy, dw, dh, t, o) {
  const img = IMGS[key]; if (!img) return false;
  const iw = img.naturalWidth, ih = img.naturalHeight;
  const p = clamp((t - (o.t0 || 0)) / ((o.t1 || 1) - (o.t0 || 0) || 1), 0, 1);
  const z = lerp(o.z0 !== undefined ? o.z0 : 1.05, o.z1 !== undefined ? o.z1 : 1.2, p);
  const scale = Math.max(dw / iw, dh / ih) * z;
  const sw = dw / scale, sh = dh / scale;
  const fx = o.fx !== undefined ? o.fx : .5, fy = o.fy !== undefined ? o.fy : .5;
  const sx = clamp(fx * iw - sw / 2, 0, Math.max(0, iw - sw));
  const sy = clamp(fy * ih - sh / 2, 0, Math.max(0, ih - sh));
  ctx.drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh);
  return true;
}
// 全画面写真＋トーン（tint: [top,bottom]）
function photoBG(key, t, o, tintTop, tintBot) {
  if (!kb(key, 0, 0, W, H, t, o)) {
    ctx.fillStyle = '#0A0C14'; ctx.fillRect(0, 0, W, H); return false;
  }
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, tintTop || 'rgba(6,8,18,0.62)');
  g.addColorStop(1, tintBot || 'rgba(6,8,18,0.88)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  return true;
}
// 角丸パネル写真（ラベル＋クレジット）
function photoPanel(key, x, y, w, h, t, o, labelTxt, credit, p) {
  if (p === undefined) p = 1; if (p <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(p, p); ctx.rotate(o.rot || 0);
  ctx.fillStyle = 'rgba(0,0,0,0.5)'; rr(-w / 2 + 8, -h / 2 + 10, w, h, 20); ctx.fill();
  rr(-w / 2, -h / 2, w, h, 20); ctx.save(); ctx.clip(); ctx.translate(-w / 2, -h / 2);
  kb(key, 0, 0, w, h, t, o);
  ctx.fillStyle = 'rgba(8,10,22,0.26)'; ctx.fillRect(0, 0, w, h);
  const vg = ctx.createLinearGradient(0, h * .5, 0, h);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.6)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, w, h);
  if (credit) label(credit, w - 14, h - 16, 21, 'rgba(255,255,255,0.55)', 'right', 500);
  ctx.restore();
  ctx.strokeStyle = 'rgba(255,255,255,0.8)'; ctx.lineWidth = 5; rr(-w / 2, -h / 2, w, h, 20); ctx.stroke();
  if (labelTxt) {
    ctx.font = `900 34px ${SANS}`;
    const lw = ctx.measureText(labelTxt).width + 56;
    ctx.fillStyle = 'rgba(5,7,18,0.9)'; rr(-w / 2 + 16, -h / 2 - 24, lw, 54, 27); ctx.fill();
    ctx.strokeStyle = COL.g; ctx.lineWidth = 3; rr(-w / 2 + 16, -h / 2 - 24, lw, 54, 27); ctx.stroke();
    label(labelTxt, -w / 2 + 44, -h / 2 + 3, 34, '#fff', 'left', 900);
  }
  ctx.restore();
}

// ---- 背景（常時わずかに動く：§4）----
function ambientBG(t, tone) {
  const g = ctx.createLinearGradient(0, 0, 0, H);
  if (tone === 'law') { g.addColorStop(0, '#0B0A06'); g.addColorStop(1, '#1A1408'); }
  else if (tone === 'case') { g.addColorStop(0, '#07080F'); g.addColorStop(1, '#12141F'); }
  else if (tone === 'red') { g.addColorStop(0, '#140608'); g.addColorStop(1, '#2A0A0C'); }
  else { g.addColorStop(0, '#07080F'); g.addColorStop(1, '#0E1018'); }
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(-Math.PI / 7);
  const period = 300, off = (t * 46) % period;
  ctx.fillStyle = 'rgba(255,255,255,0.020)';
  for (let x = -1700 + off; x < 1700; x += period) ctx.fillRect(x, -1400, 130, 2800);
  ctx.restore();
  for (let i = 0; i < 14; i++) {
    const spd = 16 + rnd(i * 3) * 26;
    const px = rnd(i * 7) * W + Math.sin(t * (.35 + rnd(i) * .4) + i) * 26;
    const py = (H + 140 - ((t * spd + rnd(i * 13) * H) % (H + 280)));
    ctx.globalAlpha = .05 + rnd(i * 5) * .07; ctx.fillStyle = '#fff';
    ctx.beginPath(); ctx.arc(px, py, 2 + rnd(i * 11) * 3.5, 0, 7); ctx.fill();
  }
  ctx.globalAlpha = 1;
}
function vignette(strength) {
  const vg = ctx.createRadialGradient(W / 2, H / 2, 480, W / 2, H / 2, 1350);
  vg.addColorStop(0, 'rgba(0,0,0,0)');
  vg.addColorStop(1, `rgba(0,0,0,${strength !== undefined ? strength : .5})`);
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
}
function grain(t, amt) {
  const f = Math.floor(t * 30);
  ctx.globalAlpha = amt !== undefined ? amt : .045; ctx.fillStyle = '#fff';
  for (let i = 0; i < 100; i++) ctx.fillRect(rnd(i * 7 + f * 13) * W, rnd(i * 11 + f * 17) * H, 2.2, 2.2);
  ctx.globalAlpha = 1;
}

window.CORE = {
  W, H, clamp, lerp, rnd, fract,
  easeInQuad, easeOutQuad, easeInOut, easeOutCubic, easeOutQuint, easeOutBack, easeOutElastic,
  prog, popIn, fadeIn, outSc, win,
  COL, SANS, SERIF, bind, rr, goldGrad, chW, segText, label,
  addImpacts, IMPACTS, shakeOffset, shakeZoom, drawFlashes, drawBursts,
  setImages, hasImg, kb, photoBG, photoPanel, ambientBG, vignette, grain,
  get ctx() { return ctx; },
};
})();
