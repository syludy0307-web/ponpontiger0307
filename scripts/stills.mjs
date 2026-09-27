// プレビュー画像(4枚、エンドカード付きなら5枚)を書き出す: node scripts/stills.mjs
// 追加でフレーム番号を渡すと、確認用に output/previews/extra/ へ書き出す: node scripts/stills.mjs 120 126
import {bundle} from '@remotion/bundler';
import {openBrowser, renderStill, selectComposition} from '@remotion/renderer';
import {mkdirSync} from 'node:fs';
import path from 'node:path';

const PREVIEWS = [
  {sec: 1.0, file: 'preview_01_quiz_1.0s.png'}, // 質問の読みやすさ
  {sec: 4.4, file: 'preview_02_answer_4.4s.png'}, // 答えとアイコン(集中線は 4.00〜4.35秒)
  {sec: 9.0, file: 'preview_03_explain_9.0s.png'}, // 解説(September の綴りと配色)
  {sec: 13.0, file: 'preview_04_recap_13.0s.png'}, // 復習テロップの配置
];

const outDir = path.resolve('output/previews');
const browserExecutable = process.env.REMOTION_BROWSER_EXECUTABLE ?? null;
const extraFrames = process.argv.slice(2).map(Number).filter(Number.isFinite);

const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const browser = await openBrowser('chrome', {browserExecutable});
const composition = await selectComposition({serveUrl, id: 'DanceTrivia', puppeteerInstance: browser});

// エンドカード付き(16秒より長い)なら、エンドカードの確認用に5枚目を足す
const previews = composition.durationInFrames > 16 * composition.fps
  ? [...PREVIEWS, {sec: 17.5, file: 'preview_05_endcard_17.5s.png'}]
  : PREVIEWS;

const jobs = extraFrames.length
  ? extraFrames.map((frame) => ({frame, file: path.join('extra', `frame_${String(frame).padStart(3, '0')}.png`)}))
  : previews.map((p) => ({frame: Math.round(p.sec * composition.fps), file: p.file}));

for (const job of jobs) {
  const output = path.join(outDir, job.file);
  mkdirSync(path.dirname(output), {recursive: true});
  await renderStill({composition, serveUrl, output, frame: job.frame, imageFormat: 'png', puppeteerInstance: browser});
  console.log(`frame ${job.frame} (${(job.frame / composition.fps).toFixed(2)}s) -> ${path.relative(process.cwd(), output)}`);
}
await browser.close({silent: true});
