/* ===========================================================
   scenes.js — 動く参考イラスト(SVG)ライブラリ
   -----------------------------------------------------------
   各シーンは SCENES[key](big) で SVG 文字列を返す。
     big=false … ページ背景の ambient (常時アニメ・低不透明度・ラベルなし)
     big=true  … 「イメージ」ボタンで開く拡大表示 (ラベルつき)
   アニメーションは deck.css の .an-* クラスで付与する。

   図はすべて概念図であり、実際の現場の配置・寸法ではない。
   =========================================================== */
(function (global) {
  'use strict';

  var VB = '0 0 480 320';
  var C = { red:'#ff3b3b', amber:'#ffb020', cyan:'#4fd7ff', green:'#6ee7a8', violet:'#c39cff', dim:'#8f9baa' };

  /* 決定論的な擬似乱数 (毎回同じ絵になるように) */
  function rnd(seed) {
    var s = seed;
    return function () { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; };
  }

  function lbl(x, y, text, size, color) {
    if (size === undefined) size = 15;
    return '<text class="sv-lbl" x="' + x + '" y="' + y + '" font-size="' + size + '"' +
           (color ? ' fill="' + color + '"' : '') + '>' + text + '</text>';
  }
  /* big のときだけラベルを出す */
  function L(big) {
    return function (x, y, text, size, color) { return big ? lbl(x, y, text, size, color) : ''; };
  }

  /* 建物のシルエット (共通パーツ) */
  function mall(x, y, w, h, fill) {
    return '<g>' +
      '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="4" fill="' + (fill || '#1b2432') + '" stroke="#3a4658" stroke-width="2"/>' +
      '<rect x="' + (x + 6) + '" y="' + (y + 6) + '" width="' + (w - 12) + '" height="' + (h * 0.42) + '" fill="rgba(255,255,255,.05)"/>' +
      '<line x1="' + x + '" y1="' + (y + h * 0.55) + '" x2="' + (x + w) + '" y2="' + (y + h * 0.55) + '" stroke="#3a4658" stroke-width="1.5"/>' +
      '</g>';
  }
  function ground(y) {
    return '<line x1="10" y1="' + y + '" x2="470" y2="' + y + '" stroke="#3a4658" stroke-width="2"/>';
  }
  function wrap(inner) { return '<svg viewBox="' + VB + '" xmlns="http://www.w3.org/2000/svg">' + inner + '</svg>'; }

  var SCENES = {};

  /* 01 爆発 ------------------------------------------------------------ */
  SCENES.blast = function (big) {
    var t = L(big), r = rnd(7), s = '', i;
    for (i = 0; i < 4; i++) {
      s += '<circle cx="248" cy="150" r="34" fill="none" stroke="' + C.red + '" stroke-width="3" ' +
           'class="an-expand" style="--d:2.8s;--dl:' + (i * 0.7).toFixed(2) + 's"/>';
    }
    for (i = 0; i < 14; i++) {
      var a = r() * Math.PI * 2, d = 30 + r() * 26;
      s += '<rect x="' + (248 + Math.cos(a) * d).toFixed(1) + '" y="' + (150 + Math.sin(a) * d * 0.7).toFixed(1) + '" ' +
           'width="' + (4 + r() * 7).toFixed(1) + '" height="' + (3 + r() * 5).toFixed(1) + '" fill="' + C.amber + '" ' +
           'class="an-fall" style="--d:' + (2 + r() * 2).toFixed(2) + 's;--dl:' + (r() * 2.4).toFixed(2) + 's;--ty:' + (70 + r() * 70).toFixed(0) + 'px;--rot:' + (r() * 540).toFixed(0) + 'deg"/>';
    }
    return wrap(
      ground(258) + mall(60, 168, 360, 90) +
      '<circle cx="248" cy="150" r="26" fill="' + C.amber + '" class="an-pulse" style="--d:1.6s" opacity=".85"/>' +
      s +
      t(60, 292, '爆発起点・規模は未公表（概念図）', 14, C.dim)
    );
  };

  /* 02 ガス漏れ -------------------------------------------------------- */
  SCENES.gasleak = function (big) {
    var t = L(big), r = rnd(11), s = '', i;
    for (i = 0; i < 12; i++) {
      s += '<circle cx="' + (196 + r() * 74).toFixed(0) + '" cy="' + (196 + r() * 22).toFixed(0) + '" r="' + (4 + r() * 8).toFixed(1) + '" ' +
           'fill="' + C.amber + '" opacity=".55" class="an-rise" ' +
           'style="--d:' + (2.6 + r() * 2.4).toFixed(2) + 's;--dl:' + (r() * 3.2).toFixed(2) + 's;--ty:-' + (60 + r() * 80).toFixed(0) + 'px"/>';
    }
    return wrap(
      ground(258) +
      '<rect x="40" y="196" width="150" height="14" rx="7" fill="' + C.dim + '"/>' +
      '<rect x="182" y="150" width="14" height="60" rx="7" fill="' + C.dim + '"/>' +
      '<circle cx="192" cy="200" r="9" fill="' + C.red + '" class="an-blink" style="--d:1.2s"/>' + s +
      '<text x="300" y="120" font-size="70" font-weight="900" fill="' + C.amber + '" opacity=".30" class="an-pulse" style="--d:3.2s">?</text>' +
      t(40, 240, '漏出箇所＝未判明', 15, C.amber) +
      t(40, 292, 'ガス漏れは有力視。ただし公式な原因確定ではない', 14, C.dim)
    );
  };

  /* 03 地震 ------------------------------------------------------------ */
  SCENES.quake = function (big) {
    var t = L(big), s = '', i;
    for (i = 0; i < 5; i++) {
      s += '<ellipse cx="150" cy="212" rx="30" ry="14" fill="none" stroke="' + C.red + '" stroke-width="2.5" ' +
           'class="an-expand" style="--d:3.2s;--dl:' + (i * 0.64).toFixed(2) + 's"/>';
    }
    var w = 'M240 150';
    for (i = 0; i < 24; i++) {
      var amp = i > 5 && i < 15 ? 34 : 9;
      w += ' L' + (240 + i * 9.5).toFixed(0) + ' ' + (150 + (i % 2 ? -amp : amp) * (0.55 + (i % 3) * 0.22)).toFixed(0);
    }
    return wrap(
      ground(212) +
      '<g class="an-shake" style="--d:.42s">' + mall(58, 160, 150, 52) + '</g>' + s +
      '<circle cx="150" cy="212" r="7" fill="' + C.red + '"/>' +
      '<path d="' + w + '" stroke="' + C.cyan + '" stroke-width="2.5" ' +
      'stroke-dasharray="460" class="sv-stroke an-sweep" style="--len:460;--d:3.4s"/>' +
      t(240, 118, 'M7.1 / 最大震度7', 17, C.cyan) +
      t(240, 250, '横ずれ断層型・深さ約16km', 14, C.dim) +
      t(58, 292, '震源から地表へ、揺れが同心円状に伝わる（概念図）', 14, C.dim)
    );
  };

  /* 04 時間差 ---------------------------------------------------------- */
  SCENES.clock = function (big) {
    var t = L(big), r = rnd(23), s = '', i;
    for (i = 0; i < 10; i++) {
      s += '<circle cx="' + (300 + r() * 130).toFixed(0) + '" cy="' + (150 + r() * 80).toFixed(0) + '" r="' + (5 + r() * 9).toFixed(1) + '" ' +
           'fill="' + C.amber + '" opacity=".4" class="an-pulse" style="--d:' + (2 + r() * 2).toFixed(2) + 's;--dl:' + (r() * 2).toFixed(2) + 's"/>';
    }
    return wrap(
      '<circle cx="150" cy="160" r="82" fill="none" stroke="' + C.dim + '" stroke-width="3"/>' +
      '<circle cx="150" cy="160" r="6" fill="' + C.amber + '"/>' +
      '<line x1="150" y1="160" x2="150" y2="96" stroke="' + C.amber + '" stroke-width="5" stroke-linecap="round" ' +
      'class="an-spin" style="--d:4s;--ox:150px;--oy:160px"/>' +
      '<line x1="150" y1="160" x2="150" y2="112" stroke="#fff" stroke-width="3" stroke-linecap="round" ' +
      'class="an-spin" style="--d:24s;--ox:150px;--oy:160px"/>' +
      '<rect x="288" y="120" width="156" height="112" rx="6" fill="none" stroke="' + C.dim + '" stroke-width="2"/>' + s +
      '<rect x="290" y="200" width="152" height="30" fill="' + C.amber + '" opacity=".22" class="an-pulse" style="--d:3.6s"/>' +
      t(96, 268, '地震発生', 16, C.cyan) + t(300, 268, 'ガスが滞留', 16, C.amber) +
      t(150, 40, '約80〜90分', 22, C.amber) +
      t(96, 296, '時間差＝蓄積説と整合。ただし裏づけ鑑定は未了', 14, C.dim)
    );
  };

  /* 05 配管 ------------------------------------------------------------ */
  SCENES.pipes = function (big) {
    var t = L(big), i, s = '';
    var pts = [[110, 196], [222, 196], [222, 130], [340, 130]];
    for (i = 0; i < pts.length; i++) {
      s += '<circle cx="' + pts[i][0] + '" cy="' + pts[i][1] + '" r="11" fill="none" stroke="' + C.red + '" stroke-width="3" ' +
           'class="an-blink" style="--d:2.4s;--dl:' + (i * 0.6).toFixed(2) + 's"/>' +
           '<circle cx="' + pts[i][0] + '" cy="' + pts[i][1] + '" r="4" fill="' + C.red + '" ' +
           'class="an-blink" style="--d:2.4s;--dl:' + (i * 0.6).toFixed(2) + 's"/>';
    }
    return wrap(
      ground(258) +
      '<rect x="46" y="176" width="40" height="40" rx="5" fill="#1b2432" stroke="' + C.dim + '" stroke-width="2"/>' +
      '<path d="M86 196 H340 M222 196 V130 H400" class="sv-stroke" stroke="' + C.dim + '" stroke-width="12"/>' +
      '<path d="M86 196 H340 M222 196 V130 H400" class="sv-stroke an-dash" stroke="' + C.cyan + '" stroke-width="4" ' +
      'stroke-dasharray="14 22" style="--d:1.6s;--dof:-36"/>' + s +
      '<rect x="392" y="106" width="52" height="48" rx="5" fill="#1b2432" stroke="' + C.dim + '" stroke-width="2"/>' +
      t(40, 236, 'LPガス設備', 15) + t(330, 96, '厨房・飲食区画', 14) +
      t(40, 292, '赤＝漏出の候補地点。実際の配管経路・破断位置は未公表', 14, C.dim)
    );
  };

  /* 06 着火源 ---------------------------------------------------------- */
  SCENES.spark = function (big) {
    var t = L(big), r = rnd(31), s = '', i;
    for (i = 0; i < 14; i++) {
      s += '<circle cx="' + (70 + r() * 170).toFixed(0) + '" cy="' + (120 + r() * 110).toFixed(0) + '" r="' + (10 + r() * 22).toFixed(0) + '" ' +
           'fill="' + C.amber + '" opacity=".16" class="an-pulse" style="--d:' + (2.4 + r() * 2).toFixed(2) + 's;--dl:' + (r() * 2.4).toFixed(2) + 's"/>';
    }
    var srcs = [['配線', 330, 120], ['スイッチ', 330, 170], ['厨房機器', 330, 220], ['復電の火花', 330, 268]];
    for (i = 0; i < srcs.length; i++) {
      s += '<circle cx="' + srcs[i][1] + '" cy="' + (srcs[i][2] - 5) + '" r="9" fill="' + C.red + '" ' +
           'class="an-seq" style="--d:6s;--dl:' + (i * 1.5).toFixed(2) + 's"/>' +
           (big ? lbl(srcs[i][1] + 18, srcs[i][2], srcs[i][0], 15) : '');
    }
    return wrap(
      ground(288) + s +
      '<text x="150" y="185" font-size="54" fill="#fff" opacity=".9" class="an-blink" style="--d:1.4s" text-anchor="middle">⚡</text>' +
      t(60, 100, '可燃範囲まで蓄積？', 16, C.amber) +
      t(60, 312, 'いずれも候補であり、着火源は特定されていない', 14, C.dim)
    );
  };

  /* 07 感震遮断 (マイコンメーター) ------------------------------------- */
  SCENES.meter = function (big) {
    var t = L(big);
    return wrap(
      '<rect x="180" y="110" width="120" height="104" rx="10" fill="#1b2432" stroke="' + C.dim + '" stroke-width="2.5"/>' +
      '<circle cx="240" cy="146" r="17" fill="none" stroke="' + C.cyan + '" stroke-width="2.5"/>' +
      '<circle cx="240" cy="146" r="6" fill="' + C.cyan + '" class="an-shake" style="--d:.4s"/>' +
      '<rect x="204" y="176" width="72" height="20" rx="4" fill="#0b1017" stroke="' + C.dim + '"/>' +
      '<rect x="208" y="180" width="64" height="12" fill="' + C.red + '" opacity=".8" class="an-blink" style="--d:1.1s"/>' +
      '<path d="M40 162 H180" class="sv-stroke" stroke="' + C.dim + '" stroke-width="12"/>' +
      '<path d="M300 162 H440" class="sv-stroke" stroke="' + C.dim + '" stroke-width="12"/>' +
      '<path d="M40 162 H180" class="sv-stroke an-dash" stroke="' + C.amber + '" stroke-width="4" stroke-dasharray="12 18" style="--d:1.3s;--dof:-30"/>' +
      '<path d="M300 162 H440" class="sv-stroke an-dash" stroke="' + C.green + '" stroke-width="4" stroke-dasharray="12 18" style="--d:2.6s;--dof:-30" opacity=".35"/>' +
      '<line x1="300" y1="140" x2="300" y2="184" stroke="' + C.green + '" stroke-width="5" class="an-blink" style="--d:2.2s"/>' +
      t(40, 132, '上流＝供給側', 15, C.amber) + t(330, 132, '下流＝館内', 15, C.green) +
      t(196, 240, '感震遮断', 16, C.cyan) +
      t(40, 276, 'メーターが止められるのは下流のみ。', 14, C.dim) +
      t(40, 296, '上流側の配管破断はメーターでは止まらない（一般論）', 14, C.dim)
    );
  };

  /* 08 避難 ------------------------------------------------------------ */
  SCENES.people = function (big) {
    var t = L(big), r = rnd(41), s = '', i;
    for (i = 0; i < 9; i++) {
      s += '<circle cx="' + (120 + r() * 120).toFixed(0) + '" cy="' + (150 + r() * 70).toFixed(0) + '" r="6" fill="' + C.cyan + '" ' +
           'class="an-drift" style="--d:' + (4 + r() * 3).toFixed(2) + 's;--dl:' + (r() * 4).toFixed(2) + 's;--tx:' + (150 + r() * 60).toFixed(0) + 'px"/>';
    }
    for (i = 0; i < 3; i++) {
      s += '<circle cx="' + (150 + i * 34) + '" cy="' + (196 + (i % 2) * 22) + '" r="7" fill="' + C.amber + '" ' +
           'class="an-blink" style="--d:2s;--dl:' + (i * 0.5) + 's"/>';
    }
    return wrap(
      '<rect x="70" y="110" width="250" height="140" rx="8" fill="none" stroke="' + C.dim + '" stroke-width="2.5"/>' +
      '<rect x="316" y="160" width="8" height="42" fill="' + C.green + '"/>' + s +
      '<path d="M330 181 H420" class="sv-stroke" stroke="' + C.green + '" stroke-width="3" marker-end="url(#ar)"/>' +
      '<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">' +
      '<path d="M0 0 L9 4.5 L0 9 z" fill="' + C.green + '"/></marker></defs>' +
      t(354, 168, '避難', 15, C.green) +
      t(80, 100, '館内', 15) + t(120, 282, '橙＝爆発時に残っていた人', 14, C.amber) +
      t(120, 302, '個別の行動理由は正式確認前', 14, C.dim)
    );
  };

  /* 09 救助 ------------------------------------------------------------ */
  SCENES.rescue = function (big) {
    var t = L(big), r = rnd(53), s = '', i;
    for (i = 0; i < 16; i++) {
      s += '<rect x="' + (70 + r() * 300).toFixed(0) + '" y="' + (196 + r() * 46).toFixed(0) + '" width="' + (10 + r() * 24).toFixed(0) + '" ' +
           'height="' + (7 + r() * 13).toFixed(0) + '" fill="#2a3546" stroke="#3f4c60" transform="rotate(' + (r() * 40 - 20).toFixed(0) + ' 200 220)"/>';
    }
    for (i = 0; i < 3; i++) {
      s += '<ellipse cx="240" cy="252" rx="60" ry="16" fill="none" stroke="' + C.red + '" stroke-width="2" ' +
           'class="an-expand" style="--d:3.6s;--dl:' + (i * 1.2) + 's"/>';
    }
    return wrap(
      ground(252) + s +
      '<circle cx="146" cy="176" r="11" fill="' + C.green + '"/><rect x="140" y="188" width="12" height="30" rx="4" fill="' + C.green + '"/>' +
      '<circle cx="300" cy="176" r="11" fill="' + C.green + '"/><rect x="294" y="188" width="12" height="30" rx="4" fill="' + C.green + '"/>' +
      '<g class="an-blink" style="--d:1.5s">' +
      '<text x="370" y="130" font-size="30">⚠</text><text x="404" y="130" font-size="30">🔥</text></g>' +
      t(60, 110, '余震・ガス・火災・崩落が同時進行', 16, C.amber) +
      t(60, 296, '救助側は複数の危険に同時対応する（概念図）', 14, C.dim)
    );
  };

  /* 10 崩落原因 -------------------------------------------------------- */
  SCENES.collapse = function (big) {
    var t = L(big), r = rnd(61), s = '', i;
    for (i = 0; i < 10; i++) {
      s += '<rect x="' + (270 + r() * 150).toFixed(0) + '" y="' + (110 + r() * 40).toFixed(0) + '" width="' + (8 + r() * 14).toFixed(0) + '" ' +
           'height="' + (6 + r() * 10).toFixed(0) + '" fill="' + C.red + '" opacity=".8" class="an-fall" ' +
           'style="--d:' + (2 + r() * 1.6).toFixed(2) + 's;--dl:' + (r() * 2).toFixed(2) + 's;--ty:110px;--rot:' + (r() * 360).toFixed(0) + 'deg"/>';
    }
    return wrap(
      ground(258) +
      '<g class="an-shake" style="--d:.44s">' + mall(40, 168, 190, 90) + '</g>' +
      '<path d="M60 140 H210" class="sv-stroke" stroke="' + C.cyan + '" stroke-width="4" marker-end="url(#ar2)"/>' +
      '<defs><marker id="ar2" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">' +
      '<path d="M0 0 L9 4.5 L0 9 z" fill="' + C.cyan + '"/></marker></defs>' +
      mall(268, 168, 172, 90) +
      '<circle cx="330" cy="196" r="30" fill="' + C.red + '" opacity=".3" class="an-expand" style="--d:2.6s"/>' + s +
      t(46, 128, '① 地震の揺れ（水平力）', 15, C.cyan) +
      t(268, 128, '② 爆発の内圧', 15, C.red) +
      t(40, 292, 'どちらがどこまで壊したかは、破断面・焼損の鑑定で切り分ける', 14, C.dim)
    );
  };

  /* 11 施設の履歴 ------------------------------------------------------ */
  SCENES.history = function (big) {
    var t = L(big), i, s = '', ys = ['2016', '復旧・改修', '2026'];
    for (i = 0; i < 3; i++) {
      var x = 90 + i * 150;
      s += '<circle cx="' + x + '" cy="180" r="15" fill="none" stroke="' + (i === 2 ? C.red : C.cyan) + '" stroke-width="3" ' +
           'class="an-pulse" style="--d:2.8s;--dl:' + (i * 0.8) + 's"/>' +
           '<circle cx="' + x + '" cy="180" r="6" fill="' + (i === 2 ? C.red : C.cyan) + '"/>' +
           (big ? lbl(x - 34, 224, ys[i], 15, i === 2 ? C.red : C.cyan) : '');
    }
    return wrap(
      '<line x1="90" y1="180" x2="390" y2="180" stroke="' + C.dim + '" stroke-width="3"/>' +
      '<line x1="90" y1="180" x2="390" y2="180" stroke="' + C.amber + '" stroke-width="3" stroke-dasharray="300" ' +
      'class="an-sweep" style="--len:300;--d:5s"/>' + s +
      mall(60, 96, 60, 46) + mall(210, 96, 60, 46) + '<g class="an-shake" style="--d:.5s">' + mall(360, 96, 60, 46) + '</g>' +
      t(60, 274, '2016年にも被災し、復旧・改修を経て営業してきた', 14, C.dim) +
      t(60, 296, '損傷箇所が旧部分・補強部分のどこかは重要な検証点', 14, C.dim)
    );
  };

  /* 12 耐震補強 vs 爆圧 ------------------------------------------------ */
  SCENES.retrofit = function (big) {
    var t = L(big), i, s = '';
    for (i = 0; i < 5; i++) {
      s += '<circle cx="330" cy="180" r="20" fill="none" stroke="' + C.red + '" stroke-width="2.5" ' +
           'class="an-expand" style="--d:2.6s;--dl:' + (i * 0.5).toFixed(2) + 's"/>';
    }
    return wrap(
      '<rect x="60" y="120" width="120" height="120" fill="none" stroke="' + C.dim + '" stroke-width="3"/>' +
      '<path d="M60 120 L180 240 M180 120 L60 240" class="sv-stroke" stroke="' + C.green + '" stroke-width="4"/>' +
      '<path d="M28 132 H56" class="sv-stroke an-scan" stroke="' + C.cyan + '" stroke-width="5" style="--d:1.4s;--x0:-8px;--x1:8px;--r0:0;--r1:0"/>' +
      '<path d="M28 172 H56" class="sv-stroke an-scan" stroke="' + C.cyan + '" stroke-width="5" style="--d:1.4s;--dl:.2s;--x0:-8px;--x1:8px;--r0:0;--r1:0"/>' +
      '<rect x="270" y="120" width="120" height="120" fill="none" stroke="' + C.dim + '" stroke-width="3"/>' + s +
      t(56, 100, '耐震設計＝水平力を想定', 15, C.green) +
      t(266, 100, '爆発＝内側からの面圧', 15, C.red) +
      t(40, 274, '「耐震化されていた」ことと', 13, C.dim) +
      t(40, 294, '「爆圧に耐える」ことは別物（一般論）', 13, C.dim)
    );
  };

  /* 13 警報・防火区画 -------------------------------------------------- */
  SCENES.alarm = function (big) {
    var t = L(big), i, s = '';
    var steps = [['感知器', 74], ['館内放送', 174], ['防火扉', 274], ['排煙', 374]];
    for (i = 0; i < steps.length; i++) {
      var x = steps[i][1];
      s += '<rect x="' + (x - 34) + '" y="146" width="68" height="60" rx="10" fill="#1b2432" ' +
           'stroke="' + C.cyan + '" stroke-width="2.5" class="an-seq" ' +
           'style="--d:6.4s;--dl:' + (i * 1.3).toFixed(2) + 's"/>' +
           (big ? lbl(x - 32, 228, steps[i][0], 14, C.cyan) : '');
      if (i < steps.length - 1) {
        s += '<line x1="' + (x + 36) + '" y1="176" x2="' + (x + 62) + '" y2="176" ' +
             'stroke="' + C.dim + '" stroke-width="3" class="an-seq" ' +
             'style="--d:6.4s;--dl:' + (i * 1.3 + 0.65).toFixed(2) + 's"/>';
      }
    }
    /* 連鎖のどこか一段が働かないと、その先が止まる */
    s += '<text x="274" y="126" font-size="24" fill="' + C.amber + '" text-anchor="middle" ' +
         'class="an-blink" style="--d:2.2s">?</text>';
    return wrap(s +
      t(60, 112, '設備は「単体」ではなく「連鎖」で効く', 16, C.cyan) +
      t(40, 266, '感知 → 放送 → 区画 → 排煙。', 13, C.dim) +
      t(40, 286, 'どこか一段が働かないと、その先が止まる', 13, C.dim) +
      t(40, 306, '現段階で設備の不作動を示す公式発表はない', 13, C.dim)
    );
  };

  /* 14 におい ---------------------------------------------------------- */
  SCENES.smell = function (big) {
    var t = L(big), r = rnd(83), s = '', i;
    for (i = 0; i < 14; i++) {
      s += '<circle cx="' + (110 + r() * 40).toFixed(0) + '" cy="' + (140 + r() * 90).toFixed(0) + '" r="' + (3 + r() * 6).toFixed(1) + '" ' +
           'fill="' + C.violet + '" opacity=".65" class="an-drift" ' +
           'style="--d:' + (5 + r() * 4).toFixed(2) + 's;--dl:' + (r() * 5).toFixed(2) + 's;--tx:' + (200 + r() * 90).toFixed(0) + 'px"/>';
    }
    return wrap(
      '<circle cx="104" cy="186" r="14" fill="none" stroke="' + C.violet + '" stroke-width="3" class="an-pulse" style="--d:2.2s"/>' +
      '<text x="98" y="192" font-size="18" fill="' + C.violet + '" font-weight="900">?</text>' + s +
      '<path d="M120 108 Q240 92 380 108" stroke="' + C.cyan + '" stroke-width="2.5" stroke-dasharray="8 10" ' +
      'class="sv-stroke an-dash" style="--d:2s;--dof:-36"/>' +
      t(140, 96, '風向き', 14, C.cyan) +
      t(60, 246, '起点？', 15, C.violet) +
      t(40, 278, 'ガスは本来無臭。付臭剤で気づけるようにしている', 13, C.dim) +
      t(40, 300, '風向き・場所・時刻が揃わないと起点は特定できない', 13, C.dim)
    );
  };

  /* 15 爆圧 ------------------------------------------------------------ */
  SCENES.pressure = function (big) {
    var t = L(big), i, s = '';
    for (i = 0; i < 5; i++) {
      s += '<rect x="' + (150 - i * 14) + '" y="' + (150 - i * 10) + '" width="' + (120 + i * 28) + '" height="' + (90 + i * 20) + '" ' +
           'rx="6" fill="none" stroke="' + C.red + '" stroke-width="2" opacity=".6" ' +
           'class="an-expand" style="--d:2.8s;--dl:' + (i * 0.55).toFixed(2) + 's"/>';
    }
    return wrap(
      '<rect x="110" y="120" width="200" height="140" rx="6" fill="none" stroke="' + C.dim + '" stroke-width="4"/>' + s +
      '<rect x="306" y="124" width="8" height="132" fill="' + C.amber + '" class="an-scan" style="--d:1.1s;--x0:0;--x1:56px;--r0:0deg;--r1:14deg"/>' +
      '<circle cx="210" cy="190" r="26" fill="' + C.red + '" opacity=".35" class="an-pulse" style="--d:1.8s"/>' +
      t(112, 108, '閉鎖空間で内圧が急上昇', 15, C.red) +
      t(322, 108, '弱い外壁へ', 14, C.amber) +
      t(322, 128, '圧力が抜ける', 14, C.amber) +
      t(40, 280, '一般の外壁は数kPaで壊れる。', 13, C.dim) +
      t(40, 300, '地震で弱っていれば破壊が拡大しやすい', 13, C.dim)
    );
  };

  /* 16 爆発音 ---------------------------------------------------------- */
  SCENES.sound = function (big) {
    var t = L(big), i, r = rnd(97), d = 'M40 180';
    for (i = 1; i <= 84; i++) {
      var x = 40 + i * 5;
      var peak = (i > 14 && i < 20) || (i > 38 && i < 43) || (i > 60 && i < 64);
      var amp = peak ? 60 : 8;
      d += ' L' + x + ' ' + (180 + (i % 2 ? -1 : 1) * amp * (0.4 + r() * 0.6)).toFixed(0);
    }
    return wrap(
      '<line x1="40" y1="180" x2="460" y2="180" stroke="#2a3546" stroke-width="1.5"/>' +
      '<path d="' + d + '" class="sv-stroke an-sweep" stroke="' + C.cyan + '" stroke-width="2.5" ' +
      'stroke-dasharray="1400" style="--len:1400;--d:4.2s"/>' +
      '<circle cx="122" cy="180" r="13" fill="none" stroke="' + C.red + '" stroke-width="2.5" class="an-expand" style="--d:2.6s"/>' +
      '<circle cx="242" cy="180" r="13" fill="none" stroke="' + C.amber + '" stroke-width="2.5" class="an-expand" style="--d:2.6s;--dl:.85s"/>' +
      '<circle cx="352" cy="180" r="13" fill="none" stroke="' + C.amber + '" stroke-width="2.5" class="an-expand" style="--d:2.6s;--dl:1.7s"/>' +
      t(96, 104, '主爆発？', 14, C.red) + t(212, 104, '崩落音？', 14, C.amber) + t(324, 104, '設備の破損音？', 14, C.amber) +
      t(40, 282, '「爆発音」がすべて化学的な爆発とは限らない', 14, C.dim)
    );
  };

  /* 17 監視カメラ・ログ ------------------------------------------------ */
  SCENES.cctv = function (big) {
    var t = L(big), i, s = '';
    for (i = 0; i < 7; i++) {
      s += '<rect x="272" y="' + (118 + i * 20) + '" width="' + (60 + (i % 4) * 32) + '" height="8" rx="4" ' +
           'fill="' + C.green + '" opacity=".7" class="an-seq" style="--d:5.6s;--dl:' + (i * 0.42).toFixed(2) + 's"/>';
    }
    return wrap(
      '<rect x="70" y="112" width="44" height="26" rx="6" fill="#1b2432" stroke="' + C.dim + '" stroke-width="2"/>' +
      '<rect x="112" y="120" width="14" height="10" fill="' + C.dim + '"/>' +
      '<g class="an-scan" style="--d:4.6s;--x0:0;--x1:0;--r0:-24deg;--r1:24deg;transform-origin:92px 138px">' +
      '<path d="M92 138 L34 246 L150 246 Z" fill="' + C.cyan + '" opacity=".18"/>' +
      '<path d="M92 138 L34 246 M92 138 L150 246" class="sv-stroke" stroke="' + C.cyan + '" stroke-width="1.5" opacity=".5"/></g>' +
      '<circle cx="80" cy="125" r="4" fill="' + C.red + '" class="an-blink" style="--d:1.4s"/>' +
      '<rect x="262" y="104" width="180" height="152" rx="8" fill="#0b1017" stroke="' + C.dim + '" stroke-width="2"/>' + s +
      '<rect x="262" y="238" width="180" height="18" fill="' + C.red + '" opacity=".22" class="an-blink" style="--d:2.4s"/>' +
      t(262, 92, '設備ログ', 15, C.green) + t(268, 252, '電源喪失で記録停止？', 13, C.red) +
      t(40, 290, 'レコーダーは通常上書き式。停電・損傷で欠落する可能性がある', 14, C.dim)
    );
  };

  /* 18 連鎖 ------------------------------------------------------------ */
  SCENES.chain = function (big) {
    var t = L(big), names = ['地震', '損傷', '避難', '滞留', '着火', '崩落'], i, s = '';
    for (i = 0; i < 6; i++) {
      var x = 52 + i * 70;
      s += '<circle cx="' + x + '" cy="170" r="24" fill="none" stroke="' + (i === 5 ? C.red : C.amber) + '" stroke-width="3" ' +
           'class="an-seq" style="--d:6s;--dl:' + (i * 0.9).toFixed(2) + 's"/>' +
           (big ? lbl(x - 16, 176, names[i], 14, i === 5 ? C.red : C.amber) : '');
      if (i < 5) {
        s += '<line x1="' + (x + 26) + '" y1="170" x2="' + (x + 44) + '" y2="170" stroke="' + C.dim + '" stroke-width="3" ' +
             'class="an-seq" style="--d:6s;--dl:' + (i * 0.9 + 0.45).toFixed(2) + 's"/>';
      }
    }
    return wrap(s +
      t(52, 122, '複合災害：ひとつの事故ではなく、連鎖', 16, C.amber) +
      t(52, 246, '地震 → 配管損傷 → 避難 → ガス蓄積 → 着火 → 崩落', 14, C.dim)
    );
  };

  /* 19 確度の層 -------------------------------------------------------- */
  SCENES.layers = function (big) {
    var t = L(big), rows = [['確定に近い', C.green, 300], ['有力', C.amber, 210], ['未判明', C.red, 130]], i, s = '';
    for (i = 0; i < rows.length; i++) {
      var y = 122 + i * 52;
      s += '<rect x="60" y="' + y + '" width="340" height="34" rx="8" fill="rgba(255,255,255,.06)"/>' +
           '<rect x="60" y="' + y + '" width="' + rows[i][2] + '" height="34" rx="8" fill="' + rows[i][1] + '" opacity=".55" ' +
           'class="an-pulse" style="--d:3.4s;--dl:' + (i * 0.7).toFixed(2) + 's"/>' +
           (big ? lbl(66, y + 24, rows[i][0], 16, '#0b1017') : '');
    }
    return wrap(s +
      t(60, 106, '確定・有力・未判明を混ぜない', 16, C.cyan) +
      t(60, 300, '同じ画面で扱っても、確度のラベルは分けて示す', 14, C.dim)
    );
  };

  /* 20 断てなかった連鎖 ------------------------------------------------ */
  SCENES.chainbreak = function (big) {
    var t = L(big), i, s = '';
    for (i = 0; i < 5; i++) {
      var x = 70 + i * 76;
      var isBreak = i === 2;
      s += '<circle cx="' + x + '" cy="176" r="26" fill="none" stroke="' + (isBreak ? C.green : C.red) + '" stroke-width="3.5" ' +
           (isBreak ? 'stroke-dasharray="8 8" class="an-blink" style="--d:1.6s"' : 'class="an-pulse" style="--d:3s;--dl:' + (i * 0.4).toFixed(2) + 's"') + '/>';
      if (i < 4) s += '<line x1="' + (x + 28) + '" y1="176" x2="' + (x + 48) + '" y2="176" stroke="' + C.dim + '" stroke-width="3"/>';
    }
    return wrap(s +
      '<text x="222" y="128" font-size="26" fill="' + C.green + '" text-anchor="middle" class="an-pulse" style="--d:2s">✂</text>' +
      t(60, 96, 'どこかで連鎖を断てなかったか', 16, C.green) +
      t(60, 252, '地震そのものは止められない。断てるのは連鎖の途中（概念図）', 14, C.dim)
    );
  };

  global.SCENES = SCENES;
  global.SCENE_KEYS = Object.keys(SCENES);
})(window);
