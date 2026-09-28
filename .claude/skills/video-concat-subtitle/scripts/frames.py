#!/usr/bin/env python3
"""指定した時刻のコマを並べた1枚の画像（コンタクトシート）を作る。

話者の確認（その瞬間に誰が映っていて、誰の口が動いているか）や、
タイトル・字幕の見え方のチェックに使う。できた画像は Read ツールで開いて目で見る。

  # 連結前のクリップに対して（時刻は連結後の通し時刻）
  python frames.py --clips 001.mov 002.mov 003.mov --at 2.2 16.0 34.8 \
                   --labels "1 お姉ちゃん来ない" "5 なんで私に" "11 はい" --out WORK/who.jpg

  # 書き出した動画に対して
  python frames.py --video WORK/final.mp4 --at 2.0 10.5 --out WORK/check.jpg
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


def _grab(path: str, t: float, width: int, out: Path) -> Path:
    r = common.run([common.ffmpeg(), "-v", "error", "-ss", f"{t:.3f}", "-i", path,
                    "-frames:v", "1", "-vf", f"scale={width}:-2", "-y", out])
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


def sheet_from_clips(clip_paths: list, times: list, labels: list, out, width: int = 240) -> None:
    clips = [common.probe(p) for p in clip_paths]
    with tempfile.TemporaryDirectory() as td:
        items = []
        for k, t in enumerate(times):
            c, lt = _locate(clips, t)
            items.append((_grab(c["path"], lt, width, Path(td) / f"f{k}.png"),
                          labels[k] if k < len(labels) else f"{t:.2f}s"))
        _compose(items, out, width)


def sheet_from_video(video: str, times: list, labels: list, out, width: int = 240) -> None:
    with tempfile.TemporaryDirectory() as td:
        items = [(_grab(video, t, width, Path(td) / f"f{k}.png"),
                  labels[k] if k < len(labels) else f"{t:.2f}s") for k, t in enumerate(times)]
        _compose(items, out, width)


def main() -> None:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--clips", nargs="+", help="連結前のクリップ（番号順）")
    src.add_argument("--video", help="1本の動画")
    ap.add_argument("--at", nargs="+", type=float, required=True, help="時刻（秒）")
    ap.add_argument("--labels", nargs="*", default=[], help="各コマの下に書く説明")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=240)
    a = ap.parse_args()
    if a.clips:
        sheet_from_clips(a.clips, a.at, a.labels, a.out, a.width)
    else:
        sheet_from_video(a.video, a.at, a.labels, a.out, a.width)
    print(f"保存: {a.out}  （Read ツールで開いて確認する）")


if __name__ == "__main__":
    main()
