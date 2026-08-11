# -*- coding: utf-8 -*-
"""Scene still builders.  Each returns a 2688x1512 RGB PIL image.

Registry BUILDERS maps art names used in scenes.py to builder functions.
Overlay ghost layers (RGBA) are built by OVERLAYS.
"""
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from common import AW, AH
import art_base as B


# ---------------------------------------------------------------- helpers
def finish(img, lift=(8, 10, 14), gain=(228, 234, 242), sat=0.8, vig=0.55,
           halo=None, seed=1, dirt_amt=0.05, gamma=1.0):
    img = ImageOps.autocontrast(img, cutoff=(0.4, 0.1), preserve_tone=True)
    img = ImageEnhance.Brightness(img).enhance(1.10)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img = B.grade(img, lift, gain, gamma, sat)
    if halo:
        img = B.halation(img, *halo)
    img = B.vignette(img, min(vig * 0.8, 0.6))
    if dirt_amt:
        img = B.dirt(img, seed + 77, dirt_amt)
    return img


def texture_board(seed, base=(13, 15, 19), smear=None):
    """Dark concrete backplate used for card scenes."""
    img = B.new_canvas((base[0] + 6, base[1] + 6, base[2] + 8), base)
    n = B.vnoise(AW // 2, AH // 2, 14, seed, 5)
    n = Image.fromarray((n * 60).astype(np.uint8)).resize((AW, AH))
    img = ImageChops.subtract(img, Image.merge("RGB", (n, n, n)))
    st = B.streaks(AW, AH, seed + 3, density=10, blur=8)
    img = Image.composite(Image.new("RGB", img.size, (4, 5, 7)), img,
                          Image.fromarray((st * 90).astype(np.uint8)))
    if smear:
        ov = Image.new("RGB", img.size, (0, 0, 0))
        d = ImageDraw.Draw(ov)
        y = AH * smear.get("y", 0.5)
        d.ellipse([AW * 0.1, y - 130, AW * 0.9, y + 130], fill=smear.get("color", (64, 10, 14)))
        ov = ov.filter(ImageFilter.GaussianBlur(120))
        img = ImageChops.screen(img, ov)
    return img


def ghost_number(img, num, cx=0.78, cy=0.52, size=1500, alpha=26):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f = B.font(size, "black")
    d.text((img.width * cx, img.height * cy), num, font=f, anchor="mm",
           fill=(190, 200, 210, alpha))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def kanji_watermark(img, ch, cx=0.82, cy=0.5, size=1150, alpha=16, serif=True,
                    color=(200, 60, 66)):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f = B.font(size, serif=serif)
    d.text((img.width * cx, img.height * cy), ch, font=f, anchor="mm", fill=(*color, alpha))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def nv_process(img, seed):
    """Night-vision camcorder bake: green mono + scanlines + sensor noise."""
    g = ImageOps.grayscale(img)
    g = ImageOps.autocontrast(g, cutoff=1)
    arr = np.asarray(g, np.float32) / 255.0
    r = (arr * 70).astype(np.uint8)
    gr = (np.clip(arr * 1.25, 0, 1) * 225).astype(np.uint8)
    b = (arr * 78).astype(np.uint8)
    img = Image.merge("RGB", (Image.fromarray(r), Image.fromarray(gr), Image.fromarray(b)))
    noise = np.random.default_rng(seed).normal(0, 14, (AH // 2, AW // 2, 3))
    noise = Image.fromarray(np.clip(noise + 128, 0, 255).astype(np.uint8)).resize((AW, AH))
    img = ImageChops.add(img, ImageChops.subtract(noise, Image.new("RGB", (AW, AH), (128, 128, 128))))
    sl = np.ones((AH, 1), np.float32)
    sl[::4] = 0.82
    sl_img = Image.fromarray((np.tile(sl, (1, AW)) * 255).astype(np.uint8))
    img = ImageChops.multiply(img, Image.merge("RGB", (sl_img, sl_img, sl_img)))
    return B.vignette(img, 0.72)


# ================================================================ INTRO
def title_night_front(seed=10):
    img = B.new_canvas((5, 8, 16), (13, 20, 30))
    img = B.add_glow(img, AW * 0.76, AH * 0.16, 300, (108, 122, 148), 0.5)  # moon haze
    d = ImageDraw.Draw(img)
    d.ellipse([AW * 0.76 - 52, AH * 0.16 - 52, AW * 0.76 + 52, AH * 0.16 + 52],
              fill=(196, 205, 218))
    # tree line behind
    for i, tx in enumerate(np.linspace(-80, AW + 80, 15)):
        B.tree_blob(img, tx, AH * 0.62 + (i % 3) * 16, 120, (7, 10, 13), seed + i)
    pal = dict(wall=(30, 36, 46))
    B.draw_building(img, AW * 0.20, AH * 0.30, AW * 0.80, AH * 0.78, pal, seed,
                    floors=5, bays=11, broken_p=0.3, sign="○○病院")
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.78, AW, AH], fill=(9, 12, 16))
    B.draw_pole(d, AW * 0.09, AH * 0.86, AH * 0.5)
    B.draw_pole(d, AW * 0.93, AH * 0.88, AH * 0.44)
    B.wires(d, AW * 0.09, AW * 0.93, AH * 0.40, sag=40)
    img = B.fog_bands(img, seed, 0.55, (84, 98, 112), y0=0.42)
    img = kanji_watermark(img, "怨", 0.5, 0.42, 1350, 12)
    return finish(img, lift=(6, 8, 15), gain=(206, 218, 235), sat=0.72, vig=0.62,
                  halo=(180, 30, 0.5), seed=seed)


def _corridor_base(pal, seed, **kw):
    img = B.new_canvas((10, 12, 15), (16, 19, 23))
    img, proj = B.corridor_geometry(img, pal, seed, **kw)
    return img, proj


def flashback_corridor(seed=20):
    pal = dict(floor=(148, 132, 108), ceil=(178, 170, 156), wallL=(168, 152, 128),
               wallR=(150, 136, 114), door=(120, 96, 70), light_on=(255, 244, 214),
               light_off=(236, 228, 208), glow=(255, 240, 200), refl=(220, 205, 175),
               end=(160, 150, 128), flicker_idx=1)
    img = B.new_canvas((160, 150, 132), (120, 110, 94))
    img, proj = B.corridor_geometry(img, pal, seed, doors=5, end="window",
                                    lights=4, debris=0.0)
    # bustling silhouettes (nurse + patients), soft
    for cx, z, hgt, kind in [(0.36, 5.2, 0.34, "pale"), (0.60, 3.4, 0.46, "shadow"),
                             (0.47, 7.5, 0.24, "shadow")]:
        x, y = proj(z, (cx - 0.5) * 2, 1.0)
        fig = B.fig_humanoid(int(AH * hgt), "shadow", seed + int(z))
        fig = ImageEnhance.Brightness(fig).enhance(1.0)
        B.paste_center(img, fig, x, y - fig.height * 0.48, 1.0)
    img = B.add_glow(img, AW * 0.5, AH * 0.40, AW * 0.3, (255, 236, 190), 0.5)
    return finish(img, lift=(26, 20, 12), gain=(255, 246, 224), sat=1.0, vig=0.42,
                  halo=(200, 40, 0.7), seed=seed, dirt_amt=0.02)


def decay_corridor_a(seed=30):
    pal = dict(floor=(28, 33, 36), ceil=(30, 36, 40), wallL=(44, 52, 56),
               wallR=(36, 44, 48), door=(52, 58, 60), light_on=(148, 170, 158),
               light_off=(26, 30, 33), glow=(120, 150, 138), refl=(52, 66, 68),
               flicker_idx=1, debris=(14, 16, 17))
    img, _ = _corridor_base(pal, seed, doors=5, end="black", lights=4, debris=1.0)
    img = B.fog_bands(img, seed, 0.35, (70, 88, 96), y0=0.5)
    return finish(img, lift=(6, 9, 12), gain=(198, 214, 220), sat=0.62, vig=0.6,
                  halo=(170, 34, 0.5), seed=seed)


def japan_map(seed=40):
    img = texture_board(seed, base=(9, 12, 20))
    # faint grid
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, AW, 96):
        d.line([x, 0, x, AH], fill=(70, 110, 130, 14), width=1)
    for y in range(0, AH, 96):
        d.line([0, y, AW, y], fill=(70, 110, 130, 14), width=1)
    # rough stylized Japan (angular TV-graphic look), map space 1000x1000
    HON = [(700, 300), (742, 362), (762, 432), (752, 500), (726, 556), (738, 596),
           (700, 622), (652, 640), (600, 650), (544, 662), (506, 688), (512, 722),
           (470, 692), (428, 700), (378, 690), (312, 700), (322, 662), (390, 642),
           (452, 620), (506, 600), (556, 562), (572, 546), (578, 508), (596, 546),
           (610, 528), (642, 518), (664, 470), (680, 400), (690, 340)]
    HOK = [(762, 118), (830, 148), (862, 206), (820, 236), (772, 226), (726, 262),
           (692, 226), (716, 174)]
    SHI = [(396, 718), (470, 714), (494, 744), (430, 764), (376, 750)]
    KYU = [(286, 714), (322, 730), (330, 780), (306, 830), (260, 844), (236, 796),
           (250, 744)]
    sx, sy = AH * 1.26 / 1000.0, AH * 1.26 / 1000.0
    ox, oy = AW * 0.5 - 560 * sx, AH * 0.50 - 480 * sy

    def T(pts):
        return [(ox + x * sx, oy + y * sy) for x, y in pts]
    for poly in (HON, HOK, SHI, KYU):
        p = T(poly)
        d.polygon(p, fill=(46, 62, 82, 255))
        d.line(p + [p[0]], fill=(140, 215, 230, 190), width=5)
    glow = img.filter(ImageFilter.GaussianBlur(6))
    img = ImageChops.screen(img, ImageEnhance.Brightness(glow).enhance(0.25))
    d = ImageDraw.Draw(img, "RGBA")
    pins = [("黒瀬病院", "広島", (372, 676), (-180, -120)),
            ("旧相武病院", "東京", (694, 612), (170, 100)),
            ("旧野木病院", "栃木", (706, 570), (185, -40)),
            ("小美玉小川脳病院", "茨城", (740, 552), (150, -140)),
            ("姫川病院", "新潟", (612, 528), (-330, -110))]
    f1 = B.font(52, "black")
    f2 = B.font(36, "bold")
    for name, pref, (px, py), (lx, ly) in pins:
        x, y = ox + px * sx, oy + py * sy
        for r, a in [(40, 90), (24, 160)]:
            d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 74, 84, a), width=4)
        d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=(255, 64, 74, 255))
        tx, ty = x + lx * 1.25, y + ly * 1.25
        d.line([x, y, tx + (54 if lx < 0 else -8), ty + 20], fill=(255, 90, 96, 150), width=3)
        d.text((tx, ty), name, font=f1, fill=(238, 243, 248, 250),
               anchor="lm" if lx > 0 else "rm")
        d.text((tx, ty + 52), pref, font=f2, fill=(255, 116, 122, 220),
               anchor="lm" if lx > 0 else "rm")
    img = B.add_glow(img, AW * 0.5, AH * 0.5, AW * 0.5, (30, 60, 80), 0.4)
    return finish(img, lift=(4, 6, 12), gain=(215, 226, 240), sat=0.95, vig=0.5,
                  seed=seed, dirt_amt=0.02)


# ================================================================ rank boards
def _rank_board(num, seed, red=False):
    img = texture_board(seed, base=(12, 13, 17),
                        smear=dict(y=0.55, color=(70, 12, 16) if red else (40, 14, 18)))
    img = ghost_number(img, num, 0.79, 0.50, 1450, 30 if red else 24)
    img = kanji_watermark(img, "霊", 0.16, 0.70, 780, 12)
    return finish(img, lift=(6, 7, 10), gain=(210, 216, 228), sat=0.85, vig=0.6, seed=seed)


def rank_board_5(seed=50):
    return _rank_board("05", seed)


def rank_board_4(seed=51):
    return _rank_board("04", seed)


def rank_board_3(seed=52):
    return _rank_board("03", seed)


def rank_board_2(seed=53):
    return _rank_board("02", seed)


def rank_board_1(seed=54):
    return _rank_board("01", seed, red=True)


# ================================================================ #5 黒瀬 (day suburb)
def _overcast(seed):
    img = B.new_canvas((150, 158, 168), (108, 118, 128))
    n = B.vnoise(AW // 3, AH // 3, 5, seed, 4)
    n = Image.fromarray((n * 50).astype(np.uint8)).resize((AW, AH)).filter(
        ImageFilter.GaussianBlur(10))
    return ImageChops.subtract(img, Image.merge("RGB", (n, n, n)))


def kurose_exterior_day(seed=60):
    img = _overcast(seed)
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.72, AW, AH], fill=(70, 74, 78))  # road
    # neighbor houses
    for hx, hw_, hh in [(AW * 0.02, 300, 260), (AW * 0.82, 330, 280)]:
        B.draw_house(d, hx, AH * 0.72, hw_, hh, dict(house=(52, 56, 62)), lit=False, seed=seed)
    pal = dict(wall=(96, 100, 102))
    B.draw_building(img, AW * 0.26, AH * 0.26, AW * 0.74, AH * 0.72, pal, seed,
                    floors=4, bays=9, broken_p=0.34, sign="正仁クリニック")
    d = ImageDraw.Draw(img)
    # overgrowth in front
    for i, tx in enumerate(np.linspace(AW * 0.24, AW * 0.76, 9)):
        B.tree_blob(img, tx, AH * 0.72, 66, (34, 44, 32), seed + 9 + i)
    B.draw_pole(d, AW * 0.135, AH * 0.86, AH * 0.56)
    B.wires(d, AW * 0.135, AW * 1.02, AH * 0.34, sag=36)
    img = B.fog_bands(img, seed, 0.12, (140, 148, 154), y0=0.6)
    return finish(img, lift=(14, 16, 18), gain=(225, 230, 235), sat=0.66, vig=0.46,
                  seed=seed)


def kurose_street_wide(seed=61):
    img = _overcast(seed + 1)
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.70, AW, AH], fill=(66, 70, 74))
    d.polygon([(AW * 0.42, AH), (AW * 0.5, AH * 0.70), (AW * 0.56, AH * 0.70), (AW * 0.72, AH)],
              fill=(88, 92, 96))  # street receding
    for i, (hx, hw_, hh) in enumerate([(-40, 340, 250), (AW * 0.17, 300, 230),
                                       (AW * 0.72, 320, 240), (AW * 0.88, 300, 265)]):
        B.draw_house(d, hx, AH * 0.70, hw_, hh, dict(house=(58, 62, 68)), lit=False,
                     seed=seed + i)
    pal = dict(wall=(84, 88, 90))
    B.draw_building(img, AW * 0.33, AH * 0.20, AW * 0.70, AH * 0.70, pal, seed + 2,
                    floors=5, bays=8, broken_p=0.3)
    d = ImageDraw.Draw(img)
    B.draw_pole(d, AW * 0.25, AH * 0.84, AH * 0.6)
    B.draw_pole(d, AW * 0.79, AH * 0.82, AH * 0.55)
    B.wires(d, AW * 0.25, AW * 0.79, AH * 0.28, sag=44)
    img = B.fog_bands(img, seed, 0.10, (150, 155, 160), y0=0.62)
    img = kanji_watermark(img, "異", 0.87, 0.32, 620, 10)
    return finish(img, lift=(13, 15, 17), gain=(222, 227, 232), sat=0.64, vig=0.5,
                  seed=seed)


def kurose_fence(seed=62):
    img = _overcast(seed + 2)
    d = ImageDraw.Draw(img, "RGBA")
    pal = dict(wall=(88, 92, 94))
    B.draw_building(img, AW * 0.12, AH * 0.12, AW * 0.98, AH * 0.78, pal, seed,
                    floors=4, bays=10, broken_p=0.4)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, AH * 0.78, AW, AH], fill=(52, 58, 52))
    for i, tx in enumerate(np.linspace(0, AW, 13)):
        B.tree_blob(img, tx, AH * 0.80, 88, (30, 40, 28), seed + 20 + i)
    # chain-link fence in front
    d = ImageDraw.Draw(img, "RGBA")
    fy0, fy1 = AH * 0.42, AH * 0.98
    for x in range(-60, AW + 60, 52):
        d.line([x, fy0 + 40, x + 260, fy1], fill=(150, 158, 164, 90), width=3)
        d.line([x + 260, fy0 + 40, x, fy1], fill=(150, 158, 164, 90), width=3)
    for px in np.linspace(AW * 0.06, AW * 0.94, 5):
        d.line([px, fy0, px, fy1], fill=(96, 102, 108, 220), width=10)
    d.line([0, fy0 + 8, AW, fy0 - 6], fill=(110, 116, 122, 230), width=8)
    return finish(img, lift=(12, 14, 16), gain=(218, 224, 230), sat=0.6, vig=0.55,
                  seed=seed)


def ff_window_night(seed=63):
    # IR-lit exterior wall, one dark window; NV camcorder look
    img = Image.new("RGB", (AW, AH), (96, 102, 96))
    n = B.vnoise(AW // 2, AH // 2, 16, seed, 5)
    n = Image.fromarray((n * 60).astype(np.uint8)).resize((AW, AH))
    img = ImageChops.subtract(img, Image.merge("RGB", (n, n, n)))
    st = B.streaks(AW, AH, seed + 2, 14, 5)
    img = Image.composite(Image.new("RGB", (AW, AH), (40, 44, 40)), img,
                          Image.fromarray((st * 120).astype(np.uint8)))
    d = ImageDraw.Draw(img)
    # window (IR falls off inside -> near black interior)
    wx0, wy0, wx1, wy1 = AW * 0.32, AH * 0.16, AW * 0.84, AH * 0.78
    d.rectangle([wx0 - 34, wy0 - 34, wx1 + 34, wy1 + 34], fill=(150, 156, 148))
    d.rectangle([wx0, wy0, wx1, wy1], fill=(16, 19, 17))
    # faint interior: far wall hint + door gap
    d.rectangle([wx0 + 60, wy0 + 90, wx1 - 60, wy1 - 40], fill=(26, 30, 27))
    d.rectangle([wx0 + (wx1 - wx0) * 0.62, wy0 + 60, wx0 + (wx1 - wx0) * 0.78, wy1 - 40],
                fill=(9, 11, 10))
    d.line([(wx0 + wx1) / 2, wy0, (wx0 + wx1) / 2, wy1], fill=(120, 126, 118), width=16)
    d.line([wx0, (wy0 + wy1) * 0.5, wx1, (wy0 + wy1) * 0.5], fill=(120, 126, 118), width=16)
    # crack in lower-left pane
    rng = np.random.default_rng(seed)
    ax, ay = AW * 0.40, AH * 0.60
    for _ in range(8):
        bx = ax + rng.uniform(-60, 160)
        by = ay + rng.uniform(-120, 90)
        d.line([ax, ay, bx, by], fill=(168, 175, 166), width=4)
        ax, ay = bx, by
    # IR hotspot center falloff
    img = B.add_glow(img, AW * 0.5, AH * 0.47, AW * 0.42, (60, 66, 58), 0.55)
    img = nv_process(img, seed)
    return B.vignette(ImageEnhance.Contrast(img).enhance(1.05), 0.5)


def kurose_lowangle(seed=64):
    img = B.new_canvas((16, 20, 34), (40, 48, 64))
    d = ImageDraw.Draw(img)
    # low-angle building trapezoid
    d.polygon([(AW * 0.12, AH), (AW * 0.30, AH * 0.10), (AW * 0.72, AH * 0.10),
               (AW * 0.92, AH)], fill=(30, 35, 44))
    rng = np.random.default_rng(seed)
    for fy in np.linspace(AH * 0.16, AH * 0.9, 7):
        t = (fy - AH * 0.10) / (AH * 0.9)
        x0 = AW * (0.30 - 0.17 * t) + AW * 0.02
        x1 = AW * (0.72 + 0.19 * t) - AW * 0.02
        for wx in np.linspace(x0, x1, 8):
            ww = (x1 - x0) / 8 * 0.5
            col = (12, 15, 20) if rng.random() > 0.2 else (7, 8, 11)
            d.rectangle([wx, fy, wx + ww, fy + AH * 0.055 * (0.5 + t)], fill=col)
    d.rectangle([AW * 0.30, AH * 0.10 - 26, AW * 0.72, AH * 0.10], fill=(24, 28, 36))
    img = B.fog_bands(img, seed, 0.4, (54, 66, 84), y0=0.55)
    img = B.add_glow(img, AW * 0.5, AH * 0.02, AW * 0.4, (60, 74, 100), 0.5)
    return finish(img, lift=(7, 9, 16), gain=(200, 212, 232), sat=0.72, vig=0.6,
                  halo=(185, 30, 0.4), seed=seed)


def kurose_dusk(seed=65):
    img = B.new_canvas((40, 34, 58), (16, 14, 22))
    # dusk horizon band
    band = B.grad_v(AW, int(AH * 0.5), (176, 106, 76), (40, 34, 58))
    img.paste(band.transpose(Image.FLIP_TOP_BOTTOM), (0, int(AH * 0.12)))
    img = img.filter(ImageFilter.GaussianBlur(60))
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.74, AW, AH], fill=(12, 11, 15))
    for i, (hx, hw_, hh) in enumerate([(AW * 0.0, 330, 250), (AW * 0.16, 300, 225),
                                       (AW * 0.75, 320, 235), (AW * 0.90, 330, 260)]):
        B.draw_house(d, hx, AH * 0.74, hw_, hh, dict(house=(14, 13, 18)), lit=True,
                     seed=seed + i)
    pal = dict(wall=(22, 22, 30))
    B.draw_building(img, AW * 0.33, AH * 0.26, AW * 0.71, AH * 0.74, pal, seed,
                    floors=4, bays=8, broken_p=0.32, glass=(10, 10, 14))
    d = ImageDraw.Draw(img)
    B.draw_pole(d, AW * 0.24, AH * 0.87, AH * 0.58)
    B.draw_pole(d, AW * 0.80, AH * 0.86, AH * 0.55)
    B.wires(d, AW * 0.24, AW * 0.80, AH * 0.30, sag=40)
    img = B.fog_bands(img, seed, 0.2, (50, 44, 62), y0=0.6)
    return finish(img, lift=(9, 8, 14), gain=(225, 205, 215), sat=0.9, vig=0.55,
                  halo=(180, 34, 0.55), seed=seed)


def detail_wall_crack(seed=66):
    img = Image.new("RGB", (AW, AH), (118, 120, 118))
    n = B.vnoise(AW // 2, AH // 2, 24, seed, 4)
    n = Image.fromarray((n * 34).astype(np.uint8)).resize((AW, AH))
    img = ImageChops.subtract(img, Image.merge("RGB", (n, n, n)))
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    # a few peeled patches exposing dark plaster
    for _ in range(9):
        x, y = rng.uniform(0, AW), rng.uniform(0, AH)
        r = rng.uniform(60, 200)
        pts = [(x + np.cos(a) * r * rng.uniform(0.5, 1.2),
                y + np.sin(a) * r * rng.uniform(0.4, 1.0))
               for a in np.linspace(0, 6.28, 9)]
        d.polygon(pts, fill=(64, 60, 54, 200))
        d.polygon([(px + 8, py + 8) for px, py in pts[:5]], fill=(140, 138, 130, 90))
    # one strong crack diagonal with branches
    x, y = AW * 0.12, AH * 0.22
    main = [(x, y)]
    for _ in range(16):
        x += rng.uniform(60, 170)
        y += rng.uniform(-30, 110)
        main.append((x, y))
    for i in range(len(main) - 1):
        wdt = int(14 - 10 * i / len(main))
        d.line([main[i], main[i + 1]], fill=(12, 13, 14, 255), width=max(3, wdt))
        if rng.random() < 0.5:
            bx, by = main[i]
            d.line([bx, by, bx + rng.uniform(-40, 120), by + rng.uniform(40, 170)],
                   fill=(20, 21, 22, 230), width=3)
    # grime streaks + corner shadow
    st = B.streaks(AW, AH, seed + 4, 12, 6)
    img = Image.composite(Image.new("RGB", img.size, (58, 58, 54)), img,
                          Image.fromarray((st * 110).astype(np.uint8)))
    img = B.add_glow(img, AW * 0.70, AH * 0.26, AW * 0.4, (96, 100, 98), 0.5)
    return finish(img, lift=(10, 11, 13), gain=(210, 214, 218), sat=0.5, vig=0.58,
                  seed=seed)


def detail_window_broken(seed=67):
    img = B.new_canvas((30, 34, 40), (16, 18, 22))
    d = ImageDraw.Draw(img)
    wx0, wy0, wx1, wy1 = AW * 0.18, AH * 0.12, AW * 0.82, AH * 0.88
    d.rectangle([wx0 - 44, wy0 - 44, wx1 + 44, wy1 + 44], fill=(70, 72, 70))
    d.rectangle([wx0, wy0, wx1, wy1], fill=(7, 8, 10))
    rng = np.random.default_rng(seed)
    cx, cy = AW * 0.55, AH * 0.44
    for a in np.linspace(0, 6.28, 14):
        L = rng.uniform(120, 520)
        d.line([cx, cy, cx + np.cos(a) * L, cy + np.sin(a) * L],
               fill=(150, 158, 162), width=3)
    for a in np.linspace(0, 6.28, 9):
        r = rng.uniform(90, 260)
        d.arc([cx - r, cy - r, cx + r, cy + r], a * 57, a * 57 + 40,
              fill=(140, 148, 152), width=3)
    # glass shards on sill
    for _ in range(14):
        x = rng.uniform(wx0, wx1)
        y = rng.uniform(wy1 - 30, wy1 + 30)
        d.polygon([(x, y), (x + rng.uniform(8, 40), y - rng.uniform(6, 30)),
                   (x + rng.uniform(14, 50), y + 6)], fill=(120, 130, 136))
    img = B.add_glow(img, cx, cy, 260, (70, 84, 92), 0.5)
    return finish(img, lift=(6, 8, 11), gain=(205, 214, 222), sat=0.55, vig=0.62,
                  halo=(170, 26, 0.4), seed=seed)


# ================================================================ #4 相武 (night blue)
def sobu_exterior(seed=70):
    img = B.new_canvas((10, 14, 26), (22, 30, 44))
    for i, tx in enumerate(np.linspace(-60, AW + 60, 17)):
        B.tree_blob(img, tx, AH * 0.55 + (i % 4) * 22, 130, (8, 12, 14), seed + i)
    pal = dict(wall=(34, 40, 52))
    B.draw_building(img, AW * 0.18, AH * 0.22, AW * 0.60, AH * 0.80, pal, seed,
                    floors=5, bays=7, broken_p=0.3)
    B.draw_building(img, AW * 0.60, AH * 0.34, AW * 0.86, AH * 0.80, dict(wall=(28, 34, 44)),
                    seed + 1, floors=4, bays=4, broken_p=0.3, roofbox=False)
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.80, AW, AH], fill=(10, 13, 18))
    img = B.fog_bands(img, seed, 0.5, (52, 66, 88), y0=0.45)
    img = kanji_watermark(img, "視", 0.88, 0.28, 560, 11)
    return finish(img, lift=(6, 9, 18), gain=(198, 210, 234), sat=0.75, vig=0.58,
                  seed=seed)


def sobu_corridor(seed=71):
    pal = dict(floor=(22, 27, 34), ceil=(26, 32, 40), wallL=(38, 46, 58),
               wallR=(32, 40, 52), door=(46, 52, 62), light_on=(130, 148, 168),
               light_off=(22, 26, 32), glow=(110, 130, 158), refl=(46, 58, 74),
               flicker_idx=2)
    img, _ = _corridor_base(pal, seed, doors=6, end="black", lights=5, debris=0.8)
    img = B.fog_bands(img, seed, 0.4, (48, 62, 86), y0=0.5)
    return finish(img, lift=(5, 8, 16), gain=(192, 205, 230), sat=0.7, vig=0.62,
                  seed=seed)


def eye_room(seed=72):
    pal = dict(wallL=(44, 43, 46), wallR=(34, 33, 37), ceil=(26, 26, 30),
               floor=(38, 36, 38), back=(88, 82, 72))
    img = B.new_canvas((16, 16, 19), (28, 28, 32))
    img, (bx0, by0, bx1, by1) = B.room_box(img, pal, seed, back=0.66)
    d = ImageDraw.Draw(img, "RGBA")
    # peeling wall texture on back
    rng = np.random.default_rng(seed)
    for _ in range(40):
        x = rng.uniform(bx0, bx1); y = rng.uniform(by0, by1)
        r = rng.uniform(16, 70)
        d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6],
                  fill=(70, 64, 56, rng.integers(30, 80)))
    # the giant eye
    ecx, ecy = (bx0 + bx1) / 2, (by0 + by1) / 2 - 20
    ew, eh = (bx1 - bx0) * 0.36, (by1 - by0) * 0.30
    d.polygon([(ecx - ew, ecy), (ecx, ecy - eh), (ecx + ew, ecy), (ecx, ecy + eh)],
              fill=(188, 178, 160, 255))
    d.ellipse([ecx - eh * 0.85, ecy - eh * 0.85, ecx + eh * 0.85, ecy + eh * 0.85],
              fill=(120, 86, 60, 255))
    d.ellipse([ecx - eh * 0.8, ecy - eh * 0.8, ecx + eh * 0.8, ecy + eh * 0.8],
              fill=(150, 104, 66, 255))
    d.ellipse([ecx - eh * 0.38, ecy - eh * 0.38, ecx + eh * 0.38, ecy + eh * 0.38],
              fill=(12, 8, 8, 255))
    d.ellipse([ecx - eh * 0.13, ecy - eh * 0.52, ecx + eh * 0.10, ecy - eh * 0.28],
              fill=(210, 200, 188, 220))
    for _ in range(14):  # veins
        a = rng.uniform(0, 6.28)
        x0v = ecx + np.cos(a) * ew * 0.55
        y0v = ecy + np.sin(a) * eh * 0.75
        d.line([x0v, y0v, x0v + rng.uniform(-60, 60), y0v + rng.uniform(-30, 30)],
               fill=(150, 60, 56, 160), width=3)
    # dripping paint under eye
    for _ in range(8):
        x = rng.uniform(ecx - ew * 0.7, ecx + ew * 0.7)
        d.line([x, ecy + eh * 0.9, x, ecy + eh * 0.9 + rng.uniform(30, 170)],
               fill=(96, 60, 44, 200), width=int(rng.uniform(3, 8)))
    # flashlight cone from lower-left lighting the whole wall
    img = B.light_cone(img, (AW * 0.04, AH * 1.02), (bx0 - 80, by0 - 120),
                       (bx1 + 120, by1 - 60), (168, 156, 130), alpha=105, blur=80)
    img = B.add_glow(img, ecx, ecy, ew * 0.8, (128, 102, 74), 0.5)
    return finish(img, lift=(6, 6, 9), gain=(222, 214, 210), sat=0.72, vig=0.58,
                  seed=seed)


def eye_closeup(seed=73):
    img = B.new_canvas((30, 27, 24), (46, 42, 38))
    n = B.vnoise(AW // 2, AH // 2, 16, seed, 5)
    n = Image.fromarray((n * 56).astype(np.uint8)).resize((AW, AH))
    img = ImageChops.subtract(img, Image.merge("RGB", (n, n, n)))
    d = ImageDraw.Draw(img, "RGBA")
    ecx, ecy = AW * 0.5, AH * 0.47
    ew, eh = AW * 0.34, AH * 0.30
    d.polygon([(ecx - ew, ecy), (ecx - ew * 0.3, ecy - eh), (ecx + ew * 0.3, ecy - eh),
               (ecx + ew, ecy), (ecx + ew * 0.3, ecy + eh), (ecx - ew * 0.3, ecy + eh)],
              fill=(196, 186, 168, 255))
    rng = np.random.default_rng(seed)
    for _ in range(22):
        a = rng.uniform(0, 6.28)
        r0 = eh * rng.uniform(0.55, 0.95)
        x0v = ecx + np.cos(a) * ew * 0.75
        y0v = ecy + np.sin(a) * eh * 0.75
        d.line([x0v, y0v, ecx + np.cos(a) * ew * 0.4, ecy + np.sin(a) * eh * 0.4],
               fill=(160, 62, 58, 130), width=3)
    d.ellipse([ecx - eh * 0.92, ecy - eh * 0.92, ecx + eh * 0.92, ecy + eh * 0.92],
              fill=(118, 82, 54, 255))
    for a in np.linspace(0, 6.28, 40):  # iris striations
        d.line([ecx + np.cos(a) * eh * 0.4, ecy + np.sin(a) * eh * 0.4,
                ecx + np.cos(a) * eh * 0.88, ecy + np.sin(a) * eh * 0.88],
               fill=(88, 58, 40, 120), width=4)
    img = B.add_glow(img, ecx, ecy, ew, (110, 88, 62), 0.45)
    img = kanji_watermark(img, "呪", 0.12, 0.78, 520, 14)
    return finish(img, lift=(8, 7, 8), gain=(215, 206, 200), sat=0.85, vig=0.66,
                  seed=seed)


def sobu_fence(seed=74):
    img = B.new_canvas((12, 16, 28), (24, 32, 46))
    pal = dict(wall=(30, 36, 48))
    B.draw_building(img, AW * 0.10, AH * 0.18, AW * 0.94, AH * 0.72, pal, seed,
                    floors=4, bays=10, broken_p=0.32)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, AH * 0.72, AW, AH], fill=(11, 14, 20))
    # tall fence + barbed wire
    fy0 = AH * 0.34
    for x in range(-40, AW + 40, 46):
        d.line([x, fy0 + 30, x + 220, AH], fill=(120, 130, 142, 80), width=3)
        d.line([x + 220, fy0 + 30, x, AH], fill=(120, 130, 142, 80), width=3)
    for px in np.linspace(AW * 0.04, AW * 0.96, 6):
        d.line([px, fy0, px, AH], fill=(70, 78, 90, 230), width=11)
    d.line([0, fy0 + 4, AW, fy0 - 4], fill=(88, 96, 108, 240), width=7)
    xs = np.linspace(0, AW, 90)
    d.line([(x, fy0 - 24 + 10 * np.sin(i)) for i, x in enumerate(xs)],
           fill=(96, 104, 116, 230), width=4)
    rng = np.random.default_rng(seed)
    for x in xs[::3]:
        d.line([x - 8, fy0 - 30, x + 8, fy0 - 14], fill=(110, 118, 130, 220), width=3)
        d.line([x + 8, fy0 - 30, x - 8, fy0 - 14], fill=(110, 118, 130, 220), width=3)
    # warning sign
    sx, sy = AW * 0.70, AH * 0.52
    d.rectangle([sx, sy, sx + 420, sy + 250], fill=(196, 190, 178, 255),
                outline=(150, 60, 50, 255), width=8)
    f = B.font(96, "black")
    d.text((sx + 210, sy + 92), "立入禁止", font=f, anchor="mm", fill=(168, 40, 38, 255))
    f2 = B.font(40, "bold")
    d.text((sx + 210, sy + 190), "管理者以外の立入を禁ず", font=f2, anchor="mm",
           fill=(40, 40, 44, 255))
    st = B.streaks(420, 250, seed, 14, 3)
    reg = img.crop((int(sx), int(sy), int(sx) + 420, int(sy) + 250))
    img.paste(Image.composite(Image.new("RGB", (420, 250), (60, 50, 44)), reg,
                              Image.fromarray((st * 120).astype(np.uint8))), (int(sx), int(sy)))
    img = B.fog_bands(img, seed, 0.4, (46, 60, 84), y0=0.5)
    return finish(img, lift=(6, 9, 17), gain=(200, 212, 234), sat=0.72, vig=0.6,
                  seed=seed)


def sobu_lit_window(seed=75):
    img = B.new_canvas((7, 9, 16), (14, 18, 28))
    pal = dict(wall=(24, 28, 38))
    B.draw_building(img, AW * 0.06, AH * 0.10, AW * 0.98, AH * 0.86, pal, seed,
                    floors=5, bays=11, broken_p=0.3, lit={(2, 6)}, glass=(12, 15, 21))
    # extra glow on the lit one
    gw = (AW * 0.92 - AW * 0.06 * 2)
    img = B.add_glow(img, AW * 0.655, AH * 0.512, 190, (255, 214, 130), 0.9)
    img = B.fog_bands(img, seed, 0.35, (40, 52, 74), y0=0.55)
    return finish(img, lift=(5, 7, 14), gain=(195, 206, 230), sat=0.8, vig=0.66,
                  halo=(150, 40, 0.8), seed=seed)


def maze_corridor(seed=76):
    pal = dict(floor=(20, 25, 32), ceil=(24, 30, 38), wallL=(36, 44, 56),
               wallR=(30, 38, 50), door=(44, 50, 60), light_on=None,
               light_off=(20, 24, 30), refl=(40, 52, 68))
    img, proj = _corridor_base(pal, seed, doors=8, end="black", lights=6, debris=0.7,
                               vp=(0.5, 0.5), k=0.7)
    img = B.fog_bands(img, seed, 0.5, (44, 58, 82), y0=0.42)
    img = kanji_watermark(img, "迷", 0.85, 0.25, 600, 12)
    return finish(img, lift=(4, 7, 15), gain=(188, 200, 226), sat=0.68, vig=0.68,
                  seed=seed)


# ================================================================ #3 野木 (green decay)
def nogi_exterior(seed=80):
    img = B.new_canvas((14, 20, 18), (30, 40, 34))
    for i, tx in enumerate(np.linspace(-80, AW + 80, 19)):
        B.tree_blob(img, tx, AH * 0.5 + (i % 4) * 30, 150, (8, 13, 10), seed + i)
    pal = dict(wall=(44, 50, 44))
    B.draw_building(img, AW * 0.16, AH * 0.30, AW * 0.84, AH * 0.82, pal, seed,
                    floors=3, bays=10, broken_p=0.38, sign="野木厚生クリニック")
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.82, AW, AH], fill=(14, 18, 14))
    for i, tx in enumerate(np.linspace(AW * 0.1, AW * 0.9, 7)):
        B.tree_blob(img, tx, AH * 0.86, 60, (10, 15, 10), seed + 40 + i)
    img = B.fog_bands(img, seed, 0.45, (56, 74, 64), y0=0.5)
    return finish(img, lift=(7, 11, 9), gain=(200, 218, 204), sat=0.7, vig=0.58,
                  seed=seed)


def nogi_archival(seed=81):
    """Sepia 'archival photo' framed on dark board (1985 era)."""
    board = texture_board(seed, base=(11, 12, 14))
    ph = Image.new("RGB", (int(AW * 0.62), int(AH * 0.62)), (196, 180, 150))
    d = ImageDraw.Draw(ph)
    d.rectangle([0, int(ph.height * 0.62), ph.width, ph.height], fill=(150, 132, 104))
    pal = dict(wall=(120, 106, 84))
    B.draw_building(ph, ph.width * 0.14, ph.height * 0.22, ph.width * 0.86,
                    ph.height * 0.72, pal, seed, floors=3, bays=9, broken_p=0.0,
                    glass=(96, 88, 72))
    dd = ImageDraw.Draw(ph)
    for i, tx in enumerate(np.linspace(ph.width * 0.1, ph.width * 0.9, 5)):
        B.tree_blob(ph, tx, ph.height * 0.72, 40, (86, 76, 56), seed + i)
    n = B.vnoise(ph.width // 2, ph.height // 2, 40, seed, 3)
    n = Image.fromarray((n * 40).astype(np.uint8)).resize(ph.size)
    ph = ImageChops.subtract(ph, Image.merge("RGB", (n, n, n)))
    ph = B.vignette(ph, 0.35)
    frame = Image.new("RGB", (ph.width + 60, ph.height + 60), (222, 216, 200))
    frame.paste(ph, (30, 30))
    frame = frame.rotate(-2.2, expand=True, fillcolor=(11, 12, 14))
    board.paste(frame, (int(AW * 0.20), int(AH * 0.13)))
    sh = Image.new("RGB", board.size, (0, 0, 0))
    board = Image.blend(board, sh, 0.0)
    board = kanji_watermark(board, "跡", 0.88, 0.75, 560, 12)
    return finish(board, lift=(8, 9, 11), gain=(214, 216, 220), sat=0.9, vig=0.55,
                  seed=seed)


def renovation_interior(seed=82):
    pal = dict(wallL=(52, 46, 38), wallR=(40, 36, 30), ceil=(30, 28, 24),
               floor=(44, 40, 34), back=(58, 54, 46))
    img = B.new_canvas((16, 15, 13), (26, 24, 20))
    img, (bx0, by0, bx1, by1) = B.room_box(img, pal, seed, back=0.7)
    d = ImageDraw.Draw(img, "RGBA")
    # exposed studs on half the back wall
    for x in np.linspace(bx0, (bx0 + bx1) / 2, 7):
        d.rectangle([x, by0, x + 22, by1], fill=(96, 78, 54, 255))
        d.rectangle([x + 22, by0, x + 26, by1], fill=(30, 24, 18, 255))
    # hospital wall remains right: door + tiles hint
    d.rectangle([(bx0 + bx1) / 2 + 60, by0 + (by1 - by0) * 0.25,
                 (bx0 + bx1) / 2 + 210, by1], fill=(70, 74, 70, 255))
    d.rectangle([(bx0 + bx1) / 2 + 60, by0 + (by1 - by0) * 0.25,
                 (bx0 + bx1) / 2 + 210, by1], outline=(40, 42, 40, 255), width=6)
    # ladder silhouette
    lx = bx0 + (bx1 - bx0) * 0.78
    d.line([lx, by1 + 60, lx + 120, by0 - 40], fill=(20, 18, 16, 255), width=14)
    d.line([lx + 60, by1 + 60, lx + 180, by0 - 40], fill=(20, 18, 16, 255), width=14)
    for t in np.linspace(0.12, 0.88, 7):
        x0v = lx + 120 * t; y0v = (by1 + 60) + (by0 - 40 - by1 - 60) * t
        d.line([x0v, y0v, x0v + 62, y0v], fill=(20, 18, 16, 255), width=10)
    # plastic sheet
    d.polygon([(bx0 - 100, by1 + 200), (bx0 + 250, by0 + 60), (bx0 + 420, by1 + 220)],
              fill=(120, 124, 128, 60))
    img = B.fog_bands(img, seed, 0.25, (60, 58, 48), y0=0.55)
    return finish(img, lift=(9, 8, 7), gain=(212, 206, 194), sat=0.72, vig=0.6,
                  seed=seed)


def nogi_corridor_glimpse(seed=83):
    pal = dict(floor=(24, 28, 24), ceil=(28, 33, 28), wallL=(42, 50, 42),
               wallR=(34, 42, 34), door=(48, 54, 46), light_on=(150, 165, 140),
               light_off=(24, 28, 24), glow=(130, 150, 120), refl=(50, 62, 50),
               flicker_idx=1)
    img, _ = _corridor_base(pal, seed, doors=5, end="black", lights=4, debris=0.9)
    img = B.fog_bands(img, seed, 0.4, (54, 70, 58), y0=0.48)
    return finish(img, lift=(5, 9, 6), gain=(190, 210, 192), sat=0.66, vig=0.66,
                  seed=seed)


def white_ritual(seed=84):
    pal = dict(wallL=(52, 54, 46), wallR=(42, 44, 38), ceil=(30, 32, 27),
               floor=(46, 46, 39), back=(66, 68, 58))
    img = B.new_canvas((16, 17, 14), (28, 29, 25))
    img, (bx0, by0, bx1, by1) = B.room_box(img, seed=seed, pal=pal, back=0.78)
    d = ImageDraw.Draw(img, "RGBA")
    # tall broken windows on back wall, moonlight slivers
    for i, wx in enumerate(np.linspace(bx0 + (bx1 - bx0) * 0.10,
                                       bx0 + (bx1 - bx0) * 0.78, 4)):
        ww_ = (bx1 - bx0) * 0.10
        d.rectangle([wx, by0 + (by1 - by0) * 0.12, wx + ww_, by0 + (by1 - by0) * 0.62],
                    fill=(108, 122, 116, 255))
        d.line([wx + ww_ / 2, by0 + (by1 - by0) * 0.12, wx + ww_ / 2,
                by0 + (by1 - by0) * 0.62], fill=(36, 40, 36, 255), width=8)
        # moon spill on floor
        d.polygon([(wx - 30, by1 + 130), (wx + ww_ + 60, by1 + 130),
                   (wx + ww_ * 0.8, by0 + (by1 - by0) * 0.62),
                   (wx + ww_ * 0.2, by0 + (by1 - by0) * 0.62)],
                  fill=(96, 108, 102, 60))
    # candle ring on floor
    rng = np.random.default_rng(seed)
    for cx_ in np.linspace(AW * 0.22, AW * 0.78, 7):
        cy_ = AH * 0.80 + 26 * np.sin(cx_ * 0.01)
        img = B.add_glow(img, cx_, cy_ - 10, 110, (216, 148, 62), 0.6, power=2.2)
        d = ImageDraw.Draw(img, "RGBA")
        d.line([cx_, cy_ - 26, cx_, cy_], fill=(232, 226, 210, 255), width=8)
        d.ellipse([cx_ - 5, cy_ - 40, cx_ + 5, cy_ - 24], fill=(255, 226, 160, 255))
    img = B.fog_bands(img, seed, 0.3, (52, 58, 48), y0=0.55)
    img = kanji_watermark(img, "儀", 0.85, 0.26, 620, 15)
    return finish(img, lift=(8, 8, 6), gain=(212, 212, 196), sat=0.85, vig=0.6,
                  seed=seed)


def ff_forest(seed=85):
    # IR beam into foggy woods: bright fog bg, dark trunk silhouettes
    img = Image.new("RGB", (AW, AH), (88, 96, 88))
    n = B.vnoise(AW // 2, AH // 2, 6, seed, 5)
    n = Image.fromarray((n * 70).astype(np.uint8)).resize((AW, AH)).filter(
        ImageFilter.GaussianBlur(8))
    img = ImageChops.subtract(img, Image.merge("RGB", (n, n, n)))
    img = B.add_glow(img, AW * 0.5, AH * 0.5, AW * 0.45, (90, 98, 86), 0.7)
    d = ImageDraw.Draw(img)
    # building shadow far
    d.rectangle([AW * 0.42, AH * 0.28, AW * 0.74, AH * 0.66], fill=(52, 58, 52))
    rng = np.random.default_rng(seed)
    # dark trunks over
    for i in range(17):
        x = rng.uniform(-40, AW)
        w_ = rng.uniform(26, 110)
        depth = rng.uniform(0, 1)
        col = tuple(int(c * (0.12 + 0.5 * depth)) for c in (60, 66, 58))
        d.rectangle([x, 0, x + w_, AH], fill=col)
        if rng.random() < 0.6:
            d.line([x + w_ / 2, AH * rng.uniform(0.1, 0.3),
                    x + w_ / 2 + rng.uniform(-260, 260), AH * rng.uniform(0.0, 0.2)],
                   fill=col, width=int(w_ * 0.3))
    img = nv_process(img, seed)
    return B.vignette(ImageEnhance.Contrast(img).enhance(1.05), 0.5)


def graffiti_corridor(seed=86):
    pal = dict(floor=(44, 47, 41), ceil=(50, 54, 47), wallL=(76, 82, 70),
               wallR=(64, 70, 59), door=(80, 84, 72), light_on=(170, 185, 160),
               light_off=(40, 44, 38), glow=(150, 165, 135), refl=(84, 92, 78),
               flicker_idx=2)
    img, proj = _corridor_base(pal, seed, doors=4, end="window", lights=4, debris=1.0)
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    # graffiti scrawls on left wall
    for gi in range(7):
        z = rng.uniform(0.8, 6.5)
        X = -1
        x, y = proj(z, X, rng.uniform(-0.3, 0.45))
        s = 240 * 0.9 / (0.9 + z)
        col = [(205, 70, 70), (85, 175, 195), (215, 190, 70), (185, 185, 185)][gi % 4]
        pts = [(x + np.cos(a) * s * rng.uniform(0.4, 1.1) * 1.8,
                y + np.sin(a) * s * rng.uniform(0.2, 0.5))
               for a in np.linspace(0, 6.28, 7)]
        d.line(pts, fill=(*col, 235), width=int(max(6, s * 0.16)),
               joint="curve")
    img = B.fog_bands(img, seed, 0.3, (58, 66, 54), y0=0.5)
    return finish(img, lift=(8, 10, 8), gain=(205, 214, 200), sat=0.75, vig=0.6,
                  seed=seed)


def dark_field(seed=87):
    img = B.new_canvas((6, 8, 7), (14, 17, 14))
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.62, AW, AH], fill=(10, 12, 10))
    for i, tx in enumerate(np.linspace(-60, AW + 60, 13)):
        B.tree_blob(img, tx, AH * 0.55 + (i % 3) * 24, 120, (5, 7, 5), seed + i)
    d = ImageDraw.Draw(img)
    d.rectangle([AW * 0.30, AH * 0.34, AW * 0.72, AH * 0.64], fill=(16, 19, 16))
    img = B.fog_bands(img, seed, 0.5, (36, 44, 38), y0=0.5)
    img = B.add_glow(img, AW * 0.5, AH * 0.66, AW * 0.4, (40, 50, 42), 0.4)
    return finish(img, lift=(4, 6, 5), gain=(175, 190, 178), sat=0.6, vig=0.7,
                  seed=seed)


def renovation_split(seed=88):
    """Split comparison: hospital era | abandoned mid-renovation."""
    img = Image.new("RGB", (AW, AH))
    left = flashback_corridor(seed + 1).resize((AW // 2, AH))
    pal = dict(floor=(26, 28, 26), ceil=(30, 33, 30), wallL=(46, 50, 44),
               wallR=(38, 42, 36), door=(50, 54, 46), light_on=None,
               light_off=(26, 28, 26), refl=(52, 60, 52))
    rimg = B.new_canvas((10, 12, 10), (18, 20, 17))
    rimg, _ = B.corridor_geometry(rimg, pal, seed + 2, doors=4, end="black", lights=3,
                                  debris=1.0)
    rimg = B.fog_bands(rimg, seed, 0.35, (52, 62, 52), y0=0.5)
    rimg = finish(rimg, lift=(5, 8, 6), gain=(190, 205, 190), sat=0.62, vig=0.5,
                  seed=seed)
    right = rimg.resize((AW // 2, AH))
    img.paste(left, (0, 0))
    img.paste(right, (AW // 2, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([AW // 2 - 8, 0, AW // 2 + 8, AH], fill=(214, 208, 196))
    f = B.font(64, "black")
    d.rectangle([AW * 0.25 - 210, AH * 0.075, AW * 0.25 + 210, AH * 0.075 + 96],
                fill=(20, 16, 10))
    d.text((AW * 0.25, AH * 0.075 + 48), "病院だった頃", font=f, anchor="mm",
           fill=(238, 226, 200))
    d.rectangle([AW * 0.75 - 210, AH * 0.075, AW * 0.75 + 210, AH * 0.075 + 96],
                fill=(10, 14, 12))
    d.text((AW * 0.75, AH * 0.075 + 48), "現在", font=f, anchor="mm",
           fill=(200, 220, 208))
    return B.vignette(img, 0.4)


# ================================================================ #2 小川脳 (forest deep)
def ogawa_exterior(seed=90):
    img = B.new_canvas((8, 12, 14), (18, 26, 28))
    for i, tx in enumerate(np.linspace(-80, AW + 80, 21)):
        B.tree_blob(img, tx, AH * 0.42 + (i % 5) * 40, 160, (5, 9, 9), seed + i)
    pal = dict(wall=(30, 38, 40))
    B.draw_building(img, AW * 0.22, AH * 0.36, AW * 0.78, AH * 0.84, pal, seed,
                    floors=3, bays=8, broken_p=0.42)
    # bars over windows: horizontal strokes
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, AH * 0.84, AW, AH], fill=(8, 12, 11))
    img = B.fog_bands(img, seed, 0.55, (40, 56, 58), y0=0.42)
    img = kanji_watermark(img, "囚", 0.87, 0.26, 580, 12)
    return finish(img, lift=(5, 9, 11), gain=(188, 206, 210), sat=0.68, vig=0.62,
                  seed=seed)


def ogawa_approach(seed=91):
    img = B.new_canvas((10, 14, 15), (20, 28, 29))
    d = ImageDraw.Draw(img)
    # path receding to building
    d.polygon([(AW * 0.28, AH), (AW * 0.47, AH * 0.55), (AW * 0.53, AH * 0.55),
               (AW * 0.78, AH)], fill=(38, 43, 37))
    rng = np.random.default_rng(seed)
    for i in range(30):
        side = -1 if i % 2 == 0 else 1
        depth = rng.uniform(0, 1)
        x = AW * (0.5 + side * (0.06 + 0.5 * depth) * rng.uniform(0.8, 1.2))
        w_ = 30 + 130 * depth
        shade = 0.25 + 0.75 * depth
        d.rectangle([x, AH * (0.55 - 0.55 * depth), x + w_, AH],
                    fill=tuple(int(c * shade) for c in (36, 44, 40)))
    d.rectangle([AW * 0.42, AH * 0.36, AW * 0.60, AH * 0.58], fill=(24, 30, 30))
    for wy in np.linspace(AH * 0.40, AH * 0.54, 3):
        for wx in np.linspace(AW * 0.44, AW * 0.57, 4):
            d.rectangle([wx, wy, wx + 26, wy + 30], fill=(10, 13, 13))
    img = B.fog_bands(img, seed, 0.42, (38, 52, 54), y0=0.42)
    img = B.add_glow(img, AW * 0.5, AH * 0.45, 300, (46, 62, 62), 0.5)
    return finish(img, lift=(5, 8, 9), gain=(185, 202, 205), sat=0.66, vig=0.68,
                  seed=seed)


def isolation_room(seed=92):
    pal = dict(wallL=(56, 58, 52), wallR=(42, 44, 39), ceil=(30, 32, 28),
               floor=(48, 48, 42), back=(84, 84, 74))
    img = B.new_canvas((18, 19, 16), (30, 31, 27))
    img, (bx0, by0, bx1, by1) = B.room_box(img, pal, seed, back=0.64)
    d = ImageDraw.Draw(img, "RGBA")
    # padded wall grid on back
    cw = (bx1 - bx0) / 6
    ch = (by1 - by0) / 4
    for i in range(6):
        for j in range(4):
            x, y = bx0 + i * cw, by0 + j * ch
            d.rectangle([x + 6, y + 6, x + cw - 6, y + ch - 6],
                        outline=(34, 34, 29, 255), width=6)
            d.ellipse([x + cw / 2 - 7, y + ch / 2 - 7, x + cw / 2 + 7, y + ch / 2 + 7],
                      fill=(34, 34, 29, 255))
            d.polygon([(x + 8, y + ch - 8), (x + cw - 8, y + ch - 8),
                       (x + cw - 14, y + ch - 20), (x + 14, y + ch - 20)],
                      fill=(28, 28, 24, 90))
    # heavy door with barred hatch
    dx0 = bx0 + (bx1 - bx0) * 0.40
    dx1 = bx0 + (bx1 - bx0) * 0.60
    d.rectangle([dx0, by0 + (by1 - by0) * 0.16, dx1, by1], fill=(38, 36, 31, 255),
                outline=(18, 17, 14, 255), width=10)
    hx0, hy0 = dx0 + (dx1 - dx0) * 0.22, by0 + (by1 - by0) * 0.30
    hx1, hy1 = dx0 + (dx1 - dx0) * 0.78, by0 + (by1 - by0) * 0.46
    d.rectangle([hx0, hy0, hx1, hy1], fill=(6, 7, 6, 255))
    for bx in np.linspace(hx0 + 10, hx1 - 10, 5):
        d.line([bx, hy0, bx, hy1], fill=(72, 70, 60, 255), width=7)
    # bare hanging bulb
    lbx, lby = AW * 0.5, AH * 0.20
    d.line([lbx, 0, lbx, lby], fill=(22, 22, 19, 255), width=6)
    d.ellipse([lbx - 22, lby, lbx + 22, lby + 52], fill=(255, 238, 190, 255))
    img = B.add_glow(img, lbx, lby + 30, 360, (200, 180, 120), 0.75, power=2.0)
    d = ImageDraw.Draw(img, "RGBA")
    # single chair silhouette (dark, foreground left)
    chx, chy = bx0 + (bx1 - bx0) * 0.16, by1 + 90
    for seg in [([chx, chy, chx, chy - 170], 16), ([chx + 110, chy, chx + 110, chy - 160], 16)]:
        d.line(seg[0], fill=(12, 12, 10, 255), width=seg[1])
    d.rectangle([chx - 10, chy - 170, chx + 122, chy - 152], fill=(12, 12, 10, 255))
    d.rectangle([chx - 10, chy - 260, chx + 10, chy - 152], fill=(12, 12, 10, 255))
    img = B.fog_bands(img, seed, 0.2, (54, 58, 48), y0=0.62)
    return finish(img, lift=(7, 8, 6), gain=(214, 214, 198), sat=0.66, vig=0.6,
                  seed=seed)


def deep_corridor(seed=93):
    pal = dict(floor=(18, 22, 22), ceil=(20, 25, 25), wallL=(32, 40, 40),
               wallR=(26, 34, 34), door=(38, 44, 44), light_on=None,
               light_off=(18, 22, 22), refl=(36, 46, 46))
    img, _ = _corridor_base(pal, seed, doors=6, end="black", lights=5, debris=0.8,
                            vp=(0.5, 0.52))
    img = B.fog_bands(img, seed, 0.55, (36, 50, 52), y0=0.4)
    return finish(img, lift=(3, 6, 7), gain=(175, 194, 198), sat=0.6, vig=0.72,
                  seed=seed)


def stairs_down(seed=94):
    img = B.new_canvas((16, 18, 18), (26, 29, 28))
    d = ImageDraw.Draw(img)
    # stairwell walls
    d.polygon([(0, 0), (AW * 0.30, AH * 0.10), (AW * 0.30, AH), (0, AH)],
              fill=(40, 44, 42))
    d.polygon([(AW, 0), (AW * 0.72, AH * 0.10), (AW * 0.72, AH), (AW, AH)],
              fill=(34, 38, 36))
    # steps descending into dark
    for i in range(10):
        t = i / 10
        y0 = AH * (0.35 + 0.6 * t)
        x0 = AW * (0.30 + 0.02 * i)
        x1 = AW * (0.72 - 0.02 * i)
        shade = 1 - t * 0.9
        d.rectangle([x0, y0, x1, y0 + AH * 0.06],
                    fill=tuple(int(c * shade) for c in (66, 70, 66)))
        d.rectangle([x0, y0 + AH * 0.06, x1, y0 + AH * 0.075],
                    fill=tuple(int(c * shade * 0.5) for c in (66, 70, 66)))
    d.rectangle([AW * 0.30, AH * 0.10, AW * 0.72, AH * 0.35], fill=(6, 7, 7))
    # handrail
    d.line([AW * 0.33, AH * 0.42, AW * 0.40, AH * 0.95], fill=(20, 22, 20), width=14)
    img = B.add_glow(img, AW * 0.5, AH * 0.14, 240, (36, 44, 42), 0.5)
    img = B.fog_bands(img, seed, 0.35, (40, 50, 48), y0=0.55)
    img = kanji_watermark(img, "地", 0.14, 0.30, 480, 11)
    return finish(img, lift=(5, 7, 7), gain=(190, 200, 198), sat=0.55, vig=0.68,
                  seed=seed)


def bars_closeup(seed=95):
    img = B.new_canvas((26, 32, 33), (14, 18, 18))
    d = ImageDraw.Draw(img)
    wx0, wy0, wx1, wy1 = AW * 0.14, AH * 0.10, AW * 0.86, AH * 0.90
    d.rectangle([wx0 - 50, wy0 - 50, wx1 + 50, wy1 + 50], fill=(52, 54, 50))
    d.rectangle([wx0, wy0, wx1, wy1], fill=(9, 11, 11))
    n = B.vnoise(int(wx1 - wx0) // 2, int(wy1 - wy0) // 2, 8, seed, 3)
    n = Image.fromarray((n * 30).astype(np.uint8)).resize((int(wx1 - wx0), int(wy1 - wy0)))
    img.paste(ImageChops.add(img.crop((int(wx0), int(wy0), int(wx1), int(wy1))),
                             Image.merge("RGB", (n, n, n))), (int(wx0), int(wy0)))
    d = ImageDraw.Draw(img)
    for bx in np.linspace(wx0 + 60, wx1 - 60, 7):
        d.line([bx, wy0, bx, wy1], fill=(74, 78, 74), width=22)
        d.line([bx - 8, wy0, bx - 8, wy1], fill=(38, 42, 38), width=8)
    for by in np.linspace(wy0 + 100, wy1 - 100, 3):
        d.line([wx0, by, wx1, by], fill=(64, 68, 64), width=16)
    img = B.add_glow(img, AW * 0.5, AH * 0.5, 380, (40, 52, 50), 0.4)
    return finish(img, lift=(5, 7, 7), gain=(190, 200, 198), sat=0.55, vig=0.66,
                  seed=seed)


def black_corridor(seed=96):
    pal = dict(floor=(14, 16, 16), ceil=(16, 19, 19), wallL=(26, 31, 31),
               wallR=(22, 27, 27), door=(30, 34, 34), light_on=None,
               light_off=(14, 17, 17), refl=(30, 38, 38))
    img, _ = _corridor_base(pal, seed, doors=5, end="black", lights=4, debris=0.6)
    img = B.fog_bands(img, seed, 0.45, (30, 42, 44), y0=0.45)
    return finish(img, lift=(2, 4, 5), gain=(160, 178, 182), sat=0.55, vig=0.76,
                  seed=seed)


def ogawa_far(seed=97):
    img = B.new_canvas((40, 52, 54), (24, 32, 33))
    img = B.add_glow(img, AW * 0.5, AH * 0.40, AW * 0.4, (58, 74, 74), 0.7)
    d = ImageDraw.Draw(img)
    # building silhouette in the clearing, faint window dots
    d.rectangle([AW * 0.34, AH * 0.40, AW * 0.66, AH * 0.74], fill=(30, 38, 38))
    rng = np.random.default_rng(seed)
    for wy in np.linspace(AH * 0.45, AH * 0.68, 3):
        for wx in np.linspace(AW * 0.37, AW * 0.62, 7):
            if rng.random() < 0.8:
                d.rectangle([wx, wy, wx + 22, wy + 28], fill=(14, 19, 19))
    # forest frame: dark trees left/right/bottom
    for i, tx in enumerate(np.linspace(-100, AW * 0.30, 6)):
        B.tree_blob(img, tx, AH * 0.42 + (i % 3) * 60, 190, (7, 11, 10), seed + i)
    for i, tx in enumerate(np.linspace(AW * 0.70, AW + 100, 6)):
        B.tree_blob(img, tx, AH * 0.42 + (i % 3) * 60, 190, (7, 11, 10), seed + 9 + i)
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.74, AW, AH], fill=(10, 14, 13))
    for i, tx in enumerate(np.linspace(0, AW, 9)):
        B.tree_blob(img, tx, AH * 0.80, 70, (6, 9, 8), seed + 30 + i)
    img = B.fog_bands(img, seed, 0.4, (48, 62, 62), y0=0.5)
    return finish(img, lift=(4, 8, 10), gain=(190, 208, 210), sat=0.64, vig=0.62,
                  seed=seed)


def ward_empty(seed=98):
    pal = dict(wallL=(54, 60, 62), wallR=(42, 48, 50), ceil=(34, 38, 40),
               floor=(46, 49, 50), back=(74, 80, 80))
    img = B.new_canvas((17, 19, 20), (30, 33, 34))
    img, (bx0, by0, bx1, by1) = B.room_box(img, pal, seed, back=0.72)
    d = ImageDraw.Draw(img, "RGBA")
    # window on back wall, pale but controlled
    wx0 = bx0 + (bx1 - bx0) * 0.62
    wx1 = bx0 + (bx1 - bx0) * 0.92
    wy0 = by0 + (by1 - by0) * 0.12
    wy1 = by0 + (by1 - by0) * 0.52
    d.rectangle([wx0 - 14, wy0 - 14, wx1 + 14, wy1 + 14], fill=(52, 58, 58, 255))
    d.rectangle([wx0, wy0, wx1, wy1], fill=(132, 148, 148, 255))
    d.line([(wx0 + wx1) / 2, wy0, (wx0 + wx1) / 2, wy1], fill=(40, 44, 44, 255), width=10)
    d.line([wx0, (wy0 + wy1) / 2, wx1, (wy0 + wy1) / 2], fill=(40, 44, 44, 255), width=8)
    img = B.add_glow(img, (wx0 + wx1) / 2, (wy0 + wy1) / 2, 320, (110, 128, 126), 0.6)
    d = ImageDraw.Draw(img, "RGBA")
    ink = (16, 18, 18, 255)
    # bed frames row (bold dark silhouettes)
    for i, bxc in enumerate([bx0 - 80, bx0 + (bx1 - bx0) * 0.30, bx0 + (bx1 - bx0) * 0.66]):
        s = 1.25 - i * 0.18
        bw_, bh_ = 460 * s, 200 * s
        y = by1 + 150 - i * 90
        d.line([bxc, y, bxc, y - bh_], fill=ink, width=int(16 * s))
        d.line([bxc + bw_, y, bxc + bw_, y - bh_ * 0.8], fill=ink, width=int(16 * s))
        d.line([bxc - 6, y - bh_, bxc + 6 + bw_ * 0.06, y - bh_], fill=ink, width=int(12 * s))
        d.rectangle([bxc, y - bh_ * 0.55, bxc + bw_, y - bh_ * 0.55 + 18 * s], fill=ink)
        d.rectangle([bxc, y - bh_ * 0.55 + 18 * s, bxc + bw_, y - bh_ * 0.30],
                    fill=(38, 41, 41, 255))
        if i == 1:  # stained mattress
            d.rectangle([bxc + 10, y - bh_ * 0.62, bxc + bw_ - 10, y - bh_ * 0.48],
                        fill=(84, 84, 74, 255))
    # curtain rail + torn curtain
    d.line([bx0 - 200, by0 + 50, bx1 + 100, by0 + 34], fill=(24, 26, 26, 255), width=9)
    d.polygon([(bx0 + 120, by0 + 44), (bx0 + 330, by0 + 40), (bx0 + 300, by0 + 470),
               (bx0 + 210, by0 + 420), (bx0 + 150, by0 + 300)], fill=(96, 104, 102, 190))
    img = B.fog_bands(img, seed, 0.22, (52, 60, 60), y0=0.6)
    return finish(img, lift=(6, 8, 8), gain=(206, 214, 214), sat=0.6, vig=0.6,
                  seed=seed)


# ================================================================ #1 姫川 (steel blue / red)
def black_tension(seed=100):
    img = B.new_canvas((3, 3, 5), (8, 8, 12))
    img = B.add_glow(img, AW * 0.5, AH * 0.55, AW * 0.3, (26, 20, 24), 0.5)
    n = B.vnoise(AW // 3, AH // 3, 8, seed, 4)
    n = Image.fromarray((n * 22).astype(np.uint8)).resize((AW, AH))
    img = ImageChops.add(img, Image.merge("RGB", (n, n, n)))
    return finish(img, lift=(2, 2, 4), gain=(120, 118, 132), sat=0.7, vig=0.7, seed=seed)


def himekawa_mega(seed=101):
    img = B.new_canvas((14, 18, 30), (36, 44, 60))
    d = ImageDraw.Draw(img)
    # mountain ridges
    rng = np.random.default_rng(seed)
    for ridge, (yb, col) in enumerate([(0.46, (34, 42, 60)), (0.55, (24, 30, 45))]):
        pts = [(0, AH * yb)]
        x = 0
        while x < AW:
            x += rng.uniform(140, 300)
            pts.append((x, AH * (yb - rng.uniform(0.04, 0.13))))
        pts += [(AW, AH * yb), (AW, AH), (0, AH)]
        d.polygon(pts, fill=col)
    # massive slab hospital
    pal = dict(wall=(40, 46, 58))
    B.draw_building(img, AW * 0.10, AH * 0.34, AW * 0.66, AH * 0.80, pal, seed,
                    floors=5, bays=12, broken_p=0.36, sign="姫川病院")
    B.draw_building(img, AW * 0.66, AH * 0.44, AW * 0.90, AH * 0.80, dict(wall=(34, 40, 50)),
                    seed + 1, floors=4, bays=5, broken_p=0.36, roofbox=False)
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.80, AW, AH], fill=(14, 17, 23))
    d.rectangle([AW * 0.30, AH * 0.80, AW * 0.52, AH * 0.86], fill=(20, 24, 31))  # entrance lot
    img = B.fog_bands(img, seed, 0.45, (48, 60, 80), y0=0.45)
    return finish(img, lift=(6, 9, 18), gain=(198, 210, 234), sat=0.74, vig=0.56,
                  halo=(185, 30, 0.4), seed=seed)


def stats_backdrop(seed=102):
    img = himekawa_mega(seed + 1)
    img = ImageEnhance.Brightness(img).enhance(0.55)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, AW * 0.52, AH], fill=(5, 7, 12, 150))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    return B.vignette(img, 0.5)


def decay_rows(seed=103):
    img = B.new_canvas((16, 20, 30), (30, 36, 48))
    pal = dict(wall=(44, 50, 62))
    B.draw_building(img, -AW * 0.05, AH * 0.02, AW * 1.05, AH * 1.0, pal, seed,
                    floors=6, bays=13, broken_p=0.4, roofbox=False)
    img = B.fog_bands(img, seed, 0.25, (50, 62, 82), y0=0.55)
    return finish(img, lift=(6, 9, 17), gain=(200, 211, 233), sat=0.7, vig=0.6,
                  seed=seed)


def news_frame(seed=104):
    inner = himekawa_mega(seed + 3).resize((int(AW * 0.72), int(AH * 0.72)))
    img = texture_board(seed, base=(16, 17, 22))
    img = ImageEnhance.Brightness(img).enhance(0.8)
    ix, iy = int(AW * 0.14), int(AH * 0.09)
    d = ImageDraw.Draw(img)
    d.rectangle([ix - 8, iy - 8, ix + inner.width + 8, iy + inner.height + 8],
                fill=(210, 214, 220))
    img.paste(inner, (ix, iy))
    d = ImageDraw.Draw(img)
    # generic news chrome (fictional neutral)
    d.rectangle([ix, iy, ix + 250, iy + 90], fill=(190, 30, 40))
    f = B.font(56, "black")
    d.text((ix + 125, iy + 45), "NEWS", font=f, anchor="mm", fill=(255, 255, 255))
    d.rectangle([ix, iy + 90, ix + 250, iy + 140], fill=(240, 240, 244))
    f2 = B.font(34, "bold")
    d.text((ix + 125, iy + 115), "2025年放送", font=f2, anchor="mm", fill=(30, 30, 36))
    # lower third
    ly = iy + inner.height - 170
    d.rectangle([ix, ly, ix + inner.width, ly + 170], fill=(244, 244, 248))
    d.rectangle([ix, ly, ix + inner.width, ly + 14], fill=(190, 30, 40))
    f3 = B.font(72, "black")
    d.text((ix + 40, ly + 88), "【取材】廃病院となった現在の姿", font=f3, anchor="lm",
           fill=(24, 24, 30))
    d.rectangle([ix + inner.width - 340, iy + 20, ix + inner.width - 40, iy + 76],
                fill=(0, 0, 0, 120))
    f4 = B.font(40, "bold")
    d.text((ix + inner.width - 190, iy + 48), "新潟県糸魚川市", font=f4, anchor="mm",
           fill=(240, 240, 244))
    return finish(img, lift=(8, 9, 12), gain=(226, 230, 238), sat=0.9, vig=0.5,
                  seed=seed, dirt_amt=0.02)


def broken_glass(seed=105):
    return detail_window_broken(seed)


def rough_corridor(seed=106):
    pal = dict(floor=(24, 28, 34), ceil=(28, 33, 40), wallL=(42, 50, 60),
               wallR=(34, 42, 52), door=(48, 54, 62), light_on=None,
               light_off=(24, 28, 33), refl=(44, 56, 68))
    img, proj = _corridor_base(pal, seed, doors=5, end="window", lights=5, debris=1.0)
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    # fallen ceiling panel
    a = proj(2.4, -0.3, -0.9)
    b = proj(3.2, 0.25, -0.9)
    d.polygon([a, (a[0] + 120, a[1] + 300), (b[0] - 60, b[1] + 380), b],
              fill=(52, 58, 64, 255))
    # hanging wires
    for z in [1.8, 3.5, 5.2]:
        x, y = proj(z, rng.uniform(-0.4, 0.4), -0.9)
        d.line([x, y, x + rng.uniform(-30, 30), y + rng.uniform(120, 320)],
               fill=(14, 15, 18, 255), width=5)
    img = B.fog_bands(img, seed, 0.35, (46, 58, 76), y0=0.48)
    return finish(img, lift=(5, 8, 15), gain=(192, 204, 228), sat=0.66, vig=0.64,
                  seed=seed)


def equipment_room(seed=107):
    pal = dict(wallL=(52, 58, 66), wallR=(40, 46, 54), ceil=(30, 34, 40),
               floor=(44, 47, 52), back=(72, 78, 86))
    img = B.new_canvas((16, 18, 22), (28, 31, 36))
    img, (bx0, by0, bx1, by1) = B.room_box(img, pal, seed, back=0.7)
    # window light from right wall
    img = B.light_cone(img, (AW * 1.05, AH * 0.16), (AW * 0.30, AH * 0.85),
                       (AW * 0.95, AH * 1.05), (108, 122, 134), alpha=80, blur=90)
    d = ImageDraw.Draw(img, "RGBA")
    ink = (14, 16, 19, 255)
    # IV stand
    ivx = bx0 + (bx1 - bx0) * 0.16
    d.line([ivx, by1 + 120, ivx, by0 + 30], fill=ink, width=12)
    d.line([ivx - 70, by0 + 44, ivx + 70, by0 + 44], fill=ink, width=9)
    d.line([ivx - 54, by0 + 44, ivx - 54, by0 + 96], fill=ink, width=6)
    d.ellipse([ivx - 78, by0 + 96, ivx - 30, by0 + 210], fill=(30, 36, 42, 255),
              outline=ink, width=6)
    for leg in (-70, -20, 40, 80):
        d.line([ivx, by1 + 120, ivx + leg, by1 + 170], fill=ink, width=10)
    # machine cart with dead CRT
    mx = bx0 + (bx1 - bx0) * 0.50
    d.rectangle([mx, by1 - 130, mx + 300, by1 + 100], fill=(24, 27, 32, 255),
                outline=(12, 14, 17, 255), width=8)
    d.rectangle([mx + 26, by1 - 104, mx + 160, by1 - 10], fill=(7, 9, 11, 255))
    d.rectangle([mx + 40, by1 - 90, mx + 146, by1 - 24], fill=(16, 22, 26, 255))
    for i in range(4):
        d.ellipse([mx + 190 + (i % 2) * 50, by1 - 100 + (i // 2) * 50,
                   mx + 226 + (i % 2) * 50, by1 - 64 + (i // 2) * 50],
                  fill=ink)
    # wheelchair silhouette (foreground right, backlit rim)
    whx, why = bx1 - 60, by1 + 160
    d.ellipse([whx - 170, why - 240, whx + 70, why], outline=ink, width=16)
    d.ellipse([whx - 130, why - 200, whx + 30, why - 40], outline=(40, 46, 54, 255), width=6)
    d.ellipse([whx - 250, why - 90, whx - 170, why - 10], outline=ink, width=12)
    d.line([whx - 120, why - 300, whx - 40, why - 210], fill=ink, width=14)
    d.line([whx - 200, why - 300, whx - 120, why - 300], fill=ink, width=14)
    d.polygon([(whx - 205, why - 310, ), (whx - 115, why - 310),
               (whx - 135, why - 210), (whx - 185, why - 210)], fill=(20, 23, 27, 255))
    img = B.fog_bands(img, seed, 0.22, (52, 60, 70), y0=0.6)
    return finish(img, lift=(6, 8, 13), gain=(205, 214, 228), sat=0.64, vig=0.6,
                  seed=seed)


def himekawa_dusk(seed=108):
    img = himekawa_mega(seed + 5)
    img = ImageEnhance.Brightness(img).enhance(0.8)
    ov = B.grad_v(AW, AH, (60, 40, 60), (10, 12, 20))
    img = ImageChops.multiply(img, ImageChops.screen(ov, Image.new("RGB", ov.size, (140, 140, 150))))
    img = B.fog_bands(img, seed, 0.3, (52, 54, 74), y0=0.5)
    return finish(img, lift=(7, 8, 15), gain=(210, 205, 228), sat=0.78, vig=0.58,
                  seed=seed)


def cross_section(seed=109):
    """Blueprint elevation of the hospital with haunted hotspots."""
    img = texture_board(seed, base=(8, 11, 18))
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, AW, 84):
        d.line([x, 0, x, AH], fill=(70, 120, 140, 12), width=1)
    for y in range(0, AH, 84):
        d.line([0, y, AW, y], fill=(70, 120, 140, 12), width=1)
    bx0, by0, bx1, by1 = AW * 0.16, AH * 0.16, AW * 0.84, AH * 0.82
    line = (150, 225, 240, 255)
    d.rectangle([bx0, by0, bx1, by1], fill=(18, 26, 38, 255))
    d.rectangle([bx0, by0, bx1, by1], outline=line, width=7)
    floors = 4
    fh = (by1 - by0) / floors
    f_lab = B.font(44, "bold")
    for i in range(1, floors):
        y = by1 - i * fh
        d.line([bx0, y, bx1, y], fill=line, width=4)
    for i in range(floors):
        d.text((bx0 - 30, by1 - i * fh - fh / 2), f"{i + 1}F", font=f_lab, anchor="rm",
               fill=(150, 210, 225, 220))
    # room cells
    cells = 10
    cw = (bx1 - bx0) / cells
    for fl in range(floors):
        for c in range(cells):
            if (fl * 3 + c) % 4 == 0:
                continue
            x = bx0 + c * cw
            y = by1 - (fl + 1) * fh
            d.rectangle([x + 8, y + 10, x + cw - 8, y + fh - 10],
                        outline=(100, 165, 180, 130), width=3)
    # hotspots
    hot = [("霊安室", 0.235, 0.74, "女性の霊"),
           ("手術室", 0.62, 0.575, "男のうめき声"),
           ("廊下", 0.44, 0.41, "ハイヒールの音"),
           ("病室", 0.72, 0.245, "誰もいない部屋の声")]
    f_h = B.font(52, "black")
    f_s = B.font(36, "bold")
    for name, hx, hy, phen in hot:
        x, y = AW * hx, AH * hy
        for r, a in [(46, 60), (26, 120)]:
            d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 70, 78, a), width=4)
        d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(255, 62, 70, 255))
        d.text((x + 60, y - 16), name, font=f_h, anchor="lm", fill=(240, 244, 248, 245))
        d.text((x + 60, y + 34), phen, font=f_s, anchor="lm", fill=(255, 120, 126, 230))
    d.text((AW * 0.5, AH * 0.09), "姫川病院  館内マップ(イメージ)", font=B.font(56, "black"),
           anchor="mm", fill=(170, 220, 232, 240))
    # dashed measure line
    for x in np.arange(bx0, bx1, 40):
        d.line([x, by1 + 46, x + 20, by1 + 46], fill=(120, 190, 205, 140), width=3)
    img = B.add_glow(img, AW * 0.5, AH * 0.5, AW * 0.5, (24, 50, 66), 0.45)
    return finish(img, lift=(4, 6, 12), gain=(210, 224, 240), sat=0.95, vig=0.5,
                  seed=seed, dirt_amt=0.02)


def morgue_corridor(seed=110):
    pal = dict(floor=(20, 26, 30), ceil=(23, 29, 34), wallL=(34, 44, 50),
               wallR=(28, 38, 44), door=(40, 48, 54), light_on=(120, 160, 165),
               light_off=(20, 26, 30), glow=(100, 145, 150), refl=(40, 56, 62),
               flicker_idx=2)
    img, proj = _corridor_base(pal, seed, doors=4, end="door", lights=4, debris=0.6)
    d = ImageDraw.Draw(img, "RGBA")
    # end door with plate 霊安室
    ex0, ey0 = proj(14.0, -0.5, -0.7)
    ex1, ey1 = proj(14.0, 0.5, 1.0)
    d.rectangle([ex0, ey0, ex1, ey1], fill=(30, 36, 40, 255))
    d.rectangle([ex0, ey0, ex1, ey1], outline=(52, 62, 68, 255), width=4)
    px, py = (ex0 + ex1) / 2, ey0 - 40
    d.rectangle([px - 120, py - 34, px + 120, py + 34], fill=(180, 186, 190, 255))
    d.text((px, py), "霊安室", font=B.font(48, "bold"), anchor="mm", fill=(40, 46, 52, 255))
    img = B.fog_bands(img, seed, 0.5, (38, 56, 62), y0=0.42)
    return finish(img, lift=(4, 8, 10), gain=(180, 205, 212), sat=0.66, vig=0.7,
                  seed=seed)


def morgue_interior(seed=111):
    pal = dict(wallL=(30, 38, 42), wallR=(24, 32, 36), ceil=(20, 26, 30),
               floor=(26, 32, 35), back=(44, 54, 58))
    img = B.new_canvas((9, 12, 14), (18, 23, 26))
    img, (bx0, by0, bx1, by1) = B.room_box(img, pal, seed, back=0.68)
    d = ImageDraw.Draw(img, "RGBA")
    # fridge door wall 3x3
    gw = (bx1 - bx0) * 0.72
    gh = (by1 - by0) * 0.8
    gx, gy = bx0 + (bx1 - bx0) * 0.06, by0 + (by1 - by0) * 0.1
    cw, ch = gw / 3, gh / 3
    for i in range(3):
        for j in range(3):
            x, y = gx + i * cw, gy + j * ch
            d.rectangle([x + 6, y + 6, x + cw - 6, y + ch - 6], fill=(74, 84, 88, 255),
                        outline=(38, 46, 50, 255), width=5)
            d.ellipse([x + cw - 52, y + ch / 2 - 12, x + cw - 28, y + ch / 2 + 12],
                      fill=(120, 130, 134, 255))
            d.rectangle([x + 20, y + 18, x + 110, y + 52], fill=(150, 158, 162, 200))
    # one door ajar (dark gap)
    x, y = gx + 1 * cw, gy + 1 * ch
    d.rectangle([x + 6, y + 6, x + cw - 6, y + ch - 6], fill=(8, 10, 11, 255))
    d.polygon([(x + 6, y + 6), (x + cw * 0.55, y + 14), (x + cw * 0.55, y + ch - 14),
               (x + 6, y + ch - 6)], fill=(60, 70, 74, 255))
    # gurney
    gx2, gy2 = bx1 - (bx1 - bx0) * 0.24, by1 + 26
    d.rectangle([gx2 - 260, gy2 - 150, gx2, gy2 - 128], fill=(90, 98, 102, 255))
    d.polygon([(gx2 - 260, gy2 - 128), (gx2, gy2 - 128), (gx2 - 30, gy2 - 20),
               (gx2 - 230, gy2 - 20)], fill=(70, 78, 82, 160))
    d.line([gx2 - 240, gy2 - 128, gx2 - 210, gy2], fill=(40, 46, 50, 255), width=9)
    d.line([gx2 - 40, gy2 - 128, gx2 - 60, gy2], fill=(40, 46, 50, 255), width=9)
    # cold light
    img = B.light_cone(img, (AW * 0.5, -60), (AW * 0.2, AH * 0.9), (AW * 0.8, AH * 0.9),
                       (70, 100, 105), alpha=44, blur=110)
    img = B.fog_bands(img, seed, 0.3, (36, 54, 58), y0=0.55)
    img = kanji_watermark(img, "安", 0.87, 0.26, 540, 10)
    return finish(img, lift=(4, 8, 10), gain=(178, 205, 210), sat=0.7, vig=0.68,
                  seed=seed)


def operating_room(seed=112):
    pal = dict(wallL=(44, 54, 56), wallR=(36, 46, 48), ceil=(28, 36, 38),
               floor=(38, 46, 47), back=(62, 74, 76))
    img = B.new_canvas((14, 18, 19), (26, 33, 34))
    img, (bx0, by0, bx1, by1) = B.room_box(img, pal, seed, back=0.7)
    d = ImageDraw.Draw(img, "RGBA")
    # tiled back wall
    for x in np.arange(bx0, bx1, 60):
        d.line([x, by0, x, by1], fill=(30, 40, 42, 120), width=2)
    for y in np.arange(by0, by1, 60):
        d.line([bx0, y, bx1, y], fill=(30, 40, 42, 120), width=2)
    # surgical lamp
    lcx, lcy = AW * 0.5, by0 - 60
    d.line([lcx, 0, lcx, lcy - 90], fill=(26, 30, 32, 255), width=16)
    d.ellipse([lcx - 190, lcy - 100, lcx + 190, lcy + 60], fill=(52, 60, 62, 255))
    for a in np.linspace(0.35, 2.79, 5):
        bx_ = lcx + np.cos(a) * 140
        by_ = lcy - 20 + np.sin(a) * 46
        d.ellipse([bx_ - 34, by_ - 34, bx_ + 34, by_ + 34], fill=(110, 122, 118, 255))
    d.ellipse([lcx - 34, lcy - 54, lcx + 34, lcy + 14], fill=(146, 158, 148, 255))
    # operating table
    tcx, tcy = AW * 0.5, by1 + 40
    d.rectangle([tcx - 340, tcy - 130, tcx + 340, tcy - 74], fill=(88, 100, 102, 255),
                outline=(20, 26, 27, 255), width=6)
    d.rectangle([tcx - 70, tcy - 74, tcx + 70, tcy + 70], fill=(52, 62, 64, 255))
    d.rectangle([tcx - 210, tcy + 48, tcx + 210, tcy + 74], fill=(40, 48, 50, 255))
    img = B.add_glow(img, lcx, lcy, 380, (110, 130, 118), 0.75)
    img = B.fog_bands(img, seed, 0.35, (36, 52, 52), y0=0.5)
    img = kanji_watermark(img, "呻", 0.13, 0.30, 500, 11)
    return finish(img, lift=(4, 7, 8), gain=(180, 202, 202), sat=0.66, vig=0.68,
                  seed=seed)


def blood_room(seed=113):
    pal = dict(wallL=(40, 22, 24), wallR=(32, 17, 19), ceil=(24, 13, 15),
               floor=(34, 18, 20), back=(54, 26, 28))
    img = B.new_canvas((14, 6, 8), (26, 11, 13))
    img, (bx0, by0, bx1, by1) = B.room_box(img, pal, seed, back=0.7)
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    # dark smears on wall (abstract, tasteful)
    for _ in range(9):
        x = rng.uniform(bx0, bx1)
        y = rng.uniform(by0, by1 * 0.9)
        r = rng.uniform(30, 120)
        d.ellipse([x - r, y - r * 0.5, x + r, y + r * 0.5], fill=(58, 14, 16, 90))
        d.line([x, y, x + rng.uniform(-20, 20), y + rng.uniform(80, 260)],
               fill=(58, 14, 16, 110), width=int(rng.uniform(4, 10)))
    img = B.add_glow(img, AW * 0.5, AH * 0.45, AW * 0.3, (90, 24, 28), 0.6)
    img = B.fog_bands(img, seed, 0.25, (60, 24, 26), y0=0.55)
    img = kanji_watermark(img, "血", 0.85, 0.30, 600, 22, color=(255, 60, 60))
    return finish(img, lift=(10, 3, 4), gain=(225, 170, 175), sat=0.9, vig=0.7,
                  seed=seed)


def heels_floor(seed=114):
    img = B.new_canvas((14, 17, 21), (26, 30, 36))
    d = ImageDraw.Draw(img)
    # low-angle tiled floor
    vpx, vpy = AW * 0.5, AH * 0.30
    for i in range(14):
        t = i / 14
        y = vpy + (AH - vpy) * (t ** 1.7)
        d.line([0, y, AW, y], fill=(38 + int(20 * t), 44 + int(20 * t), 50 + int(22 * t)),
               width=max(1, int(1 + 5 * t)))
    for k in np.linspace(-3.4, 3.4, 15):
        d.line([vpx + k * 90, vpy, vpx + k * 560, AH], fill=(40, 46, 52), width=3)
    d.rectangle([0, 0, AW, vpy], fill=(9, 11, 14))
    # far doorway light
    d.rectangle([vpx - 90, vpy - 260, vpx + 90, vpy], fill=(60, 74, 82))
    img = B.add_glow(img, vpx, vpy - 100, 240, (70, 90, 100), 0.6)
    # reflective sheen
    st = B.streaks(AW, AH, seed, 8, 8)
    img = Image.composite(Image.new("RGB", img.size, (60, 72, 82)), img,
                          Image.fromarray((st * 60).astype(np.uint8)))
    img = B.fog_bands(img, seed, 0.3, (40, 50, 60), y0=0.3)
    return finish(img, lift=(5, 7, 12), gain=(188, 200, 220), sat=0.66, vig=0.66,
                  seed=seed)


def nursecall(seed=115):
    img = B.new_canvas((26, 30, 34), (14, 17, 20))
    n = B.vnoise(AW // 2, AH // 2, 20, seed, 5)
    n = Image.fromarray((n * 46).astype(np.uint8)).resize((AW, AH))
    img = ImageChops.subtract(img, Image.merge("RGB", (n, n, n)))
    d = ImageDraw.Draw(img, "RGBA")
    # wall plate
    px, py = AW * 0.5, AH * 0.47
    d.rectangle([px - 340, py - 260, px + 340, py + 260], fill=(58, 62, 66, 255),
                outline=(34, 38, 42, 255), width=10)
    d.rectangle([px - 300, py - 220, px + 300, py - 120], fill=(44, 48, 52, 255))
    d.text((px, py - 170), "NURSE CALL", font=B.font(54, "bold"), anchor="mm",
           fill=(150, 158, 164, 255))
    # the button
    d.ellipse([px - 110, py - 60, px + 110, py + 160], fill=(90, 30, 32, 255))
    d.ellipse([px - 85, py - 36, px + 85, py + 134], fill=(150, 40, 42, 255))
    d.ellipse([px - 60, py - 12, px + 20, py + 60], fill=(210, 90, 88, 160))
    # dangling cord
    pts = [(px + 250, py + 240)]
    x, y = pts[0]
    rng = np.random.default_rng(seed)
    for _ in range(9):
        x += rng.uniform(-40, 20)
        y += rng.uniform(60, 110)
        pts.append((x, y))
    d.line(pts, fill=(30, 32, 36, 255), width=12)
    img = B.add_glow(img, px, py + 40, 260, (150, 44, 44), 0.75)
    img = B.fog_bands(img, seed, 0.15, (38, 44, 50), y0=0.6)
    return finish(img, lift=(6, 6, 8), gain=(205, 198, 205), sat=0.85, vig=0.66,
                  halo=(150, 44, 0.7), seed=seed)


def nursecall_dark(seed=116):
    img = nursecall(seed + 1)
    img = ImageEnhance.Brightness(img).enhance(0.62)
    return B.vignette(img, 0.4)


def ward_corridor(seed=117):
    pal = dict(floor=(22, 26, 31), ceil=(25, 30, 36), wallL=(38, 45, 54),
               wallR=(31, 38, 47), door=(44, 50, 58), light_on=None,
               light_off=(22, 26, 30), refl=(42, 52, 64))
    img, proj = _corridor_base(pal, seed, doors=6, end="black", lights=5, debris=0.7)
    d = ImageDraw.Draw(img, "RGBA")
    # open doorway with pale spill mid-left
    a = proj(3.0, -1, 1.0)
    b = proj(3.7, -1, 1.0)
    c = proj(3.7, -1, -0.62)
    e = proj(3.0, -1, -0.62)
    d.polygon([a, b, c, e], fill=(70, 86, 92, 255))
    img = B.add_glow(img, (a[0] + c[0]) / 2, (a[1] + c[1]) / 2, 200, (70, 90, 96), 0.5)
    img = B.fog_bands(img, seed, 0.4, (42, 56, 68), y0=0.45)
    return finish(img, lift=(4, 7, 12), gain=(185, 200, 222), sat=0.64, vig=0.68,
                  seed=seed)


def himekawa_loom(seed=118):
    img = B.new_canvas((6, 8, 15), (16, 20, 30))
    d = ImageDraw.Draw(img)
    # low angle night mass
    d.polygon([(AW * 0.06, AH), (AW * 0.24, AH * 0.06), (AW * 0.78, AH * 0.06),
               (AW * 0.96, AH)], fill=(22, 27, 37))
    rng = np.random.default_rng(seed)
    for fy in np.linspace(AH * 0.12, AH * 0.88, 8):
        t = (fy - AH * 0.06) / AH
        x0 = AW * (0.24 - 0.13 * t)
        x1 = AW * (0.78 + 0.13 * t)
        for wx in np.linspace(x0 + 40, x1 - 40, 10):
            ww = (x1 - x0) / 10 * 0.44
            col = (9, 11, 16) if rng.random() > 0.15 else (5, 6, 9)
            d.rectangle([wx, fy, wx + ww, fy + AH * 0.05 * (0.5 + t)], fill=col)
    img = B.fog_bands(img, seed, 0.45, (40, 52, 74), y0=0.5)
    img = B.add_glow(img, AW * 0.5, AH * 0.0, AW * 0.5, (44, 56, 84), 0.5)
    img = kanji_watermark(img, "現", 0.88, 0.72, 560, 11)
    return finish(img, lift=(4, 6, 13), gain=(180, 194, 224), sat=0.7, vig=0.62,
                  halo=(170, 30, 0.4), seed=seed)


def himekawa_years(seed=119):
    img = himekawa_dusk(seed + 2)
    img = ImageEnhance.Brightness(img).enhance(0.7)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, AH * 0.30, AW, AH * 0.72], fill=(4, 6, 10, 110))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    return B.vignette(img, 0.5)


def night_wide(seed=120):
    img = B.new_canvas((5, 7, 13), (13, 17, 26))
    d = ImageDraw.Draw(img)
    stars = np.random.default_rng(seed)
    for _ in range(70):
        x, y = stars.uniform(0, AW), stars.uniform(0, AH * 0.4)
        d.point([x, y], fill=(140, 150, 170))
    for ridge, (yb, col) in enumerate([(0.52, (14, 18, 28)), (0.60, (10, 13, 20))]):
        pts = [(0, AH * yb)]
        x = 0
        while x < AW:
            x += stars.uniform(160, 320)
            pts.append((x, AH * (yb - stars.uniform(0.05, 0.14))))
        pts += [(AW, AH * yb), (AW, AH), (0, AH)]
        d.polygon(pts, fill=col)
    pal = dict(wall=(20, 25, 35))
    B.draw_building(img, AW * 0.22, AH * 0.44, AW * 0.78, AH * 0.82, pal, seed,
                    floors=4, bays=11, broken_p=0.3, glass=(8, 10, 15))
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.82, AW, AH], fill=(8, 10, 15))
    img = B.fog_bands(img, seed, 0.4, (34, 44, 64), y0=0.5)
    return finish(img, lift=(3, 5, 11), gain=(170, 184, 216), sat=0.72, vig=0.62,
                  seed=seed)


def keepout_gate(seed=121):
    img = B.new_canvas((10, 13, 22), (20, 26, 38))
    d = ImageDraw.Draw(img, "RGBA")
    # building far behind
    pal = dict(wall=(26, 32, 42))
    B.draw_building(img, AW * 0.30, AH * 0.30, AW * 0.74, AH * 0.72, pal, seed,
                    floors=4, bays=7, broken_p=0.3)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, AH * 0.72, AW, AH], fill=(12, 15, 21))
    # gate bars across
    for x in np.linspace(-40, AW + 40, 17):
        d.line([x, AH * 0.30, x, AH * 0.98], fill=(52, 58, 68, 240), width=16)
    d.line([0, AH * 0.34, AW, AH * 0.32], fill=(64, 70, 80, 250), width=18)
    d.line([0, AH * 0.86, AW, AH * 0.84], fill=(64, 70, 80, 250), width=18)
    # chain + padlock
    ccx, ccy = AW * 0.5, AH * 0.60
    for i in range(10):
        a = i * 0.5
        d.ellipse([ccx - 140 + i * 30, ccy - 16 + 12 * np.sin(a),
                   ccx - 100 + i * 30, ccy + 24 + 12 * np.sin(a)],
                  outline=(96, 102, 112, 255), width=8)
    d.rectangle([ccx + 10, ccy + 10, ccx + 90, ccy + 110], fill=(70, 76, 86, 255))
    d.arc([ccx + 20, ccy - 40, ccx + 80, ccy + 30], 180, 360, fill=(96, 102, 112, 255),
          width=12)
    # sign
    sx, sy = AW * 0.56, AH * 0.38
    d.rectangle([sx, sy, sx + 460, sy + 200], fill=(202, 196, 184, 255),
                outline=(160, 52, 46, 255), width=10)
    d.text((sx + 230, sy + 74), "立入禁止", font=B.font(92, "black"), anchor="mm",
           fill=(170, 40, 38, 255))
    d.text((sx + 230, sy + 158), "KEEP OUT", font=B.font(44, "bold"), anchor="mm",
           fill=(60, 60, 64, 255))
    img = B.fog_bands(img, seed, 0.35, (40, 52, 74), y0=0.5)
    return finish(img, lift=(5, 8, 15), gain=(195, 206, 230), sat=0.7, vig=0.62,
                  seed=seed)


def window_grid(seed=122):
    img = B.new_canvas((12, 16, 26), (24, 30, 42))
    pal = dict(wall=(38, 44, 56))
    B.draw_building(img, -AW * 0.2, -AH * 0.1, AW * 1.2, AH * 1.1, pal, seed,
                    floors=5, bays=16, broken_p=0.38, roofbox=False, glass=(14, 18, 26))
    # one window darker than black w/ faint outline
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([AW * 0.62, AH * 0.42, AW * 0.678, AH * 0.53], fill=(2, 2, 4, 255))
    img = B.fog_bands(img, seed, 0.2, (46, 58, 80), y0=0.6)
    return finish(img, lift=(5, 8, 16), gain=(192, 204, 230), sat=0.68, vig=0.6,
                  seed=seed)


# ================================================================ OUTRO
def recap_board(seed=130):
    img = texture_board(seed, base=(11, 13, 17))
    d = ImageDraw.Draw(img, "RGBA")
    # five slots
    for i in range(5):
        y = AH * (0.16 + i * 0.15)
        d.rectangle([AW * 0.20, y, AW * 0.80, y + AH * 0.115],
                    outline=(120, 140, 155, 60), width=3)
        d.rectangle([AW * 0.20, y, AW * 0.215, y + AH * 0.115],
                    fill=(150, 46, 52, 140))
    img = kanji_watermark(img, "残", 0.87, 0.78, 660, 12)
    return finish(img, lift=(5, 6, 9), gain=(205, 212, 224), sat=0.8, vig=0.56,
                  seed=seed)


def dawn_calm(seed=131):
    img = B.new_canvas((60, 68, 88), (150, 140, 138))
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.75, AW, AH], fill=(30, 33, 40))
    for i, tx in enumerate(np.linspace(-60, AW + 60, 15)):
        B.tree_blob(img, tx, AH * 0.70 + (i % 3) * 20, 110, (24, 28, 32), seed + i)
    pal = dict(wall=(52, 56, 66))
    B.draw_building(img, AW * 0.30, AH * 0.34, AW * 0.72, AH * 0.75, pal, seed,
                    floors=4, bays=9, broken_p=0.3, glass=(30, 34, 42))
    img = B.fog_bands(img, seed, 0.5, (110, 112, 122), y0=0.45)
    img = B.add_glow(img, AW * 0.5, AH * 0.30, AW * 0.4, (140, 120, 110), 0.4)
    return finish(img, lift=(14, 15, 20), gain=(225, 222, 230), sat=0.6, vig=0.5,
                  seed=seed)


def lightsout_corridor(seed=132):
    pal = dict(floor=(16, 19, 23), ceil=(18, 22, 27), wallL=(28, 34, 42),
               wallR=(23, 29, 37), door=(32, 38, 44), light_on=(110, 126, 132),
               light_off=(14, 17, 21), glow=(90, 110, 116), refl=(32, 42, 52),
               flicker_idx=0)
    img, _ = _corridor_base(pal, seed, doors=5, end="black", lights=5, debris=0.5)
    img = B.fog_bands(img, seed, 0.45, (32, 44, 56), y0=0.42)
    return finish(img, lift=(3, 5, 9), gain=(168, 182, 205), sat=0.6, vig=0.72,
                  seed=seed)


def five_horizon(seed=133):
    img = B.new_canvas((6, 8, 14), (16, 19, 27))
    d = ImageDraw.Draw(img)
    d.rectangle([0, AH * 0.70, AW, AH], fill=(9, 11, 16))
    shapes = [(0.10, 0.36, 0.115), (0.285, 0.30, 0.13), (0.47, 0.40, 0.10),
              (0.645, 0.33, 0.12), (0.825, 0.26, 0.14)]
    labels = ["黒瀬病院", "旧相武病院", "旧野木病院", "小美玉小川脳病院", "姫川病院"]
    f = B.font(40, "bold")
    rng = np.random.default_rng(seed)
    for (x, hgt, w_), lab in zip(shapes, labels):
        bx0, bx1 = AW * x, AW * (x + w_)
        by0, by1 = AH * (0.70 - hgt), AH * 0.70
        d.rectangle([bx0, by0, bx1, by1], fill=(15, 18, 25))
        for wy in np.linspace(by0 + 20, by1 - 30, 6):
            for wx in np.linspace(bx0 + 14, bx1 - 30, 5):
                if rng.random() < 0.8:
                    d.rectangle([wx, wy, wx + 14, wy + 18], fill=(7, 9, 13))
        d.text(((bx0 + bx1) / 2, by0 - 46), lab, font=f, anchor="mm",
               fill=(148, 160, 175))
    img = B.fog_bands(img, seed, 0.6, (36, 46, 64), y0=0.55)
    img = B.add_glow(img, AW * 0.5, AH * 0.18, AW * 0.5, (30, 40, 60), 0.5)
    return finish(img, lift=(4, 6, 12), gain=(178, 190, 218), sat=0.7, vig=0.6,
                  seed=seed)


# ================================================================ overlays (RGBA)
def ov_boy():
    f = B.fig_humanoid(560, "boy")
    return f


def ov_roof_figure():
    f = B.fig_humanoid(300, "shadow")
    return f


def ov_woman_hair():
    return B.fig_humanoid(760, "pale")


def ov_woman_pale():
    return B.fig_humanoid(820, "pale")


def ov_pupil():
    img = Image.new("RGBA", (700, 700), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([120, 120, 580, 580], fill=(12, 8, 8, 255))
    d.ellipse([200, 190, 320, 300], fill=(200, 188, 176, 200))
    return img.filter(ImageFilter.GaussianBlur(3))


def _robe(seed):
    f = B.fig_humanoid(720, "robe", seed)
    return f


def ov_robe_a():
    return _robe(1)


def ov_robe_b():
    return _robe(2)


def ov_robe_c():
    return _robe(3)


def ov_robe_far():
    return B.fig_humanoid(430, "robe", 5)


def ov_reach_woman():
    return B.fig_humanoid(880, "reach")


def ov_shadow_pass():
    f = B.fig_humanoid(760, "shadow")
    return f.filter(ImageFilter.GaussianBlur(9))


BUILDERS = {n: f for n, f in globals().items()
            if callable(f) and not n.startswith(("_", "ov_")) and
            n not in ("finish", "texture_board", "ghost_number", "kanji_watermark",
                      "nv_process")}
OVERLAYS = {n: f for n, f in globals().items() if callable(f) and n.startswith("ov_")}
