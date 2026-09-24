// 完成動画を書き出す: npm run render
// 出力: output/philippines_cr_dance_15s.mp4
//       1080x1920 / 30fps / H.264 yuv420p CRF18 / AAC 192kbps / faststart
//
// 手順
//  1. Remotion で映像だけを書き出す(テロップ合成済み・音声なし)
//  2. 元動画の音声を、同じ区間(trimStartSeconds から映像と同じ長さ)で AAC にして合わせる
//     ※ Remotion 内部の AAC は先頭のプライミング分(約43ms)音が遅れるため、
//       元動画から直接エンコードして音ズレ 0 にしている
import {spawnSync} from 'node:child_process';
import {closeSync, mkdirSync, openSync, readFileSync, readSync, rmSync, statSync, writeFileSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';

const OUT = 'output/philippines_cr_dance_15s.mp4';
const VIDEO_ONLY = 'output/.video_only.mp4';
const isWin = process.platform === 'win32';

const npx = (args, {capture = false} = {}) => {
  const r = spawnSync(isWin ? 'npx.cmd' : 'npx', args, {
    stdio: capture ? ['ignore', 'pipe', 'inherit'] : 'inherit',
    shell: isWin,
    encoding: 'utf8',
  });
  if (r.status !== 0) {
    process.exit(r.status ?? 1);
  }
  return r.stdout;
};

/** src/config.ts を読み込む(設定はこのファイル1か所だけ) */
const loadConfig = async () => {
  const source = readFileSync('src/config.ts', 'utf8');
  const js = ts.transpileModule(source, {
    compilerOptions: {module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022},
  }).outputText;
  const tmp = path.join(os.tmpdir(), `cr-config-${process.pid}.mjs`);
  writeFileSync(tmp, js);
  try {
    return (await import(pathToFileURL(tmp).href)).config;
  } finally {
    rmSync(tmp, {force: true});
  }
};

/** MP4 の最上位ボックスの並び(moov が mdat より前なら faststart 済み) */
const topLevelBoxes = (file) => {
  const fd = openSync(file, 'r');
  const size = statSync(file).size;
  const boxes = [];
  const head = Buffer.alloc(16);
  let pos = 0;
  while (pos + 8 <= size) {
    readSync(fd, head, 0, 16, pos);
    let len = head.readUInt32BE(0);
    if (len === 1) {
      len = Number(head.readBigUInt64BE(8));
    } else if (len === 0) {
      len = size - pos;
    }
    boxes.push(head.toString('latin1', 4, 8));
    if (len < 8) {
      break;
    }
    pos += len;
  }
  closeSync(fd);
  return boxes;
};

const config = await loadConfig();
const input = path.join('public', config.video.src);
mkdirSync('output', {recursive: true});

// 1. 映像(テロップ合成済み・音声なし)
npx(['remotion', 'render', 'src/index.ts', 'PhilippinesCR', VIDEO_ONLY, '--muted']);

// 2. 元動画の音声を同じ区間で合わせる(音声が無い素材なら無音のまま)
const duration = npx(['remotion', 'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', VIDEO_ONLY], {
  capture: true,
}).trim();
const hasAudio =
  npx(['remotion', 'ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', input], {
    capture: true,
  }).trim() !== '';

const args = ['remotion', 'ffmpeg', '-v', 'error', '-y', '-i', VIDEO_ONLY];
if (hasAudio) {
  if (config.video.trimStartSeconds > 0) {
    args.push('-ss', String(config.video.trimStartSeconds));
  }
  args.push('-i', input, '-map', '0:v:0', '-map', '1:a:0', '-c:a', 'aac', '-b:a', '192k');
  if (config.video.volume !== 1) {
    args.push('-af', `volume=${config.video.volume}`);
  }
} else {
  args.push('-map', '0:v:0');
  console.log('元動画に音声が無いため、無音で書き出します');
}
args.push('-c:v', 'copy', '-t', duration, '-movflags', '+faststart', OUT);
npx(args);
rmSync(VIDEO_ONLY, {force: true});

// 3. 仕様の確認
console.log(`\nMP4 boxes: ${topLevelBoxes(OUT).join(' > ')}`);
npx([
  'remotion', 'ffprobe', '-v', 'error',
  '-show_entries', 'format=duration,size:stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,nb_frames,sample_rate,channels,bit_rate',
  '-of', 'default=nw=1', OUT,
]);
console.log(`\n書き出し完了: ${OUT}`);
