"""タイトル画像を作る。

  python3 make_title.py [文字列] [出力.png]

白文字＋濃いフチ＋ドロップシャドウの PNG を書き出し、
横幅が動画からはみ出す場合は自動で縮小する。
サイズは <出力>_dims.json にも保存する。
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, os, sys

TEXT = sys.argv[1] if len(sys.argv) > 1 else "おなら以外"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "title.png"
TTC = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
VIDEO_W = 720

# --- .ttc の中から日本語フェイスを探す ---
jp_index = 0
for i in range(12):
    try:
        f = ImageFont.truetype(TTC, 100, index=i)
        if "JP" in f.getname()[0]:
            jp_index = i
            print(f"JP face at index {i}: {f.getname()}")
            break
    except Exception:
        break

FONT_SIZE = 104
font = ImageFont.truetype(TTC, FONT_SIZE, index=jp_index)

STROKE = 9          # フチの太さ
SHADOW_BLUR = 12
SHADOW_OFF = (0, 7)
PAD = STROKE + SHADOW_BLUR * 2 + 24   # フチとぼかしの余白

tmp = Image.new("RGBA", (10, 10))
bbox = ImageDraw.Draw(tmp).textbbox((0, 0), TEXT, font=font, stroke_width=STROKE)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

W, H = tw + PAD * 2, th + PAD * 2
ox, oy = PAD - bbox[0], PAD - bbox[1]

card = Image.new("RGBA", (W, H), (0, 0, 0, 0))

# --- 影 ---
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).text(
    (ox + SHADOW_OFF[0], oy + SHADOW_OFF[1]), TEXT, font=font,
    fill=(0, 0, 0, 170), stroke_width=STROKE, stroke_fill=(0, 0, 0, 170),
)
card = Image.alpha_composite(card, sh.filter(ImageFilter.GaussianBlur(SHADOW_BLUR)))

# --- 本体（白文字＋濃いフチ） ---
tx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(tx).text(
    (ox, oy), TEXT, font=font,
    fill=(255, 255, 255, 255), stroke_width=STROKE, stroke_fill=(26, 26, 32, 255),
)
card = Image.alpha_composite(card, tx)

# 横幅がはみ出すなら縮小（左右40pxずつ空ける）
max_w = VIDEO_W - 80
if W > max_w:
    r = max_w / W
    W, H = int(W * r), int(H * r)
    card = card.resize((W, H), Image.LANCZOS)

card.save(OUTPUT)
alpha_bbox = card.split()[-1].getbbox()
json.dump({"w": W, "h": H, "opaque_bbox": alpha_bbox},
          open(os.path.splitext(OUTPUT)[0] + "_dims.json", "w"))
print(f"{OUTPUT} {W}x{H}  文字の実描画域 {alpha_bbox}")
