// facecam：顔出し区間のレイヤー
//
// ★差し替え方法（顔出し素材が用意できたとき）
//   1. assets/facecam.mp4 を用意し、ffmpegでフレーム連番に展開
//        ffmpeg -i assets/facecam.mp4 -vf scale=1080:-2 -r 30 assets/face/%04d.jpg
//   2. photos.js と同様に読み込ませ、FACECAM.hasFootage = true にする
//   3. drawFootage() の中で該当フレームを drawImage するだけ。
//      呼び出し側（render.html の各シーン）は一切変更しなくてよい。
//
// 現状は hasFootage=false のため、指示書§5の許可どおり
// 「暗めのフィリピン街並み／裁判所／シルエット」による仮placeholder構成で描画する。
// AI生成の偽人物は使わない（シルエットのみ）。
(function () {
'use strict';
const C = window.CORE, W = C.W, H = C.H;

const FACECAM = {
  hasFootage: false,
  showGuide: false,          // trueにするとプレースホルダ枠を可視化（確認用）
  // 区間ごとの下地写真
  plate: { hook: 'street', deny: 'skyline', intent: 'street', punch: 'street' },
};

// 差し替え時にここだけ実装する
function drawFootage(/* t, o */) { return false; }

// 前景マス（ボケた手前の被写体）。人物の頭部は描かない＝黒い塊にしない。
// 画面下端から立ち上がる緩やかな暗部で、実写素材に「奥行き」を作るためのもの。
function foreground(t, s) {
  const ctx = C.ctx;
  const y0 = H - 300 * s;
  const g = ctx.createLinearGradient(0, y0 - 160 * s, 0, H);
  g.addColorStop(0, 'rgba(2,3,8,0)');
  g.addColorStop(.45, 'rgba(2,3,8,0.62)');
  g.addColorStop(1, 'rgba(2,3,8,0.94)');
  ctx.save();
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.moveTo(-60, H + 40);
  ctx.bezierCurveTo(-40, y0 + 40 * Math.sin(t * .5), 260, y0 - 90, 540, y0 - 60);
  ctx.bezierCurveTo(820, y0 - 30, 1080, y0 + 70, W + 60, H + 40);
  ctx.closePath(); ctx.fill();
  // ごく淡いリムライト（輪郭を示唆するだけ）
  ctx.strokeStyle = 'rgba(150,180,255,0.10)'; ctx.lineWidth = 5;
  ctx.beginPath();
  ctx.moveTo(-60, H + 40);
  ctx.bezierCurveTo(-40, y0 + 40 * Math.sin(t * .5), 260, y0 - 90, 540, y0 - 60);
  ctx.bezierCurveTo(820, y0 - 30, 1080, y0 + 70, W + 60, H + 40);
  ctx.stroke();
  ctx.restore();
}

// メイン描画
// o: {section, t, zoom(1〜), shot:'closeup'|'mid', dark:0..1, key}
function draw(t, o) {
  const ctx = C.ctx;
  o = o || {};
  if (FACECAM.hasFootage && drawFootage(t, o)) return;

  const key = o.key || FACECAM.plate[o.section] || 'street';
  const shot = o.shot || 'mid';
  const z = (o.zoom || 1) * (shot === 'closeup' ? 1.28 : 1.0);

  ctx.save();
  ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2);
  // 下地：暗いフィリピン街並み（ゆっくり寄る）
  if (!C.photoBG(key, t, {
    fx: o.fx !== undefined ? o.fx : .5, fy: o.fy !== undefined ? o.fy : .52,
    z0: 1.06, z1: 1.30, t0: o.t0 || 0, t1: (o.t0 || 0) + 12,
  }, 'rgba(5,7,16,0.72)', 'rgba(5,7,16,0.93)')) {
    ctx.fillStyle = '#06080F'; ctx.fillRect(0, 0, W, H);
  }
  // 被写界深度っぽいボケ玉
  for (let i = 0; i < 7; i++) {
    ctx.globalAlpha = .05 + .04 * Math.sin(t * 1.4 + i);
    ctx.fillStyle = ['#FF7A5C', '#6FD2FF', '#FFCF3F'][i % 3];
    ctx.beginPath();
    ctx.arc(rndX(i) * W, 300 + C.rnd(i * 13) * 700, 26 + C.rnd(i * 3) * 40, 0, 7);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
  foreground(t, shot === 'closeup' ? 1.35 : 1.0);
  ctx.restore();

  // 暗さ（区間の緊張感に合わせる）
  if (o.dark) { ctx.fillStyle = `rgba(3,4,10,${o.dark})`; ctx.fillRect(0, 0, W, H); }
  C.vignette(.58);

  if (FACECAM.showGuide) {
    ctx.save(); ctx.strokeStyle = 'rgba(255,80,80,0.9)'; ctx.lineWidth = 4; ctx.setLineDash([18, 14]);
    ctx.strokeRect(40, 40, W - 80, H - 80); ctx.setLineDash([]);
    C.label('FACE_CAM_PLACEHOLDER', W / 2, 110, 34, 'rgba(255,120,120,0.9)', 'center', 900);
    ctx.restore();
  }
}
function rndX(i) { return C.rnd(i * 7 + 2); }

FACECAM.draw = draw;
FACECAM.foreground = foreground;
window.FACECAM = FACECAM;
})();
