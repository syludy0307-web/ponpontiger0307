// broll：実写素材のカット割り（高速モンタージュ／全画面／パネル）
(function () {
'use strict';
const C = window.CORE, W = C.W, H = C.H;

// 高速モンタージュ。cuts:[{t,dur,key,fx,fy,z0,z1,label,credit}]
// 現在時刻に該当するカットだけを全画面で描く（ハードカット）
function montage(t, cuts) {
  for (const c of cuts) {
    if (t < c.t || t >= c.t + c.dur) continue;
    C.photoBG(c.key, t, {
      fx: c.fx !== undefined ? c.fx : .5, fy: c.fy !== undefined ? c.fy : .5,
      z0: c.z0 !== undefined ? c.z0 : 1.10, z1: c.z1 !== undefined ? c.z1 : 1.26,
      t0: c.t, t1: c.t + c.dur,
    }, c.tintTop || 'rgba(6,8,18,0.44)', c.tintBot || 'rgba(6,8,18,0.80)');
    // カット内で必ず動く（§4）：わずかな横流れ
    if (c.label) {
      const p = C.clamp((t - c.t) / .18, 0, 1);
      C.ctx.save(); C.ctx.globalAlpha = p;
      C.label(c.label, W / 2, 1180, 40, 'rgba(255,255,255,0.9)', 'center', 900);
      C.ctx.restore();
    }
    if (c.credit) C.label(c.credit, W - 24, 32, 20, 'rgba(255,255,255,0.42)', 'right', 500);
    return c;
  }
  return null;
}

// フィリピン国旗を旗らしく（写真がある場合は写真、なければベクター）
function flag(t, t0, dur) {
  if (C.hasImg('flag')) {
    C.photoBG('flag', t, { fx: .5, fy: .3, z0: 1.08, z1: 1.24, t0, t1: t0 + dur },
      'rgba(6,8,18,0.34)', 'rgba(6,8,18,0.74)');
    C.label('Photo: Roel Balingit / CC BY-SA 4.0', W - 24, 32, 20, 'rgba(255,255,255,0.42)', 'right', 500);
    return;
  }
  const ctx = C.ctx;
  ctx.fillStyle = C.COL.phBlue; ctx.fillRect(0, 700, W, 260);
  ctx.fillStyle = C.COL.phRed; ctx.fillRect(0, 960, W, 260);
}

// 全画面の裁判所（ラベル付き）
function courthouse(t, o) {
  C.photoBG('court2', t, {
    fx: .5, fy: o.fy !== undefined ? o.fy : .16,
    z0: o.z0 !== undefined ? o.z0 : 1.10, z1: o.z1 !== undefined ? o.z1 : 1.30,
    t0: o.t0, t1: o.t1,
  }, o.tintTop || 'rgba(6,8,18,0.52)', o.tintBot || 'rgba(6,8,18,0.86)');
  C.label('Photo: Patrickroque01 / CC BY-SA 4.0', W - 24, 32, 20, 'rgba(255,255,255,0.42)', 'right', 500);
}

// 法廷（ベクター：木製ベンチ＋判事席）※実在の法廷写真に人物が写るものは使わない
function courtroom(t, dim) {
  const ctx = C.ctx;
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, '#14100A'); g.addColorStop(1, '#070609');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // 背面の木パネル
  ctx.fillStyle = '#2A1D10';
  for (let x = -40; x < W + 60; x += 96) {
    ctx.globalAlpha = .55 + .18 * C.rnd(x); ctx.fillRect(x, 260, 84, 760);
  }
  ctx.globalAlpha = 1;
  // 判事席
  ctx.fillStyle = '#3A2716'; C.rr(150, 900, 780, 300, 12); ctx.fill();
  ctx.fillStyle = '#4A3320'; C.rr(150, 900, 780, 44, 12); ctx.fill();
  ctx.fillStyle = '#241809'; C.rr(300, 970, 480, 180, 8); ctx.fill();
  // 上からの光
  const lg = ctx.createRadialGradient(W / 2, 620, 40, W / 2, 620, 780);
  lg.addColorStop(0, 'rgba(255,226,170,0.16)'); lg.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
  if (dim) { ctx.fillStyle = `rgba(3,4,10,${dim})`; ctx.fillRect(0, 0, W, H); }
}

window.BROLL = { montage, flag, courthouse, courtroom };
})();
