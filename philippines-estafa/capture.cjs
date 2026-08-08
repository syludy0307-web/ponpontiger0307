// フレームキャプチャ: render.html の renderFrame(t) を 30fps で回して ffmpeg にパイプ
// 使い方:
//   NODE_PATH=/opt/node22/lib/node_modules node capture.cjs                # 本番レンダリング
//   NODE_PATH=/opt/node22/lib/node_modules node capture.cjs --stills 1.8,4.3,...  # プレビュー静止画
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { chromium } = require('playwright');
const TL = require('./timeline.js');

(async () => {
  const stillsArg = process.argv[2] === '--stills' ? process.argv[3] : null;
  const browser = await chromium.launch({
    args: ['--force-color-profile=srgb', '--font-render-hinting=none'],
  });
  const page = await browser.newPage({ viewport: { width: TL.W, height: TL.H }, deviceScaleFactor: 1 });
  page.on('pageerror', e => { console.error('PAGE ERROR:', e.message); process.exitCode = 1; });
  page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE:', m.text()); });
  await page.goto('file://' + path.join(__dirname, 'render.html'));
  await page.waitForFunction('window.READY===true', null, { timeout: 30000 });

  if (stillsArg) {
    fs.mkdirSync(path.join(__dirname, 'preview'), { recursive: true });
    for (const t of stillsArg.split(',').map(Number)) {
      await page.evaluate(tt => window.renderFrame(tt), t);
      await page.screenshot({ path: path.join(__dirname, 'preview', `still_${t.toFixed(2)}.png`) });
      console.log('still', t);
    }
    await browser.close();
    return;
  }

  fs.mkdirSync(path.join(__dirname, 'out'), { recursive: true });
  const ff = spawn('ffmpeg', [
    '-y', '-f', 'image2pipe', '-framerate', String(TL.FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-r', String(TL.FPS), path.join(__dirname, 'out', 'video_silent.mp4'),
  ], { stdio: ['pipe', 'ignore', 'inherit'] });

  const N = Math.round(TL.DUR * TL.FPS);
  const t0 = Date.now();
  for (let i = 0; i < N; i++) {
    const t = i / TL.FPS;
    const b64 = await page.evaluate(tt => {
      window.renderFrame(tt);
      return document.getElementById('c').toDataURL('image/jpeg', 0.95).split(',')[1];
    }, t);
    const ok = ff.stdin.write(Buffer.from(b64, 'base64'));
    if (!ok) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) {
      const el = (Date.now() - t0) / 1000;
      console.log(`frame ${i}/${N} (${el.toFixed(0)}s elapsed)`);
    }
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log(`done: ${N} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
})();
