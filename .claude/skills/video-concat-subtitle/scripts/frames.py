#!/usr/bin/env python3
"""指定した時刻のコマを並べた1枚の画像（コンタクトシート）を作る。

話者の確認（その瞬間に誰が映っていて、誰の口が動いているか）や、
タイトル・字幕の見え方のチェックに使う。できた画像は Read ツールで開いて目で見る。

  # 連結前のクリップに対して（時刻は連結後の通し時刻）
  python frames.py --clips 001.mov 002.mov 003.mov --at 2.2 16.0 34.8 \
                   --labels "1 お姉ちゃん来ない" "5 なんで私に" "11 はい" --out WORK/who.jpg

  # 書き出した動画に対して
  python frames.py --video WORK/final.mp4 --at 2.0 10.5 --out WORK/check.jpg

  # 口元を拡大して、0.2秒ごとに並べる（誰の口が動いているか見るとき）
  #   --crop は 左上X,左上Y,幅,高さ を画面に対する割合（0〜1）で指定
  python frames.py --clips 001.mov --range 7.0 9.0 --step 0.2 --crop 0.35,0.15,0.5,0.35 --out WORK/mouth.jpg
"""
from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def _locate(clips: list, t: float):
    acc = 0.0
    for i, c in enumerate(clips):
        if t < acc + c["duration"] or i == len(clips) - 1:
            return c, max(0.0, min(t - acc, c["duration"] - 0.05))
        acc += c["duration"]


def _grab(path: str, t: float, width: int, out: Path, crop=None) -> Path:
    vf = f"scale={width}:-2"
    if crop:
        x, y, w, h = crop
        vf = f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y}," + vf
    r = common.run([common.ffmpeg(), "-v", "error", "-ss", f"{t:.3f}", "-i", path,
                    "-frames:v", "1", "-vf", vf, "-y", out])
    if r.returncode != 0 or not out.exists():
        sys.exit(f"コマの取り出しに失敗: {path} @ {t:.2f}s\n{r.stderr}")
    return out


def _compose(items: list, out, width: int, per_row: int = 5) -> None:
    from PIL import Image, ImageDraw

    thumbs = [Image.open(p).convert("RGB") for p, _ in items]
    labels = [lab for _, lab in items]
    font_info = common.find_jp_font()
    font = common.load_font(font_info, max(12, width // 14)) if font_info else None
    label_h = (font.size * 2 + 10) if (font and any(labels)) else 0
    th = max(im.height for im in thumbs)
    cols = min(per_row, len(thumbs))
    rows = math.ceil(len(thumbs) / cols)
    gap = 8
    sheet = Image.new("RGB", (cols * width + (cols - 1) * gap, rows * (th + label_h) + (rows - 1) * gap), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (im, lab) in enumerate(zip(thumbs, labels)):
        x = (i % cols) * (width + gap)
        y = (i // cols) * (th + label_h + gap)
        sheet.paste(im, (x, y))
        if font and lab:
            lines, cur = [], ""
            for ch in lab:                      # 幅に合わせて最大2行に折り返す
                if draw.textlength(cur + ch, font=font) > width - 4:
                    lines.append(cur)
                    cur = ch
                else:
                    cur += ch
            lines.append(cur)
            if len(lines) > 2:
                lines = [lines[0], lines[1][:-1] + "…"]
            for k, line in enumerate(lines):
                draw.text((x + 2, y + th + 3 + k * (font.size + 2)), line, fill="black", font=font)
    sheet.save(out, quality=88)


def sheet_from_clips(clip_paths: list, times: list, labels: list, out, width: int = 240, crop=None) -> None:
    clips = [common.probe(p) for p in clip_paths]
    with tempfile.TemporaryDirectory() as td:
        items = []
        for k, t in enumerate(times):
            c, lt = _locate(clips, t)
            items.append((_grab(c["path"], lt, width, Path(td) / f"f{k}.png", crop),
                          labels[k] if k < len(labels) else f"{t:.2f}s"))
        _compose(items, out, width)


def sheet_from_video(video: str, times: list, labels: list, out, width: int = 240, crop=None) -> None:
    with tempfile.TemporaryDirectory() as td:
        items = [(_grab(video, t, width, Path(td) / f"f{k}.png", crop),
                  labels[k] if k < len(labels) else f"{t:.2f}s") for k, t in enumerate(times)]
        _compose(items, out, width)


def main() -> None:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--clips", nargs="+", help="連結前のクリップ（番号順）")
    src.add_argument("--video", help="1本の動画")
    ap.add_argument("--at", nargs="+", type=float, default=[], help="時刻（秒）")
    ap.add_argument("--range", nargs=2, type=float, metavar=("開始", "終了"), help="この区間を --step ごとに並べる")
    ap.add_argument("--step", type=float, default=0.25, help="--range の間隔（秒）")
    ap.add_argument("--crop", default=None, help="拡大する範囲 X,Y,幅,高さ（画面に対する割合 0〜1）")
    ap.add_argument("--labels", nargs="*", default=[], help="各コマの下に書く説明")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=240)
    a = ap.parse_args()
    times = list(a.at)
    if a.range:
        t, end = a.range
        while t <= end + 1e-6:
            times.append(round(t, 3))
            t += a.step
    if not times:
        ap.error("--at か --range のどちらかで時刻を指定してください")
    crop = None
    if a.crop:
        crop = [float(v) for v in a.crop.split(",")]
        if len(crop) != 4 or not all(0 <= v <= 1 for v in crop):
            ap.error("--crop は 0〜1 の数を4つ（X,Y,幅,高さ）")
    if a.clips:
        sheet_from_clips(a.clips, times, a.labels, a.out, a.width, crop)
    else:
        sheet_from_video(a.video, times, a.labels, a.out, a.width, crop)
    print(f"保存: {a.out}  （{len(times)}コマ。Read ツールで開いて確認する）")


if __name__ == "__main__":
    main()
