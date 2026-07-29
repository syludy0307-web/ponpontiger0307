#!/usr/bin/env node
/* ===========================================================
   build-standalone.js
   -----------------------------------------------------------
   index.html + CSS + JS + 効果音(mp3) を 1 個の HTML にまとめる。

     node build-standalone.js

   出力: dist/熊本地震-爆発-20の論点.html
   ダブルクリックで開けば、そのまま動く（写真だけネット接続が要る）。
   =========================================================== */
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const OUT_DIR = path.join(ROOT, 'dist');
const OUT_FILE = path.join(OUT_DIR, '熊本地震-爆発-20の論点.html');

const read = p => fs.readFileSync(path.join(ROOT, p), 'utf8');
const b64 = p => fs.readFileSync(path.join(ROOT, p)).toString('base64');

/* インライン化した中身が <script> / <style> を途中で閉じてしまわないようにする */
const safe = s => s.replace(/<\/(script|style)/gi, '<\\/$1');

let html = read('index.html');

/* --- 効果音を data URI にする --- */
const sePage = 'data:audio/mpeg;base64,' + b64('assets/se/se-page.mp3');
const seImage = 'data:audio/mpeg;base64,' + b64('assets/se/se-image.mp3');

let deckJs = read('assets/js/deck.js')
  .replace("'assets/se/se-page.mp3'", JSON.stringify(sePage))
  .replace("'assets/se/se-image.mp3'", JSON.stringify(seImage));

/* コメント中の説明文にも同じパスが出てくるので、実際の呼び出しだけを見る */
if (/make\(\s*'assets\/se\//.test(deckJs) || !deckJs.includes(sePage) || !deckJs.includes(seImage)) {
  throw new Error('効果音のパスを data URI に置換できませんでした（deck.js の書き方が変わった？）');
}

/* --- CSS を <style> に --- */
html = html.replace(
  /<link rel="stylesheet" href="assets\/css\/deck\.css"\s*\/?>/,
  '<style>\n' + safe(read('assets/css/deck.css')) + '\n</style>'
);

/* --- JS を <script> に --- */
const scripts = [
  ['assets/js/scenes.js', safe(read('assets/js/scenes.js'))],
  ['assets/js/slides.js', safe(read('assets/js/slides.js'))],
  ['assets/js/deck.js', safe(deckJs)]
];
for (const [src, code] of scripts) {
  const tag = new RegExp('<script src="' + src.replace(/[/.]/g, '\\$&') + '"></script>');
  if (!tag.test(html)) throw new Error('script タグが見つかりません: ' + src);
  html = html.replace(tag, '<script>\n' + code + '\n</script>');
}

/* --- 取りこぼしがないか確認 --- */
const leftover = html.match(/(?:src|href)="assets\/(?!photos\/)[^"]+"/g);
if (leftover) throw new Error('インライン化できていない参照が残っています: ' + leftover.join(', '));

fs.mkdirSync(OUT_DIR, { recursive: true });
fs.writeFileSync(OUT_FILE, html, 'utf8');

console.log('出力: ' + path.relative(ROOT, OUT_FILE));
console.log('サイズ: ' + (Buffer.byteLength(html) / 1024 / 1024).toFixed(2) + ' MB');
console.log('外部参照: 写真(upload.wikimedia.org)のみ。CSS/JS/効果音は埋め込み済み。');
