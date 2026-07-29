/* ===========================================================
   deck.js — スライドの組み立て / 操作 / 効果音
   -----------------------------------------------------------
   全ページ共通で必ず付くもの（データ側で書き忘れても付く）
     - 右下のワイプスペース（#wipe / fixed）
     - 常時アニメーションする参考イラスト（.ambient + .seismo）
     - 「イメージ」ボタン（#imgBtn / fixed）
     - 出典表記のフッター

   効果音
     ページ送り      → assets/se/se-page.mp3
     イメージボタン  → assets/se/se-image.mp3
   =========================================================== */
(function () {
  'use strict';

  var SLIDES = window.SLIDES, SCENES = window.SCENES;
  var deck = document.getElementById('deck');
  var wipe = document.getElementById('wipe');
  var imgBtn = document.getElementById('imgBtn');
  var modal = document.getElementById('imgModal');
  var progress = document.getElementById('progress');
  var controls = document.getElementById('controls');
  var audioNotice = document.getElementById('audioNotice');

  var idx = 0;
  var slideEls = [];

  /* ========================= 効果音 ========================= */
  var SE = (function () {
    var muted = false, unlocked = false, vol = 0.75;
    function make(src) { var a = new Audio(src); a.preload = 'auto'; a.volume = vol; return a; }
    var bank = { page: make('assets/se/se-page.mp3'), image: make('assets/se/se-image.mp3') };

    function play(name) {
      if (muted) return;
      var base = bank[name];
      if (!base) return;
      /* 連打しても重なるようにクローンを鳴らす */
      var a = base.cloneNode();
      a.volume = vol;
      var p = a.play();
      if (p && p.catch) {
        p.then(function () { markUnlocked(); })
         .catch(function () { /* 自動再生制限。最初のクリックで解除される */ });
      } else {
        markUnlocked();
      }
    }
    function markUnlocked() {
      if (unlocked) return;
      unlocked = true;
      if (audioNotice) audioNotice.classList.add('hide');
    }
    return {
      play: play,
      toggleMute: function () { muted = !muted; return muted; },
      isMuted: function () { return muted; },
      setVolume: function (v) {
        vol = Math.max(0, Math.min(1, v));
        for (var k in bank) { if (bank.hasOwnProperty(k)) bank[k].volume = vol; }
        return vol;
      },
      getVolume: function () { return vol; }
    };
  })();

  /* ========================= ブロック描画 ========================= */
  function tagsHtml(tags) {
    if (!tags || !tags.length) return '';
    return tags.map(function (t) {
      return '<span class="tag ' + t[0] + '">' + t[1] + '</span>';
    }).join('');
  }

  function listHtml(items, cls) {
    return '<ul class="' + (cls || '') + '">' +
      items.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ul>';
  }

  function photoHtml(p) {
    return '<figure class="photo-card">' +
      '<span class="badge ' + p.kind + '">' + p.badge + '</span>' +
      '<img src="' + p.src + '" alt="' + p.title.replace(/"/g, '') + '" loading="lazy">' +
      '<figcaption class="label"><b>' + p.title + '</b>' +
      '<span class="credit">' + p.credit + '</span></figcaption></figure>';
  }

  function slotHtml(b) {
    return '<div class="photo-slot">' +
      '<span class="badge slot" style="position:static">差し替えスロット</span>' +
      '<b>' + b.what + '</b>' +
      '<span>画像を <code>' + b.file + '</code> に置くと、ここに表示されます。<br>' +
      '権利処理を済ませたものだけを入れてください。</span></div>';
  }

  function block(b) {
    if (!b) return '';
    switch (b.t) {
      case 'panel':
        return '<div class="panel">' + tagsHtml(b.tags) +
               (b.items ? listHtml(b.items, b.cls) : '') +
               (b.html || '') + '</div>';
      case 'list':    return listHtml(b.items, b.cls);
      case 'quote':   return '<div class="quote">' + b.html + '</div>';
      case 'warning': return '<div class="warning">' + b.html + '</div>';
      case 'note':    return '<div class="note">' + b.html + '</div>';
      case 'photo':   return photoHtml(b.p);
      case 'slot':    return slotHtml(b);
      case 'html':    return b.html;
      case 'facts':
        return '<div class="facts">' + b.items.map(function (f) {
          return '<div class="fact"><b>' + f.v + '</b><span>' + f.l + '</span></div>';
        }).join('') + '</div>';
      case 'timeline':
        return '<div class="timeline">' + b.items.map(function (x) {
          return '<div class="time"><b>' + x.b + '</b><span>' + x.s + '</span></div>';
        }).join('') + '</div>';
      default:
        return '';
    }
  }
  function blocks(list) { return (list || []).map(block).join(''); }

  /* ========================= 常時アニメ層 ========================= */
  /* 全ページに必ず敷く。データに ambient が無ければシーンを順番に割り当てる */
  function ambientHtml(key, i) {
    var keys = window.SCENE_KEYS || [];
    var k = (key && SCENES[key]) ? key : keys[i % keys.length];
    return '<div class="ambient" aria-hidden="true">' +
      '<div class="seismo">' + seismoSvg() + '</div>' +
      '<div class="amb-art">' + SCENES[k](false) + '</div>' +
      '</div>';
  }

  /* 全ページ共通の、止まらない地震計ストリップ */
  function seismoSvg() {
    var d = 'M0 40', i, s = 1;
    for (i = 1; i <= 240; i++) {
      s = (s * 1103515245 + 12345) & 0x7fffffff;
      var r = s / 0x7fffffff;
      var burst = (i % 60 > 24 && i % 60 < 34);
      var amp = burst ? 30 : 7;
      d += ' L' + (i * 8) + ' ' + (40 + (i % 2 ? -1 : 1) * amp * (0.35 + r * 0.65)).toFixed(1);
    }
    /* 同じ波形を2本つなげて、-50% スクロールで継ぎ目なくループさせる */
    return '<svg viewBox="0 0 1920 80" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">' +
      '<path class="line" d="' + d + '"/>' +
      '<path class="line" d="' + d + '" transform="translate(1920,0)"/></svg>';
  }

  /* ========================= スライド組み立て ========================= */
  function buildSlide(s, i) {
    var el = document.createElement('section');
    el.className = 'slide';
    el.dataset.index = String(i);

    var stageCls = 'stage ' + (s.layout === 'split' ? 'split' : 'full') +
                   (s.guardBottom ? ' guard-bottom' : '') +
                   (s.guardRight ? ' guard-right' : '');

    var stageInner = (s.layout === 'split')
      ? '<div>' + blocks(s.left) + '</div><div>' + blocks(s.right) + '</div>'
      : blocks(s.body);

    el.innerHTML =
      (s.bg ? '<div class="bg" style="background-image:url(\'' + s.bg + '\')"></div>' : '') +
      ambientHtml(s.ambient, i) +
      '<div class="brand"><div class="name">YOUTUBE VISUAL BRIEF</div>' +
      '<div class="pageno">' + pad(i + 1) + '<small> / ' + pad(SLIDES.length) + '</small></div></div>' +
      '<div class="content">' +
      '<div class="kicker"><span class="dot"></span>' + s.kicker + '</div>' +
      '<h' + (s.layout === 'full' && i === 0 ? '1' : '2') + '>' + s.title +
      '</h' + (s.layout === 'full' && i === 0 ? '1' : '2') + '>' +
      (s.lead ? '<p class="lead">' + s.lead + '</p>' : '') +
      '<div class="' + stageCls + '">' + stageInner + '</div>' +
      '<div class="footer"><div class="source">' + (s.source || '') + '</div></div>' +
      '</div>';
    return el;
  }

  function pad(n) { return n < 10 ? '0' + n : String(n); }

  /* ========================= イメージモーダル ========================= */
  function openImage() {
    var s = SLIDES[idx];
    if (!s || !s.image) return;
    var im = s.image;
    var sceneKey = (im.scene && SCENES[im.scene]) ? im.scene : s.ambient;

    modal.innerHTML =
      '<div class="modal-wrap">' +
      '<button class="modal-close" type="button">閉じる ESC</button>' +
      '<div class="modal-head"><div>' +
      '<div class="modal-kicker">' + (im.kicker || 'イメージ') + '</div>' +
      '<h2>' + im.title + '</h2></div></div>' +
      '<div class="modal-body">' +
      '<div class="scene-stage">' + SCENES[sceneKey](true) +
      (im.caption ? '<div class="scene-cap">' + im.caption + '</div>' : '') + '</div>' +
      '<div class="scene-side">' + blocks(im.side) + '</div>' +
      '</div></div>';

    modal.querySelector('.modal-close').addEventListener('click', closeImage);
    modal.classList.add('open');
    imgBtn.classList.add('open');
    imgBtn.querySelector('.txt').textContent = '閉じる';
    SE.play('image');
  }

  function closeImage() {
    modal.classList.remove('open');
    modal.innerHTML = '';
    imgBtn.classList.remove('open');
    imgBtn.querySelector('.txt').textContent = 'イメージ';
  }

  function toggleImage() {
    if (modal.classList.contains('open')) { closeImage(); SE.play('image'); }
    else { openImage(); }
  }

  /* ========================= ナビゲーション ========================= */
  function show(n, opts) {
    opts = opts || {};
    var prevIdx = idx;
    idx = (n + SLIDES.length) % SLIDES.length;

    if (modal.classList.contains('open')) closeImage();

    slideEls.forEach(function (el, j) {
      el.classList.toggle('active', j === idx);
      el.classList.toggle('back', j === idx && opts.back === true);
    });

    progress.style.width = ((idx + 1) / SLIDES.length * 100) + '%';
    history.replaceState(null, '', '#' + (idx + 1));

    if (!opts.silent && prevIdx !== idx) SE.play('page');
  }

  function next() { show(idx + 1); }
  function prev() { show(idx - 1, { back: true }); }

  /* ========================= 初期化 ========================= */
  function init() {
    var frag = document.createDocumentFragment();
    SLIDES.forEach(function (s, i) {
      var el = buildSlide(s, i);
      slideEls.push(el);
      frag.appendChild(el);
    });
    deck.appendChild(frag);

    imgBtn.addEventListener('click', toggleImage);

    document.getElementById('btnPrev').addEventListener('click', prev);
    document.getElementById('btnNext').addEventListener('click', next);
    document.getElementById('btnFull').addEventListener('click', function () {
      if (document.fullscreenElement) document.exitFullscreen();
      else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
    });

    var btnMute = document.getElementById('btnMute');
    btnMute.addEventListener('click', function () {
      var m = SE.toggleMute();
      btnMute.textContent = m ? '🔇' : '🔊';
      btnMute.classList.toggle('off', m);
    });

    var btnWipe = document.getElementById('btnWipe');
    btnWipe.addEventListener('click', cycleWipe);

    /* --- キーボード --- */
    addEventListener('keydown', function (e) {
      if (['ArrowRight', ' ', 'PageDown'].indexOf(e.key) >= 0) { e.preventDefault(); next(); }
      else if (['ArrowLeft', 'PageUp'].indexOf(e.key) >= 0) { e.preventDefault(); prev(); }
      else if (e.key === 'Home') show(0);
      else if (e.key === 'End') show(SLIDES.length - 1);
      else if (e.key === 'Escape') { if (modal.classList.contains('open')) closeImage(); }
      else if (e.key === 'i' || e.key === 'I') toggleImage();
      else if (e.key === 'w' || e.key === 'W') cycleWipe();
      else if (e.key === 'd' || e.key === 'D') wipe.classList.toggle('debug');
      else if (e.key === 'm' || e.key === 'M') btnMute.click();
    });

    /* --- ホイール / スワイプ --- */
    var wheelLock = 0;
    addEventListener('wheel', function (e) {
      var now = Date.now();
      if (Math.abs(e.deltaY) > 45 && now - wheelLock > 380) {
        wheelLock = now;
        if (e.deltaY > 0) next(); else prev();
      }
    }, { passive: true });

    var sx = 0;
    addEventListener('touchstart', function (e) { sx = e.touches[0].clientX; }, { passive: true });
    addEventListener('touchend', function (e) {
      var d = e.changedTouches[0].clientX - sx;
      if (Math.abs(d) > 60) { if (d < 0) next(); else prev(); }
    }, { passive: true });

    /* --- 収録中はコントロールを自動的に隠す --- */
    var idleTimer;
    function poke() {
      controls.classList.remove('idle');
      clearTimeout(idleTimer);
      idleTimer = setTimeout(function () { controls.classList.add('idle'); }, 2600);
    }
    addEventListener('mousemove', poke);
    addEventListener('keydown', poke);
    poke();

    /* --- 最初の操作で音声を解禁する（ブラウザの自動再生制限対策） --- */
    function unlock() {
      SE.setVolume(SE.getVolume());
      if (audioNotice) audioNotice.classList.add('hide');
      removeEventListener('pointerdown', unlock);
      removeEventListener('keydown', unlock);
    }
    addEventListener('pointerdown', unlock);
    addEventListener('keydown', unlock);
    /* 収録中に映り込まないよう、操作が無くても数秒で引っ込める */
    setTimeout(function () { if (audioNotice) audioNotice.classList.add('hide'); }, 6000);

    var hash = parseInt(location.hash.slice(1), 10);
    show(hash ? hash - 1 : 0, { silent: true });
  }

  /* ワイプ表示モード: ガイドあり → 枠なし → クロマキー → ガイドあり */
  function cycleWipe() {
    if (wipe.classList.contains('chroma')) {
      wipe.classList.remove('chroma', 'bare');
    } else if (wipe.classList.contains('bare')) {
      wipe.classList.remove('bare');
      wipe.classList.add('chroma');
    } else {
      wipe.classList.add('bare');
    }
  }

  /* デバッグ用に外へ出す（衝突チェックのスクリプトから使う） */
  window.DECK = {
    show: show, next: next, prev: prev,
    openImage: openImage, closeImage: closeImage,
    count: function () { return SLIDES.length; },
    current: function () { return idx; }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
