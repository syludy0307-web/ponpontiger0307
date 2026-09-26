#!/usr/bin/env node
/*
  ゲンとモカ OP — 書き出し
    node export.mjs            … 全300フレーム + 音声 → out/genmoka_op_code.mp4
    node export.mjs --review   … 確認用静止画（f15/75/150/200/270）とコンタクトシート → out/review/
    node export.mjs --check    … 決定論チェック（同じフレームを描き直して差分ゼロか）＋カット境界
    オプション: --frames 0-59,120 … 指定フレームだけ PNG 化 / --no-video … MP4 を作らない
  必要: Node 18+, playwright（Chromium）, ffmpeg / ffprobe（PATH か環境変数 FFMPEG / FFPROBE）
*/
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, 'out');
const FRAMES = path.join(OUT, 'frames');
const REVIEW = path.join(OUT, 'review');
const HTML = path.join(HERE, 'genmoka_op.html');
const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const FFPROBE = process.env.FFPROBE || 'ffprobe';
const NF = 300, FPS = 30;

const argv = process.argv.slice(2);
const has = f => argv.includes(f);
const val = f => { const i = argv.indexOf(f); return i >= 0 ? argv[i + 1] : null; };
const mode = has('--review') ? 'review' : has('--check') ? 'check' : 'full';
const pad = n => String(n).padStart(4, '0');
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const sha = b => crypto.createHash('sha256').update(b).digest('hex').slice(0, 16);

function parseFrames(spec) {
  const set = new Set();
  for (const part of spec.split(',')) {
    const m = part.match(/^(\d+)(?:-(\d+))?$/); if (!m) continue;
    const a = +m[1], b = m[2] ? +m[2] : a; for (let i = a; i <= b; i++) if (i >= 0 && i < NF) set.add(i);
  }
  return [...set].sort((x, y) => x - y);
}

function run(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', maxBuffer: 1 << 26, ...opts });
  if (r.error) throw new Error(`${cmd} を実行できません: ${r.error.message}（ffmpeg を PATH に入れるか FFMPEG 環境変数で指定）`);
  if (r.status !== 0) throw new Error(`${cmd} failed (${r.status}):\n${r.stderr.slice(-3000)}`);
  return r;
}

async function openPage() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('[pageerror]', e.message));
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.error('[console]', m.text()); });
  await page.goto(pathToFileURL(HTML).href + '?export=1');
  await page.waitForFunction(() => window.__gm && (window.__gm.ready || window.__gm.error), null, { timeout: 0 });
  const st = await page.evaluate(() => ({ ready: window.__gm.ready, error: window.__gm.error, fontsOK: window.__gm.fontsOK }));
  if (st.error) throw new Error('ページ初期化エラー:\n' + st.error);
  if (!st.fontsOK) throw new Error('フォントが読み込めていません（build_fonts.py を実行してください）');
  return { browser, page };
}

async function grab(page, n) {
  const url = await page.evaluate(k => { window.renderFrame(k); return document.getElementById('stage').toDataURL('image/png'); }, n);
  return Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
}

async function review(page) {
  fs.mkdirSync(REVIEW, { recursive: true });
  for (const n of [15, 75, 150, 200, 270]) {
    fs.writeFileSync(path.join(REVIEW, `f${String(n).padStart(3, '0')}.png`), await grab(page, n));
    log('review still', n);
  }
  const sheet = await page.evaluate(() => {
    const list = [15, 45, 75, 105, 135, 165, 195, 225, 255, 285];
    const cw = 480, ch = 270, padX = 16, lab = 30, cols = 5;
    const c = document.createElement('canvas'); c.width = cols * cw + (cols + 1) * padX; c.height = 2 * (ch + lab) + 3 * padX;
    const x = c.getContext('2d'); x.fillStyle = '#111'; x.fillRect(0, 0, c.width, c.height);
    x.imageSmoothingQuality = 'high'; x.font = '600 18px sans-serif';
    list.forEach((n, i) => {
      window.renderFrame(n);
      const cx = padX + (i % cols) * (cw + padX), cy = padX + Math.floor(i / cols) * (ch + lab + padX);
      x.drawImage(document.getElementById('stage'), cx, cy + lab, cw, ch);
      x.fillStyle = '#ddd'; x.fillText(`f${n}  ${(n / 30).toFixed(2)}s  CUT${[0, 60, 120, 180, 240].filter(v => n >= v).length}`, cx, cy + 21);
    });
    return c.toDataURL('image/png');
  });
  fs.writeFileSync(path.join(REVIEW, 'contact_sheet.png'), Buffer.from(sheet.split(',')[1], 'base64'));
  log('contact sheet → out/review/contact_sheet.png');
}

async function check(page) {
  // 同じフレームを、間に別フレームを挟みながら2回描いてハッシュを比較
  const targets = [0, 15, 59, 60, 75, 119, 120, 150, 179, 180, 200, 239, 240, 270, 299];
  const first = {};
  for (const n of targets) first[n] = sha(await grab(page, n));
  let bad = 0;
  for (const n of targets.slice().reverse()) {
    await grab(page, (n * 7 + 13) % NF);
    const h = sha(await grab(page, n)), ok = h === first[n];
    if (!ok) bad++;
    log(`f${n}: ${first[n]} vs ${h} ${ok ? 'OK' : 'DIFF'}`);
  }
  const cuts = await page.evaluate(() => [59, 60, 119, 120, 179, 180, 239, 240].map(n => [n, cutOf(n)]));
  log('cut boundaries:', cuts.map(([n, c]) => `f${n}=CUT${c + 1}`).join(' '));
  log(bad ? `決定論チェック: ${bad} 件の差分あり` : '決定論チェック: 差分ゼロ（ピクセル一致）');
  const a1 = await page.evaluate(() => window.renderAudio());
  const a2 = await page.evaluate(() => { AUDIO_BUF = null; return window.renderAudio(); });
  const aok = sha(a1) === sha(a2);
  log('audio determinism:', aok ? 'OK（WAV バイト一致）' : 'DIFF');
  return bad + (aok ? 0 : 1);
}

async function full(page, frames) {
  fs.mkdirSync(FRAMES, { recursive: true });
  const t0 = Date.now();
  for (let i = 0; i < frames.length; i++) {
    const n = frames[i];
    fs.writeFileSync(path.join(FRAMES, `${pad(n)}.png`), await grab(page, n));
    if (i % 10 === 0 || i === frames.length - 1) log(`frame ${n} (${i + 1}/${frames.length})  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  const wav = await page.evaluate(() => window.renderAudio());
  fs.writeFileSync(path.join(OUT, 'audio.wav'), Buffer.from(wav, 'base64'));
  log('audio → out/audio.wav');
}

function measure(file) {
  const r = run(FFMPEG, ['-hide_banner', '-nostats', '-i', file, '-af', 'ebur128=peak=true', '-f', 'null', '-']);
  const tail = r.stderr.slice(r.stderr.lastIndexOf('Summary:'));
  return { I: parseFloat((tail.match(/I:\s+(-?[\d.]+) LUFS/) || [])[1]), TP: parseFloat((tail.match(/Peak:\s+(-?[\d.]+) dBFS/) || [])[1]) };
}

function encode() {
  const wav = path.join(OUT, 'audio.wav'), mp4 = path.join(OUT, 'genmoka_op_code.mp4');
  const vtmp = path.join(OUT, '_video.mp4'), atmp = path.join(OUT, '_audio_norm.wav'), aac = path.join(OUT, '_audio.m4a');
  // 映像：連番PNG → H.264（BT.709 で YUV 変換）
  log('encode video (libx264 slow, CRF16) ...');
  run(FFMPEG, ['-hide_banner', '-y', '-framerate', String(FPS), '-i', path.join(FRAMES, '%04d.png'),
    '-vf', 'scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-x264-params', 'aq-mode=3',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-frames:v', String(NF), '-an', vtmp]);
  // 音声：loudnorm 2パス（1回目で計測 → 2回目は linear で -16 LUFS へ）
  const r1 = run(FFMPEG, ['-hide_banner', '-nostats', '-i', wav, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-']);
  const js = JSON.parse(r1.stderr.slice(r1.stderr.lastIndexOf('{'), r1.stderr.lastIndexOf('}') + 1));
  log('loudness (input):', js.input_i, 'LUFS, TP', js.input_tp);
  run(FFMPEG, ['-hide_banner', '-y', '-i', wav, '-af',
    `loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=${js.input_i}:measured_TP=${js.input_tp}:measured_LRA=${js.input_lra}:measured_thresh=${js.input_thresh}:offset=${js.target_offset}:linear=true,aresample=48000`,
    '-c:a', 'pcm_f32le', atmp]);
  // AAC 化 → 実測して残差を補正（AAC 化で 0.x dB ずれるため）
  let gain = 0;
  for (let pass = 0; pass < 3; pass++) {
    run(FFMPEG, ['-hide_banner', '-y', '-i', atmp, '-af', `volume=${gain.toFixed(2)}dB`, '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', aac]);
    const m = measure(aac);
    log(`AAC pass ${pass + 1}: I ${m.I} LUFS, TP ${m.TP} dBFS (gain ${gain.toFixed(2)} dB)`);
    if (Math.abs(m.I + 16) <= 0.1) break;
    gain += (-16 - m.I);
  }
  // 結合（映像はコピー、音声もコピー）
  run(FFMPEG, ['-hide_banner', '-y', '-i', vtmp, '-i', aac, '-map', '0:v', '-map', '1:a', '-c', 'copy', '-t', '10', '-movflags', '+faststart', mp4]);
  for (const f of [vtmp, atmp, aac]) fs.rmSync(f, { force: true });
  const pr = run(FFPROBE, ['-v', 'error', '-show_entries', 'stream=codec_name,profile,width,height,r_frame_rate,nb_frames,pix_fmt,sample_rate,channels,bit_rate:format=duration,size', '-of', 'json', mp4]);
  const info = JSON.parse(pr.stdout), fin = measure(mp4);
  log('output:', mp4);
  log(JSON.stringify(info));
  log(`loudness (output): ${fin.I} LUFS, true peak ${fin.TP} dBFS`);
  return { mp4, info, loud: fin };
}

(async () => {
  const T0 = Date.now();
  fs.mkdirSync(OUT, { recursive: true });
  const { browser, page } = await openPage();
  log('page ready', ((Date.now() - T0) / 1000).toFixed(1) + 's');
  try {
    if (mode === 'review') await review(page);
    else if (mode === 'check') process.exitCode = (await check(page)) ? 1 : 0;
    else {
      const frames = val('--frames') ? parseFrames(val('--frames')) : [...Array(NF).keys()];
      await full(page, frames);
      if (!has('--no-video') && frames.length === NF) encode();
    }
  } finally { await browser.close(); }
  log(`total ${((Date.now() - T0) / 1000).toFixed(1)}s`);
})().catch(e => { console.error(e); process.exit(1); });
