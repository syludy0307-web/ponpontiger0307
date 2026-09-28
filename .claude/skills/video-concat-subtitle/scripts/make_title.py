#!/usr/bin/env python3
"""タイトル画像（白文字＋濃いフチ＋ドロップシャドウの透過 PNG）を作る。

  python make_title.py "悪だくみ" title.png --width 720

大きさは動画の横幅に比例させる（720px 基準）。長いタイトルは自動で縮めて収める。
<出力名>_dims.json に画像サイズと文字の実描画域を書く（render.py が位置決めに使う）。
ふつうは render.py が内部で呼ぶので、単体で使うのはタイトルだけ確認したいとき。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def make_title(text: str, out, video_w: int = 720) -> dict:
    from PIL import Image, ImageDraw, ImageFilter

    font_info = common.find_jp_font()
    if not font_info:
        sys.exit("日本語の太字フォントが見つかりません。scripts/setup_check.py の案内に従ってください。")
    s = video_w / 720.0
    font = common.load_font(font_info, round(104 * s))
    stroke, blur, off = round(9 * s), round(12 * s), round(7 * s)
    pad = stroke + blur * 2 + round(24 * s)          # フチとぼかしが切れない余白

    x0, y0, x1, y1 = ImageDraw.Draw(Image.new("RGBA", (10, 10))).textbbox(
        (0, 0), text, font=font, stroke_width=stroke)
    W, H = (x1 - x0) + pad * 2, (y1 - y0) + pad * 2
    ox, oy = pad - x0, pad - y0

    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((ox, oy + off), text, font=font, fill=(0, 0, 0, 170),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
    card = Image.alpha_composite(card, shadow.filter(ImageFilter.GaussianBlur(blur)))
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(body).text((ox, oy), text, font=font, fill=(255, 255, 255, 255),
                              stroke_width=stroke, stroke_fill=(26, 26, 32, 255))
    card = Image.alpha_composite(card, body)

    max_w = video_w - round(80 * s)                   # 左右に動画幅の約5.5%ずつ空ける
    if W > max_w:
        r = max_w / W
        W, H = int(W * r), int(H * r)
        card = card.resize((W, H), Image.LANCZOS)

    out = Path(out)
    card.save(out)
    dims = {"w": W, "h": H, "opaque_bbox": list(card.split()[-1].getbbox()),
            "video_w": video_w, "text": text, "font": font_info}
    out.with_name(out.stem + "_dims.json").write_text(
        json.dumps(dims, ensure_ascii=False, indent=1), encoding="utf-8")
    return dims


def main():
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text")
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=720, help="動画の横幅（px）")
    a = ap.parse_args()
    d = make_title(a.text, a.out, a.width)
    print(f"{a.out}  {d['w']}x{d['h']}  文字の実描画域 {tuple(d['opaque_bbox'])}  "
          f"フォント {d['font']['family']} {d['font']['style']}")


if __name__ == "__main__":
    main()
