from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json

TEXT = "おなら以外"
TTC = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
VIDEO_W = 720

# --- locate the JP face inside the .ttc ---
jp_index = 0
for i in range(12):
    try:
        f = ImageFont.truetype(TTC, 100, index=i)
        name = f.getname()
        if "JP" in name[0]:
            jp_index = i
            print(f"JP face at index {i}: {name}")
            break
    except Exception:
        break

FONT_SIZE = 104
font = ImageFont.truetype(TTC, FONT_SIZE, index=jp_index)

STROKE = 9          # dark outline width
SHADOW_BLUR = 12
SHADOW_OFF = (0, 7)
PAD = STROKE + SHADOW_BLUR * 2 + 24   # room for outline + blurred shadow

# measure text with stroke
tmp = Image.new("RGBA", (10, 10))
d = ImageDraw.Draw(tmp)
bbox = d.textbbox((0, 0), TEXT, font=font, stroke_width=STROKE)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

W = tw + PAD * 2
H = th + PAD * 2
ox, oy = PAD - bbox[0], PAD - bbox[1]

card = Image.new("RGBA", (W, H), (0, 0, 0, 0))

# --- soft drop shadow ---
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).text(
    (ox + SHADOW_OFF[0], oy + SHADOW_OFF[1]), TEXT, font=font,
    fill=(0, 0, 0, 170), stroke_width=STROKE, stroke_fill=(0, 0, 0, 170),
)
sh = sh.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
card = Image.alpha_composite(card, sh)

# --- text: white fill, deep charcoal outline ---
tx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(tx).text(
    (ox, oy), TEXT, font=font,
    fill=(255, 255, 255, 255), stroke_width=STROKE, stroke_fill=(26, 26, 32, 255),
)
card = Image.alpha_composite(card, tx)

# scale down if wider than the frame (keep 40px side margins)
max_w = VIDEO_W - 80
if W > max_w:
    r = max_w / W
    W, H = int(W * r), int(H * r)
    card = card.resize((W, H), Image.LANCZOS)

card.save("title.png")
json.dump({"w": W, "h": H}, open("title_dims.json", "w"))
print(f"title.png {W}x{H}  (font {FONT_SIZE}, stroke {STROKE})")
