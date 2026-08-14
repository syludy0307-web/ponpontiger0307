# -*- coding: utf-8 -*-
"""Scene stills for the JAL123 investigative documentary.

Visual language: technical / blueprint.  Deep navy ground, cyan schematic
line-work, amber data accents, restrained red reserved for failure points.
Deliberately non-sensational: no wreckage detail, no victims, no gore.
"""
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from common import AW, AH
import art_base as B

# ---------------------------------------------------------------- palette
BG0 = (10, 15, 26)
BG1 = (20, 29, 44)
GRID = (78, 132, 168)
LINE = (150, 214, 236)
INK = (8, 11, 18)
AMB = (232, 176, 74)
RED = (216, 66, 72)
PAPER = (222, 216, 202)
STEEL = (120, 138, 158)


def font(sz, w="black", serif=False):
    return B.font(sz, w, serif)


def finish(img, sat=0.92, vig=0.42, seed=1, dirt_amt=0.02, bright=1.0):
    img = ImageEnhance.Brightness(img).enhance(bright)
    img = B.grade(img, (6, 9, 14), (232, 238, 246), 1.0, sat)
    img = B.vignette(img, vig)
    if dirt_amt:
        img = B.dirt(img, seed + 41, dirt_amt)
    return img


def board(seed=1, glow=None, grid=True, gstep=96):
    """Blueprint backplate."""
    img = B.new_canvas(BG1, BG0)
    n = B.vnoise(AW // 3, AH // 3, 10, seed, 4)
    n = Image.fromarray((n * 34).astype(np.uint8)).resize((AW, AH))
    img = ImageChops.subtract(img, Image.merge("RGB", (n, n, n)))
    if grid:
        d = ImageDraw.Draw(img, "RGBA")
        for x in range(0, AW, gstep):
            d.line([x, 0, x, AH], fill=(*GRID, 16), width=1)
        for y in range(0, AH, gstep):
            d.line([0, y, AW, y], fill=(*GRID, 16), width=1)
        for x in range(0, AW, gstep * 5):
            d.line([x, 0, x, AH], fill=(*GRID, 30), width=2)
        for y in range(0, AH, gstep * 5):
            d.line([0, y, AW, y], fill=(*GRID, 30), width=2)
    if glow:
        img = B.add_glow(img, glow[0], glow[1], glow[2], (26, 54, 78), 0.55)
    return img


def corner_marks(img, label="", code=""):
    d = ImageDraw.Draw(img, "RGBA")
    for (x, y, sx, sy) in ((110, 100, 1, 1), (AW - 110, 100, -1, 1),
                           (110, AH - 100, 1, -1), (AW - 110, AH - 100, -1, -1)):
        d.line([x, y, x + 70 * sx, y], fill=(*LINE, 90), width=3)
        d.line([x, y, x, y + 70 * sy], fill=(*LINE, 90), width=3)
    if label:
        d.text((150, 128), label, font=font(34, "bold"), fill=(*LINE, 120))
    if code:
        d.text((AW - 150, 128), code, font=font(30, "bold"), fill=(*GRID, 130),
               anchor="ra")
    return img


def dim_line(d, x0, y0, x1, y1, text, col=LINE, sz=32, off=26):
    d.line([x0, y0, x1, y1], fill=(*col, 190), width=3)
    for (px, py) in ((x0, y0), (x1, y1)):
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(*col, 220))
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    d.text((mx, my - off), text, font=font(sz, "bold"), fill=(*col, 230), anchor="ms")


# ================================================================ 747 shapes
def b747_side(d, cx, cy, L, col=(206, 214, 226), tail_col=None, alpha=255,
              outline=None, gear=False, flaps=False, no_tail=False):
    """Stylised 747 side view centred at (cx,cy), fuselage length L."""
    u = L / 100.0
    tail_col = tail_col or col
    body = [(cx - 50 * u, cy + 2 * u), (cx - 46 * u, cy - 4 * u),
            (cx + 20 * u, cy - 6 * u), (cx + 40 * u, cy - 5 * u),
            (cx + 48 * u, cy - 1 * u), (cx + 50 * u, cy + 2 * u),
            (cx + 44 * u, cy + 5 * u), (cx - 40 * u, cy + 6 * u),
            (cx - 50 * u, cy + 4 * u)]
    # upper deck hump (front)
    hump = [(cx + 10 * u, cy - 6 * u), (cx + 22 * u, cy - 11 * u),
            (cx + 40 * u, cy - 10 * u), (cx + 46 * u, cy - 5 * u)]
    d.polygon(body, fill=(*col, alpha))
    d.polygon(hump, fill=(*col, alpha))
    # wing (swept back, seen from side as a wedge)
    d.polygon([(cx + 4 * u, cy + 3 * u), (cx - 26 * u, cy + 9 * u),
               (cx - 34 * u, cy + 9 * u), (cx - 2 * u, cy + 1 * u)],
              fill=(*col, alpha))
    # horizontal stabiliser
    d.polygon([(cx - 40 * u, cy - 1 * u), (cx - 56 * u, cy + 3 * u),
               (cx - 50 * u, cy + 3 * u), (cx - 38 * u, cy + 1 * u)],
              fill=(*col, alpha))
    if not no_tail:
        d.polygon([(cx - 34 * u, cy - 3 * u), (cx - 44 * u, cy - 26 * u),
                   (cx - 52 * u, cy - 26 * u), (cx - 50 * u, cy - 2 * u)],
                  fill=(*tail_col, alpha))
    # engines
    for ex, ey in ((-18, 8), (-6, 7)):
        d.rounded_rectangle([cx + ex * u - 5 * u, cy + ey * u - 2.2 * u,
                             cx + ex * u + 5 * u, cy + ey * u + 2.4 * u],
                            radius=2.2 * u, fill=(*col, alpha))
    if gear:
        for gx in (-30, 2, 8):
            d.line([cx + gx * u, cy + 6 * u, cx + gx * u, cy + 12 * u],
                   fill=(*col, alpha), width=max(2, int(1.4 * u)))
            d.ellipse([cx + gx * u - 2.4 * u, cy + 11 * u,
                       cx + gx * u + 2.4 * u, cy + 15.5 * u], fill=(*col, alpha))
    if flaps:
        d.polygon([(cx - 26 * u, cy + 9 * u), (cx - 36 * u, cy + 13 * u),
                   (cx - 30 * u, cy + 13 * u), (cx - 22 * u, cy + 9 * u)],
                  fill=(*AMB, alpha))
    if outline:
        d.line(body + [body[0]], fill=(*outline, 220), width=3)
    return u


def b747_top(d, cx, cy, L, col=(198, 208, 222), alpha=235):
    u = L / 100.0
    d.polygon([(cx + 50 * u, cy), (cx + 40 * u, cy - 4 * u), (cx - 40 * u, cy - 5 * u),
               (cx - 50 * u, cy - 2 * u), (cx - 50 * u, cy + 2 * u),
               (cx - 40 * u, cy + 5 * u), (cx + 40 * u, cy + 4 * u)],
              fill=(*col, alpha))
    for s in (-1, 1):
        d.polygon([(cx + 6 * u, cy + 3 * u * s), (cx - 30 * u, cy + 42 * u * s),
                   (cx - 40 * u, cy + 42 * u * s), (cx - 8 * u, cy + 2 * u * s)],
                  fill=(*col, alpha))
        d.polygon([(cx - 38 * u, cy + 2 * u * s), (cx - 52 * u, cy + 18 * u * s),
                   (cx - 58 * u, cy + 17 * u * s), (cx - 48 * u, cy + 1 * u * s)],
                  fill=(*col, alpha))


# ================================================================ scenes
def title_open(seed=10):
    img = board(seed, glow=(AW * 0.5, AH * 0.55, AW * 0.5))
    d = ImageDraw.Draw(img, "RGBA")
    # horizon glow + faint cloud deck
    d.rectangle([0, AH * 0.66, AW, AH], fill=(*BG0, 255))
    for i in range(9):
        y = AH * (0.66 + i * 0.035)
        d.line([0, y, AW, y], fill=(*GRID, max(6, 26 - i * 3)), width=6)
    img = B.add_glow(img, AW * 0.5, AH * 0.68, AW * 0.55, (36, 62, 88), 0.6)
    d = ImageDraw.Draw(img, "RGBA")
    b747_side(d, AW * 0.5, AH * 0.44, AW * 0.46, col=(24, 32, 46),
              outline=(120, 176, 206))
    img = B.add_glow(img, AW * 0.5, AH * 0.44, AW * 0.30, (30, 58, 82), 0.5)
    return finish(img, seed=seed, vig=0.5)


def haneda_departure(seed=11):
    img = board(seed, grid=False)
    d = ImageDraw.Draw(img, "RGBA")
    # dusk sky band
    band = B.grad_v(AW, int(AH * 0.62), (54, 46, 66), (16, 22, 36))
    img.paste(band, (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, AH * 0.62, AW, AH], fill=(12, 16, 24))
    # runway perspective
    d.polygon([(AW * 0.30, AH), (AW * 0.47, AH * 0.62), (AW * 0.53, AH * 0.62),
               (AW * 0.78, AH)], fill=(26, 31, 40))
    for i in range(9):
        t = i / 9
        y = AH * (0.63 + 0.37 * t ** 1.7)
        w = 8 + 26 * t
        d.rectangle([AW * 0.5 - w / 2, y, AW * 0.5 + w / 2, y + 10 + 26 * t],
                    fill=(*PAPER, 150))
    # apron lights
    for x in np.linspace(AW * 0.05, AW * 0.95, 16):
        img = B.add_glow(img, x, AH * 0.63, 46, (200, 150, 70), 0.5)
    d = ImageDraw.Draw(img, "RGBA")
    b747_side(d, AW * 0.56, AH * 0.40, AW * 0.40, col=(216, 222, 232), gear=True)
    img = B.add_glow(img, AW * 0.56, AH * 0.40, AW * 0.26, (60, 78, 104), 0.45)
    img = B.fog_bands(img, seed, 0.18, (60, 74, 96), y0=0.6)
    return finish(img, seed=seed, vig=0.46)


def manifest_grid(seed=12):
    """524 dots — one per person aboard.  Restrained, no names."""
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    cols, rows = 38, 14
    x0, y0 = AW * 0.14, AH * 0.26
    gx = (AW * 0.72) / cols
    gy = (AH * 0.46) / rows
    n = 0
    for r in range(rows):
        for c in range(cols):
            if n >= 524:
                break
            x, y = x0 + c * gx, y0 + r * gy
            d.ellipse([x, y, x + gx * 0.42, y + gx * 0.42], fill=(*LINE, 150))
            n += 1
    return finish(img, seed=seed)


def cabin_seats(seed=13):
    img = B.new_canvas((34, 38, 48), (18, 21, 28))
    d = ImageDraw.Draw(img, "RGBA")
    # one-point cabin: seat rows receding
    vx, vy = AW * 0.5, AH * 0.46
    for i in range(9):
        t = i / 9
        z = 1 - t
        w = AW * (0.14 + 0.62 * z)
        h = AH * (0.05 + 0.16 * z)
        y = vy + AH * (0.06 + 0.36 * z)
        shade = int(40 + 70 * z)
        d.rectangle([vx - w / 2, y - h, vx + w / 2, y], fill=(shade, shade + 6, shade + 14))
        d.rectangle([vx - w / 2, y - h, vx + w / 2, y - h + h * 0.18],
                    fill=(shade + 20, shade + 26, shade + 34))
        for k in (-1, 1):
            d.rectangle([vx + k * w * 0.16, y - h, vx + k * w * 0.16 + 4, y],
                        fill=(shade - 12, shade - 8, shade - 2))
    # ceiling + windows
    d.polygon([(0, 0), (AW, 0), (vx + AW * 0.09, vy), (vx - AW * 0.09, vy)],
              fill=(30, 35, 44))
    for side in (-1, 1):
        for i in range(6):
            t = i / 6
            wx = vx + side * AW * (0.10 + 0.40 * t)
            wy = vy + AH * (0.02 + 0.10 * t)
            ww = 20 + 70 * t
            d.rounded_rectangle([wx - ww / 2, wy - ww * 0.7, wx + ww / 2, wy + ww * 0.7],
                                radius=ww * 0.35, fill=(46, 56, 70))
    img = B.add_glow(img, vx, vy, AW * 0.2, (40, 50, 64), 0.5)
    return finish(img, seed=seed, vig=0.5)


def cruise_alt(seed=14):
    img = board(seed, glow=(AW * 0.5, AH * 0.5, AW * 0.45))
    d = ImageDraw.Draw(img, "RGBA")
    # altitude ladder
    for i in range(11):
        y = AH * (0.18 + i * 0.062)
        d.line([AW * 0.10, y, AW * 0.18, y], fill=(*GRID, 120), width=3)
        d.text((AW * 0.085, y), f"{(30 - i * 2):02d},000", font=font(28, "bold"),
               fill=(*GRID, 150), anchor="rm")
    d.line([AW * 0.10, AH * 0.305, AW * 0.90, AH * 0.305], fill=(*AMB, 170), width=4)
    b747_side(d, AW * 0.55, AH * 0.305, AW * 0.34, col=(210, 218, 230))
    img = B.add_glow(img, AW * 0.55, AH * 0.31, AW * 0.24, (34, 60, 84), 0.5)
    img = corner_marks(img, "CRUISE", "FL240")
    return finish(img, seed=seed)


def bang_abstract(seed=15):
    """The structural failure, rendered as a schematic shock — not a spectacle."""
    img = board(seed, grid=False)
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = AW * 0.34, AH * 0.46
    for r, a, wd in ((260, 200, 12), (430, 130, 8), (620, 80, 6), (830, 44, 4)):
        d.ellipse([cx - r, cy - r * 0.72, cx + r, cy + r * 0.72],
                  outline=(*RED, a), width=wd)
    for ang in np.linspace(0, 6.283, 26):
        r0, r1 = 250, 250 + np.random.default_rng(seed + int(ang * 9)).uniform(120, 520)
        d.line([cx + np.cos(ang) * r0, cy + np.sin(ang) * r0 * 0.72,
                cx + np.cos(ang) * r1, cy + np.sin(ang) * r1 * 0.72],
               fill=(*RED, 120), width=4)
    img = B.add_glow(img, cx, cy, 620, (120, 30, 34), 0.75)
    d = ImageDraw.Draw(img, "RGBA")
    b747_side(d, AW * 0.58, AH * 0.5, AW * 0.40, col=(30, 38, 52),
              outline=(150, 180, 200))
    return finish(img, seed=seed, sat=1.0, vig=0.5)


def oxygen_masks(seed=16):
    img = B.new_canvas((30, 34, 44), (14, 17, 24))
    d = ImageDraw.Draw(img, "RGBA")
    d.polygon([(0, 0), (AW, 0), (AW, AH * 0.30), (0, AH * 0.30)], fill=(38, 43, 54))
    d.rectangle([0, AH * 0.30, AW, AH * 0.33], fill=(24, 28, 36))
    rng = np.random.default_rng(seed)
    for i, x in enumerate(np.linspace(AW * 0.06, AW * 0.94, 9)):
        drop = AH * (0.30 + rng.uniform(0.10, 0.24))
        d.line([x, AH * 0.32, x + rng.uniform(-14, 14), drop], fill=(190, 196, 204, 220),
               width=4)
        d.ellipse([x - 46, drop, x + 46, drop + 92], fill=(226, 228, 232, 240))
        d.ellipse([x - 30, drop + 18, x + 30, drop + 74], fill=(150, 158, 168, 255))
    img = B.add_glow(img, AW * 0.5, AH * 0.34, AW * 0.4, (52, 62, 78), 0.5)
    return finish(img, seed=seed, vig=0.52)


def tail_loss(seed=17):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    b747_side(d, AW * 0.52, AH * 0.48, AW * 0.62, col=(38, 46, 60),
              outline=(140, 190, 214), no_tail=True)
    u = (AW * 0.62) / 100.0
    cx, cy = AW * 0.52, AH * 0.48
    # ghost of the lost fin
    d.polygon([(cx - 34 * u, cy - 3 * u), (cx - 44 * u, cy - 26 * u),
               (cx - 52 * u, cy - 26 * u), (cx - 50 * u, cy - 2 * u)],
              fill=(*RED, 46))
    d.line([(cx - 34 * u, cy - 3 * u), (cx - 44 * u, cy - 26 * u),
            (cx - 52 * u, cy - 26 * u), (cx - 50 * u, cy - 2 * u)],
           fill=(*RED, 200), width=4)
    for i in range(7):
        yy = cy - 4 * u - i * 3.2 * u
        d.line([cx - 51 * u, yy, cx - 36 * u + i * 1.6 * u, yy], fill=(*RED, 70), width=2)
    img = corner_marks(img, "VERTICAL STABILIZER", "LOST ≒ 大部分")
    return finish(img, seed=seed)


def hydraulic_diagram(seed=18):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    b747_top(d, AW * 0.5, AH * 0.46, AW * 0.60, col=(58, 70, 88))
    u = (AW * 0.60) / 100.0
    cx, cy = AW * 0.5, AH * 0.46
    cols = [(96, 200, 220), (120, 190, 240), (150, 200, 210), (110, 210, 190)]
    for i in range(4):
        off = (i - 1.5) * 5 * u
        pts = [(cx + 40 * u, cy + off * 0.35), (cx + 4 * u, cy + off * 0.7),
               (cx - 30 * u, cy + off), (cx - 44 * u, cy + off * 0.8)]
        d.line(pts, fill=(*cols[i], 230), width=7, joint="curve")
        lx, ly = cx + 42 * u, cy + off * 0.35
        d.rounded_rectangle([lx, ly - 24, lx + 88, ly + 24], radius=8,
                            fill=(14, 20, 30, 220), outline=(*cols[i], 200), width=3)
        d.text((lx + 44, ly), f"#{i + 1}", font=font(32, "bold"),
               fill=(*cols[i], 245), anchor="mm")
    # severance point at the tail
    d.ellipse([cx - 52 * u, cy - 12 * u, cx - 34 * u, cy + 12 * u],
              outline=(*RED, 230), width=6)
    d.line([cx - 50 * u, cy - 10 * u, cx - 36 * u, cy + 10 * u], fill=(*RED, 230), width=6)
    d.line([cx - 36 * u, cy - 10 * u, cx - 50 * u, cy + 10 * u], fill=(*RED, 230), width=6)
    img = B.add_glow(img, cx - 43 * u, cy, 220, (110, 26, 30), 0.6)
    img = corner_marks(img, "HYDRAULIC SYSTEMS ×4", "ALL LOST")
    return finish(img, seed=seed)


def cockpit_panel(seed=19):
    img = B.new_canvas((26, 30, 38), (14, 16, 22))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([AW * 0.08, AH * 0.16, AW * 0.92, AH * 0.86], radius=40,
                        fill=(22, 26, 33), outline=(60, 70, 84), width=6)
    rng = np.random.default_rng(seed)
    for r in range(2):
        for c in range(5):
            x = AW * (0.15 + c * 0.145)
            y = AH * (0.30 + r * 0.28)
            rr = AH * 0.10
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(14, 17, 22),
                      outline=(74, 86, 100), width=5)
            for a in np.linspace(-2.2, 2.2, 9):
                d.line([x + np.sin(a) * rr * 0.72, y - np.cos(a) * rr * 0.72,
                        x + np.sin(a) * rr * 0.9, y - np.cos(a) * rr * 0.9],
                       fill=(140, 154, 170, 200), width=3)
            ang = rng.uniform(-2.4, 2.4)
            col = AMB if rng.random() < 0.4 else (170, 190, 210)
            d.line([x, y, x + np.sin(ang) * rr * 0.66, y - np.cos(ang) * rr * 0.66],
                   fill=(*col, 235), width=6)
    # warning caption lights
    for i, (lab, col) in enumerate((("MASTER WARNING", RED), ("HYD", RED),
                                    ("R HYD", RED), ("APU", AMB))):
        x = AW * (0.16 + i * 0.19)
        d.rounded_rectangle([x, AH * 0.70, x + AW * 0.15, AH * 0.79], radius=10,
                            fill=(*col, 60), outline=(*col, 220), width=4)
        d.text((x + AW * 0.075, AH * 0.745), lab, font=font(30, "black"),
               fill=(*col, 255), anchor="mm")
        img = B.add_glow(img, x + AW * 0.075, AH * 0.745, 150, col, 0.35)
        d = ImageDraw.Draw(img, "RGBA")
    return finish(img, seed=seed, vig=0.5)


def yoke_unresponsive(seed=20):
    img = board(seed, grid=False, glow=(AW * 0.5, AH * 0.5, AW * 0.4))
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = AW * 0.42, AH * 0.52
    d.arc([cx - 260, cy - 220, cx + 260, cy + 300], 200, 340, fill=(*STEEL, 255), width=34)
    d.line([cx - 250, cy + 40, cx - 250, cy + 250], fill=(*STEEL, 255), width=30)
    d.line([cx + 250, cy + 40, cx + 250, cy + 250], fill=(*STEEL, 255), width=30)
    d.rounded_rectangle([cx - 70, cy + 210, cx + 70, cy + 470], radius=26,
                        fill=(*STEEL, 255))
    # motion arrows that lead nowhere
    for s in (-1, 1):
        d.line([cx + s * 330, cy - 40, cx + s * 470, cy - 40], fill=(*RED, 180), width=8)
        d.polygon([(cx + s * 500, cy - 40), (cx + s * 455, cy - 66),
                   (cx + s * 455, cy - 14)], fill=(*RED, 180))
    d.text((AW * 0.80, AH * 0.44), "NO\nRESPONSE", font=font(86, "black"),
           fill=(*RED, 235), anchor="mm", align="center")
    return finish(img, seed=seed)


def dutch_roll(seed=21):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    xs = np.linspace(AW * 0.10, AW * 0.90, 400)
    ys = AH * 0.50 + np.sin((xs - AW * 0.1) / AW * 22) * AH * 0.16
    d.line(list(zip(xs, ys)), fill=(*AMB, 190), width=6)
    for i, t in enumerate(np.linspace(0.06, 0.94, 6)):
        x = AW * (0.10 + 0.80 * t)
        y = AH * 0.50 + np.sin((x - AW * 0.1) / AW * 22) * AH * 0.16
        ang = np.cos((x - AW * 0.1) / AW * 22) * 26
        sub = Image.new("RGBA", (520, 320), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sub, "RGBA")
        b747_top(sd, 260, 160, 380, col=(196, 208, 224))
        sub = sub.rotate(ang, resample=Image.BICUBIC)
        img.paste(sub, (int(x - 260), int(y - 160)), sub)
        d = ImageDraw.Draw(img, "RGBA")
    img = corner_marks(img, "DUTCH ROLL", "YAW ⇄ ROLL")
    return finish(img, seed=seed)


def phugoid_chart(seed=22):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    x0, x1 = AW * 0.12, AW * 0.92
    y0, y1 = AH * 0.24, AH * 0.78
    d.line([x0, y1, x1, y1], fill=(*GRID, 180), width=4)
    d.line([x0, y0, x0, y1], fill=(*GRID, 180), width=4)
    xs = np.linspace(0, 1, 400)
    ys = 0.5 + 0.36 * np.sin(xs * 11) * np.exp(-xs * 0.25)
    pts = [(x0 + (x1 - x0) * x, y1 - (y1 - y0) * y) for x, y in zip(xs, ys)]
    d.line(pts, fill=(*AMB, 220), width=7)
    for lab, fy in (("24,000 ft", 0.86), ("22,000 ft", 0.62), ("10,000 ft", 0.22)):
        y = y1 - (y1 - y0) * fy
        d.line([x0, y, x1, y], fill=(*GRID, 70), width=2)
        d.text((x0 - 22, y), lab, font=font(30, "bold"), fill=(*GRID, 180), anchor="rm")
    d.text((x1, y1 + 46), "TIME →", font=font(30, "bold"), fill=(*GRID, 180), anchor="ra")
    img = corner_marks(img, "PHUGOID / 長周期の上下動", "ALT")
    return finish(img, seed=seed)


def thrust_control(seed=23):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    b747_top(d, AW * 0.48, AH * 0.48, AW * 0.56, col=(32, 40, 54))
    u = (AW * 0.56) / 100.0
    cx, cy = AW * 0.48, AH * 0.48
    for s, mag, col in ((1, 1.0, AMB), (-1, 0.45, (110, 170, 200))):
        for k in (0.62, 0.86):
            ex = cx - 14 * u
            ey = cy + s * k * 40 * u
            d.rounded_rectangle([ex - 6 * u, ey - 3 * u, ex + 6 * u, ey + 3 * u],
                                radius=2.4 * u, fill=(*col, 220))
            L = 150 * mag
            d.line([ex - 8 * u, ey, ex - 8 * u - L, ey], fill=(*col, 210), width=10)
            d.polygon([(ex - 8 * u - L - 40, ey), (ex - 8 * u - L, ey - 22),
                       (ex - 8 * u - L, ey + 22)], fill=(*col, 210))
    d.text((AW * 0.80, AH * 0.30), "左右の推力差で\n機首方向を制御", font=font(46, "bold"),
           fill=(*LINE, 230), anchor="mm", align="center")
    img = corner_marks(img, "DIFFERENTIAL THRUST", "ENG 1-4")
    return finish(img, seed=seed)


def gear_flaps(seed=24):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    b747_side(d, AW * 0.5, AH * 0.46, AW * 0.58, col=(36, 44, 58),
              outline=(140, 186, 210), gear=True, flaps=True, no_tail=True)
    img = corner_marks(img, "GEAR DOWN / FLAPS", "MANUAL CONTROL ATTEMPT")
    return finish(img, seed=seed)


def clock_32min(seed=25):
    img = board(seed, glow=(AW * 0.5, AH * 0.5, AW * 0.4))
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy, r = AW * 0.5, AH * 0.50, AH * 0.30
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(*GRID, 150), width=6)
    for i in range(60):
        a = i / 60 * 6.283
        rr = r * (0.90 if i % 5 else 0.84)
        d.line([cx + np.sin(a) * rr, cy - np.cos(a) * rr,
                cx + np.sin(a) * r * 0.97, cy - np.cos(a) * r * 0.97],
               fill=(*GRID, 120 if i % 5 else 200), width=3 if i % 5 else 5)
    d.arc([cx - r * 0.72, cy - r * 0.72, cx + r * 0.72, cy + r * 0.72],
          -90, -90 + 360 * 32 / 60, fill=(*AMB, 220), width=26)
    return finish(img, seed=seed)


def flight_map(seed=26):
    """Kanto map: Haneda → planned Osaka course → actual meander → Osutaka."""
    img = board(seed, gstep=120)
    d = ImageDraw.Draw(img, "RGBA")
    # coast + land mass (abstract)
    land = [(AW * 0.06, AH * 0.20), (AW * 0.40, AH * 0.14), (AW * 0.66, AH * 0.24),
            (AW * 0.82, AH * 0.42), (AW * 0.72, AH * 0.66), (AW * 0.46, AH * 0.80),
            (AW * 0.20, AH * 0.74), (AW * 0.08, AH * 0.52)]
    d.polygon(land, fill=(24, 34, 48, 255))
    d.line(land + [land[0]], fill=(*GRID, 120), width=3)
    # mountains
    for mx, my, ms in ((0.30, 0.30, 1.4), (0.38, 0.36, 1.0), (0.24, 0.38, 0.9)):
        x, y = AW * mx, AH * my
        d.polygon([(x - 70 * ms, y + 40 * ms), (x, y - 46 * ms), (x + 70 * ms, y + 40 * ms)],
                  fill=(46, 58, 74, 255))
    # route
    hnd = (AW * 0.70, AH * 0.52)
    route = [hnd, (AW * 0.68, AH * 0.62), (AW * 0.60, AH * 0.66), (AW * 0.52, AH * 0.60),
             (AW * 0.50, AH * 0.50), (AW * 0.44, AH * 0.44), (AW * 0.40, AH * 0.36),
             (AW * 0.33, AH * 0.33)]
    d.line(route, fill=(*AMB, 235), width=7, joint="curve")
    for x in np.arange(0, 1.01, 0.02):  # planned course, dashed
        p0 = (hnd[0] + (AW * 0.16 - hnd[0]) * x, hnd[1] + (AH * 0.70 - hnd[1]) * x)
        if int(x * 50) % 2 == 0:
            d.line([p0, (p0[0] - AW * 0.008, p0[1] + AH * 0.007)],
                   fill=(*GRID, 150), width=4)
    for (px, py), lab, col in ((hnd, "羽田", LINE), ((AW * 0.33, AH * 0.33), "御巣鷹の尾根", RED)):
        d.ellipse([px - 16, py - 16, px + 16, py + 16], fill=(*col, 255))
        for rr, aa in ((44, 120), (74, 60)):
            d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=(*col, aa), width=4)
        d.text((px + 56, py - 8), lab, font=font(46, "black"), fill=(*col, 240), anchor="lm")
    d.text((AW * 0.14, AH * 0.72), "大阪(伊丹)へ", font=font(38, "bold"),
           fill=(*GRID, 190), anchor="lm")
    img = corner_marks(img, "FLIGHT PATH", "18:12 → 18:56")
    return finish(img, seed=seed)


def ridge_night(seed=27):
    """Osutaka ridge at night — restrained, no wreckage."""
    img = B.new_canvas((16, 22, 34), (8, 11, 18))
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    for depth, (yb, col) in enumerate(((0.52, (22, 30, 44)), (0.62, (15, 21, 32)),
                                       (0.74, (10, 14, 22)))):
        pts = [(0, AH * yb)]
        x = 0
        while x < AW:
            x += rng.uniform(180, 340)
            pts.append((x, AH * (yb - rng.uniform(0.05, 0.15))))
        pts += [(AW, AH * yb), (AW, AH), (0, AH)]
        d.polygon(pts, fill=col)
    for _ in range(90):
        d.point([rng.uniform(0, AW), rng.uniform(0, AH * 0.45)], fill=(150, 165, 190))
    img = B.fog_bands(img, seed, 0.35, (40, 54, 74), y0=0.5)
    img = B.add_glow(img, AW * 0.5, AH * 0.30, AW * 0.5, (28, 40, 60), 0.5)
    return finish(img, seed=seed, vig=0.55)


def descent_gauge(seed=28):
    img = board(seed, glow=(AW * 0.5, AH * 0.5, AW * 0.4))
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy, r = AW * 0.32, AH * 0.50, AH * 0.30
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(*GRID, 160), width=7)
    for i in range(21):
        a = -2.4 + i * 4.8 / 20
        d.line([cx + np.sin(a) * r * 0.82, cy - np.cos(a) * r * 0.82,
                cx + np.sin(a) * r * 0.95, cy - np.cos(a) * r * 0.95],
               fill=(*GRID, 200), width=4)
    a = 1.9
    d.line([cx, cy, cx + np.sin(a) * r * 0.76, cy - np.cos(a) * r * 0.76],
           fill=(*RED, 245), width=12)
    d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=(*RED, 245))
    d.text((cx, cy + r * 0.45), "DESCENT", font=font(34, "bold"), fill=(*GRID, 200),
           anchor="mm")
    img = corner_marks(img, "VERTICAL SPEED", "ft/min")
    return finish(img, seed=seed)


def casualty_board(seed=29):
    img = board(seed, glow=(AW * 0.5, AH * 0.5, AW * 0.5))
    d = ImageDraw.Draw(img, "RGBA")
    cols, rows = 38, 14
    x0, y0 = AW * 0.14, AH * 0.30
    gx = (AW * 0.72) / cols
    gy = (AH * 0.42) / rows
    n = 0
    for r in range(rows):
        for c in range(cols):
            if n >= 524:
                break
            x, y = x0 + c * gx, y0 + r * gy
            col = (*LINE, 235) if n >= 520 else (*STEEL, 70)
            d.ellipse([x, y, x + gx * 0.42, y + gx * 0.42], fill=col)
            n += 1
    return finish(img, seed=seed)


def report_doc(seed=30, title="航空事故調査報告書", year="1987", lines=13, seal=True):
    img = board(seed, grid=False)
    d = ImageDraw.Draw(img, "RGBA")
    px, py = AW * 0.20, AH * 0.10
    pw, ph = AW * 0.60, AH * 0.84
    d.rectangle([px + 16, py + 18, px + pw + 16, py + ph + 18], fill=(0, 0, 0, 120))
    d.rectangle([px, py, px + pw, py + ph], fill=(*PAPER, 255))
    d.rectangle([px, py, px + pw, py + ph], outline=(150, 146, 134, 255), width=4)
    d.text((px + pw / 2, py + ph * 0.10), title, font=font(66, "black"),
           fill=(38, 40, 44), anchor="mm")
    d.line([px + pw * 0.16, py + ph * 0.15, px + pw * 0.84, py + ph * 0.15],
           fill=(90, 92, 96), width=4)
    d.text((px + pw / 2, py + ph * 0.19), year, font=font(40, "bold"),
           fill=(88, 90, 96), anchor="mm")
    rng = np.random.default_rng(seed)
    for i in range(lines):
        y = py + ph * (0.26 + i * 0.048)
        w = pw * rng.uniform(0.52, 0.80)
        d.rectangle([px + pw * 0.10, y, px + pw * 0.10 + w, y + 12],
                    fill=(112, 114, 120, 210))
    if seal:
        sx, sy = px + pw * 0.76, py + ph * 0.82
        d.ellipse([sx - 90, sy - 90, sx + 90, sy + 90], outline=(170, 60, 58, 220), width=8)
        d.text((sx, sy), "公表", font=font(56, "black"), fill=(170, 60, 58, 220),
               anchor="mm")
    return finish(img, seed=seed, vig=0.5)


def tailstrike_1978(seed=31):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    d.line([0, AH * 0.74, AW, AH * 0.74], fill=(*GRID, 170), width=6)
    sub = Image.new("RGBA", (int(AW * 0.8), int(AH * 0.6)), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sub, "RGBA")
    b747_side(sd, sub.width * 0.5, sub.height * 0.5, AW * 0.52, col=(36, 44, 58),
              outline=(140, 186, 210), gear=True)
    sub = sub.rotate(-11, resample=Image.BICUBIC, center=(sub.width * 0.5, sub.height * 0.5))
    img.paste(sub, (int(AW * 0.10), int(AH * 0.16)), sub)
    d = ImageDraw.Draw(img, "RGBA")
    tx, ty = AW * 0.245, AH * 0.70
    for rr, aa in ((60, 220), (110, 120), (170, 60)):
        d.ellipse([tx - rr, ty - rr, tx + rr, ty + rr], outline=(*RED, aa), width=6)
    img = B.add_glow(img, tx, ty, 260, (120, 30, 34), 0.6)
    img = corner_marks(img, "1978 / 大阪国際空港", "TAIL STRIKE")
    return finish(img, seed=seed)


def bulkhead_location(seed=32):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = AW * 0.48, AH * 0.46
    L = AW * 0.70
    b747_side(d, cx, cy, L, col=(28, 36, 48), outline=(120, 170, 200))
    u = L / 100.0
    bx = cx - 33 * u
    d.line([bx, cy - 8 * u, bx, cy + 7 * u], fill=(*AMB, 245), width=10)
    d.arc([bx - 9 * u, cy - 8 * u, bx + 9 * u, cy + 7 * u], 270, 90,
          fill=(*AMB, 245), width=10)
    for rr, aa in ((150, 130), (240, 70)):
        d.ellipse([bx - rr, cy - rr * 0.8, bx + rr, cy + rr * 0.8],
                  outline=(*AMB, aa), width=5)
    dim_line(d, bx, cy + 16 * u, cx + 48 * u, cy + 16 * u, "与圧される客室", LINE, 34)
    dim_line(d, cx - 55 * u, cy + 22 * u, bx, cy + 22 * u, "非与圧の機体後部", STEEL, 34)
    img = corner_marks(img, "後部圧力隔壁の位置", "SECTION 48")
    return finish(img, seed=seed)


def bulkhead_front(seed=33, cracked=False, burst=False):
    img = board(seed, glow=(AW * 0.5, AH * 0.5, AW * 0.44))
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy, r = AW * 0.5, AH * 0.50, AH * 0.36
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(26, 36, 50, 255),
              outline=(*LINE, 220), width=7)
    for k in (0.78, 0.56, 0.34):
        d.ellipse([cx - r * k, cy - r * k, cx + r * k, cy + r * k],
                  outline=(*LINE, 120), width=4)
    for a in np.linspace(0, 6.283, 19)[:-1]:
        d.line([cx + np.cos(a) * r * 0.12, cy + np.sin(a) * r * 0.12,
                cx + np.cos(a) * r, cy + np.sin(a) * r], fill=(*LINE, 90), width=3)
    # rivet rows
    for k in (0.34, 0.56, 0.78, 0.97):
        for a in np.linspace(0, 6.283, 46)[:-1]:
            d.ellipse([cx + np.cos(a) * r * k - 5, cy + np.sin(a) * r * k - 5,
                       cx + np.cos(a) * r * k + 5, cy + np.sin(a) * r * k + 5],
                      fill=(*LINE, 150))
    if cracked or burst:
        a0 = -0.35
        pts = [(cx + np.cos(a0 + t * 1.5) * r * (0.55 + 0.02 * np.sin(t * 18)),
                cy + np.sin(a0 + t * 1.5) * r * (0.55 + 0.02 * np.sin(t * 18)))
               for t in np.linspace(0, 1, 60)]
        d.line(pts, fill=(*RED, 245), width=9)
        img = B.add_glow(img, pts[30][0], pts[30][1], 260, (120, 28, 32), 0.55)
        d = ImageDraw.Draw(img, "RGBA")
    if burst:
        for a in np.linspace(-0.6, 1.4, 9):
            d.line([cx + np.cos(a) * r * 0.55, cy + np.sin(a) * r * 0.55,
                    cx + np.cos(a) * r * 1.5, cy + np.sin(a) * r * 1.5],
                   fill=(*RED, 150), width=6)
        img = B.add_glow(img, cx, cy, r * 1.6, (130, 34, 36), 0.7)
    img = corner_marks(img, "後部圧力隔壁(正面)", "AFT PRESSURE BULKHEAD")
    return finish(img, seed=seed)


def bulkhead_intact(seed=33):
    return bulkhead_front(seed)


def boeing_repair_scene(seed=83):
    """Hangar repair bay — technicians as distant silhouettes, no faces."""
    img = board(seed, grid=False, glow=(AW * 0.5, AH * 0.42, AW * 0.45))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, AH * 0.74, AW, AH], fill=(20, 25, 34))
    # hangar arch ribs
    for i in range(7):
        k = 1 - i * 0.11
        d.arc([AW * (0.5 - 0.46 * k), AH * (0.10 + 0.05 * i),
               AW * (0.5 + 0.46 * k), AH * (1.26 - 0.04 * i)],
              180, 360, fill=(*GRID, int(120 - i * 12)), width=8)
    # tail section on jacks
    cx, cy = AW * 0.52, AH * 0.52
    u = AW * 0.42 / 100.0
    d.polygon([(cx - 46 * u, cy + 6 * u), (cx - 30 * u, cy - 6 * u),
               (cx + 40 * u, cy - 5 * u), (cx + 46 * u, cy + 2 * u),
               (cx + 40 * u, cy + 8 * u), (cx - 40 * u, cy + 9 * u)],
              fill=(48, 58, 74, 255))
    d.polygon([(cx - 30 * u, cy - 6 * u), (cx - 40 * u, cy - 30 * u),
               (cx - 48 * u, cy - 30 * u), (cx - 46 * u, cy + 6 * u)],
              fill=(42, 52, 66, 255))
    for jx in (-30, 0, 30):
        d.line([cx + jx * u, cy + 9 * u, cx + jx * u, cy + 22 * u],
               fill=(*STEEL, 220), width=10)
    # work platform + two distant figures
    d.rectangle([cx - 52 * u, cy + 2 * u, cx - 24 * u, cy + 4 * u], fill=(*STEEL, 235))
    for fx_, s in ((-46, 0.9), (-34, 1.0)):
        x = cx + fx_ * u
        y = cy + 2 * u
        d.ellipse([x - 9 * s, y - 34 * s, x + 9 * s, y - 16 * s], fill=(14, 18, 24, 255))
        d.polygon([(x - 12 * s, y), (x - 8 * s, y - 18 * s), (x + 8 * s, y - 18 * s),
                   (x + 12 * s, y)], fill=(14, 18, 24, 255))
    # work light pools
    for lx in (0.30, 0.66):
        img = B.add_glow(img, AW * lx, AH * 0.40, AW * 0.16, (150, 130, 80), 0.45)
    d = ImageDraw.Draw(img, "RGBA")
    img = corner_marks(img, "1978 / 修理作業", "SECTION 48 REPAIR")
    return finish(img, seed=seed, vig=0.5)


def bulkhead_cracked(seed=34):
    return bulkhead_front(seed, cracked=True)


def bulkhead_burst(seed=35):
    return bulkhead_front(seed, burst=True)


def pressure_load(seed=36):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    cx = AW * 0.62
    d.line([cx, AH * 0.12, cx, AH * 0.88], fill=(*LINE, 230), width=12)
    d.arc([cx - 90, AH * 0.12, cx + 90, AH * 0.88], 270, 90, fill=(*LINE, 230), width=12)
    for y in np.linspace(AH * 0.18, AH * 0.82, 11):
        d.line([cx - 420, y, cx - 90, y], fill=(*AMB, 200), width=8)
        d.polygon([(cx - 66, y), (cx - 116, y - 22), (cx - 116, y + 22)],
                  fill=(*AMB, 220))
    d.text((AW * 0.20, AH * 0.24), "客室側\n(与圧)", font=font(52, "black"),
           fill=(*AMB, 235), anchor="mm", align="center")
    d.text((AW * 0.86, AH * 0.24), "機体後部\n(非与圧)", font=font(48, "black"),
           fill=(*STEEL, 220), anchor="mm", align="center")
    img = corner_marks(img, "PRESSURE LOAD", "毎フライト加圧/減圧")
    return finish(img, seed=seed)


def _splice(seed, correct=True):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    x0, x1 = AW * 0.16, AW * 0.84
    ymid = AH * 0.50
    # two bulkhead panels meeting at the joint
    d.rectangle([x0, ymid - 150, AW * 0.5 - 6, ymid + 150], fill=(30, 40, 54, 255),
                outline=(*LINE, 150), width=4)
    d.rectangle([AW * 0.5 + 6, ymid - 150, x1, ymid + 150], fill=(30, 40, 54, 255),
                outline=(*LINE, 150), width=4)
    if correct:
        d.rectangle([AW * 0.30, ymid - 96, AW * 0.70, ymid + 96],
                    fill=(56, 92, 116, 255), outline=(*LINE, 230), width=5)
        for row in (-46, 46):
            for x in np.linspace(AW * 0.325, AW * 0.675, 15):
                d.ellipse([x - 12, ymid + row - 12, x + 12, ymid + row + 12],
                          fill=(*LINE, 245))
        d.text((AW * 0.5, ymid - 210), "接合板 1枚 / リベット2列", font=font(52, "black"),
               fill=(*LINE, 240), anchor="mm")
        d.text((AW * 0.5, ymid + 232), "荷重を2列で分担", font=font(44, "bold"),
               fill=(120, 200, 170, 235), anchor="mm")
    else:
        d.rectangle([AW * 0.30, ymid - 96, AW * 0.495, ymid + 96],
                    fill=(72, 62, 66, 255), outline=(*RED, 230), width=5)
        d.rectangle([AW * 0.505, ymid - 96, AW * 0.70, ymid + 96],
                    fill=(72, 62, 66, 255), outline=(*RED, 230), width=5)
        for x in np.linspace(AW * 0.325, AW * 0.675, 15):
            if abs(x - AW * 0.5) < AW * 0.012:
                continue
            d.ellipse([x - 12, ymid - 58, x + 12, ymid - 34], fill=(*STEEL, 120))
            d.ellipse([x - 12, ymid + 34, x + 12, ymid + 58], fill=(*RED, 245))
        d.text((AW * 0.5, ymid - 210), "接合板 2枚 / 実質1列で荷重", font=font(52, "black"),
               fill=(*RED, 245), anchor="mm")
        d.text((AW * 0.5, ymid + 232), "上列が荷重を受けられない", font=font(44, "bold"),
               fill=(*RED, 225), anchor="mm")
        img = B.add_glow(img, AW * 0.5, ymid, 420, (110, 30, 34), 0.5)
    return finish(img, seed=seed)


def splice_correct(seed=37):
    return _splice(seed, True)


def splice_actual(seed=38):
    return _splice(seed, False)


def splice_compare(seed=39):
    img = Image.new("RGB", (AW, AH))
    a = splice_correct(seed + 1).resize((AW, AH // 2))
    b = splice_actual(seed + 2).resize((AW, AH // 2))
    img.paste(a, (0, 0))
    img.paste(b, (0, AH // 2))
    d = ImageDraw.Draw(img, "RGBA")
    d.line([0, AH // 2, AW, AH // 2], fill=(*LINE, 200), width=6)
    return img


def strength_gauge(seed=40):
    img = board(seed, glow=(AW * 0.5, AH * 0.5, AW * 0.4))
    d = ImageDraw.Draw(img, "RGBA")
    x0, x1 = AW * 0.16, AW * 0.84
    y = AH * 0.52
    d.rounded_rectangle([x0, y - 70, x1, y + 70], radius=18, fill=(24, 32, 44, 255),
                        outline=(*GRID, 160), width=5)
    d.rounded_rectangle([x0, y - 70, x0 + (x1 - x0) * 0.70, y + 70], radius=18,
                        fill=(*RED, 190))
    for t in np.linspace(0, 1, 11):
        x = x0 + (x1 - x0) * t
        d.line([x, y + 74, x, y + 100], fill=(*GRID, 170), width=3)
        d.text((x, y + 138), f"{int(t * 100)}", font=font(30, "bold"),
               fill=(*GRID, 190), anchor="mm")
    d.line([x1, y - 120, x1, y + 70], fill=(*LINE, 200), width=4)
    d.text((x1, y - 150), "本来の強度 100%", font=font(44, "black"),
           fill=(*LINE, 235), anchor="mm")
    img = corner_marks(img, "REPAIRED JOINT STRENGTH", "≒70%")
    return finish(img, seed=seed)


def cycles_counter(seed=41):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    for i in range(340):
        x = AW * 0.10 + (i % 34) * AW * 0.0235
        y = AH * 0.26 + (i // 34) * AH * 0.048
        a = 200 if i < 300 else 90
        d.line([x, y, x + AW * 0.014, y], fill=(*LINE, a), width=5)
    img = corner_marks(img, "PRESSURIZATION CYCLES", "1978 → 1985")
    return finish(img, seed=seed)


def crack_growth(seed=42):
    img = board(seed, glow=(AW * 0.5, AH * 0.52, AW * 0.36))
    d = ImageDraw.Draw(img, "RGBA")
    y = AH * 0.50
    d.rectangle([AW * 0.10, y - 130, AW * 0.90, y + 130], fill=(30, 40, 54, 255),
                outline=(*LINE, 140), width=4)
    for x in np.linspace(AW * 0.13, AW * 0.87, 22):
        d.ellipse([x - 11, y + 60, x + 11, y + 82], fill=(*LINE, 150))
    rng = np.random.default_rng(seed)
    px, py = AW * 0.14, y - 10
    pts = [(px, py)]
    for i in range(40):
        px += (AW * 0.72) / 40
        py += rng.uniform(-16, 16)
        pts.append((px, py))
    for i in range(len(pts) - 1):
        t = i / len(pts)
        d.line([pts[i], pts[i + 1]], fill=(*RED, int(90 + 160 * t)),
               width=int(3 + 9 * t))
    d.text((AW * 0.16, y - 190), "微細な亀裂", font=font(40, "bold"),
           fill=(*STEEL, 220), anchor="lm")
    d.text((AW * 0.86, y - 190), "貫通亀裂へ", font=font(44, "black"),
           fill=(*RED, 240), anchor="rm")
    img = corner_marks(img, "FATIGUE CRACK GROWTH", "疲労亀裂の進展")
    return finish(img, seed=seed)


def hidden_crack(seed=43):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    y = AH * 0.50
    d.rectangle([AW * 0.12, y - 40, AW * 0.88, y + 150], fill=(32, 42, 56, 255),
                outline=(*LINE, 130), width=4)
    d.rectangle([AW * 0.24, y - 130, AW * 0.76, y - 40], fill=(56, 76, 96, 255),
                outline=(*LINE, 170), width=4)
    d.text((AW * 0.5, y - 176), "接合板・シール材", font=font(42, "bold"),
           fill=(*LINE, 220), anchor="mm")
    pts = [(AW * 0.30 + i * AW * 0.02, y - 10 + np.sin(i) * 9) for i in range(22)]
    d.line(pts, fill=(*RED, 235), width=7)
    # magnifier: what the eye can see
    mx, my = AW * 0.74, y - 250
    d.ellipse([mx - 120, my - 120, mx + 120, my + 120], outline=(*STEEL, 220), width=12)
    d.line([mx + 86, my + 86, mx + 200, my + 200], fill=(*STEEL, 220), width=18)
    d.text((AW * 0.5, y + 230), "外からは見つけにくい", font=font(52, "black"),
           fill=(*AMB, 235), anchor="mm")
    img = corner_marks(img, "VISUAL INSPECTION", "困難")
    return finish(img, seed=seed)


def air_blast(seed=44):
    img = board(seed, grid=False)
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = AW * 0.46, AH * 0.48
    b747_side(d, cx, cy, AW * 0.66, col=(28, 36, 48), outline=(120, 170, 200),
              no_tail=True)
    u = (AW * 0.66) / 100.0
    bx = cx - 33 * u
    for i, k in enumerate(np.linspace(0.2, 1.0, 7)):
        y = cy - 8 * u + i * 2.6 * u
        L = 90 + 220 * k
        d.line([bx, y, bx - L, y], fill=(*RED, int(90 + 120 * k)), width=int(6 + 6 * k))
        d.polygon([(bx - L - 34, y), (bx - L, y - 16), (bx - L, y + 16)],
                  fill=(*RED, int(90 + 120 * k)))
    img = B.add_glow(img, bx - 200, cy, 360, (110, 30, 34), 0.6)
    img = corner_marks(img, "DECOMPRESSION FLOW", "客室 → 機体後部")
    return finish(img, seed=seed)


def chain_diagram(seed=45):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    steps = ["1978\n不適切な修理", "疲労亀裂の\n進展", "圧力隔壁\n破壊", "垂直尾翼\n喪失",
             "油圧4系統\n喪失", "制御不能"]
    n = len(steps)
    bw = AW * 0.128
    for i, s in enumerate(steps):
        x = AW * (0.075 + i * 0.152)
        y = AH * 0.50
        col = RED if i in (0, 5) else LINE
        d.rounded_rectangle([x, y - 120, x + bw, y + 120], radius=16,
                            fill=(22, 30, 42, 255), outline=(*col, 220), width=5)
        d.text((x + bw / 2, y), s, font=font(36, "black"), fill=(*col, 240),
               anchor="mm", align="center")
        if i < n - 1:
            ax = x + bw + AW * 0.006
            d.line([ax, y, ax + AW * 0.011, y], fill=(*GRID, 200), width=6)
            d.polygon([(ax + AW * 0.018, y), (ax + AW * 0.010, y - 16),
                       (ax + AW * 0.010, y + 16)], fill=(*GRID, 200))
    img = corner_marks(img, "OFFICIAL CAUSAL CHAIN", "事故調査報告書")
    return finish(img, seed=seed)


def evidence_bulkhead(seed=46):
    """Recovered bulkhead fragment on an evidence table."""
    img = board(seed, grid=False, glow=(AW * 0.5, AH * 0.55, AW * 0.4))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, AH * 0.62, AW, AH], fill=(24, 28, 36))
    cx, cy = AW * 0.5, AH * 0.48
    rng = np.random.default_rng(seed)
    pts = [(cx + np.cos(a) * (AW * 0.20 + rng.uniform(-60, 60)),
            cy + np.sin(a) * (AH * 0.22 + rng.uniform(-50, 50)))
           for a in np.linspace(0, 6.283, 13)]
    d.polygon(pts, fill=(64, 74, 88, 255))
    d.line(pts + [pts[0]], fill=(*LINE, 200), width=5)
    for k in (0.5, 0.75):
        d.arc([cx - AW * 0.2 * k, cy - AH * 0.22 * k, cx + AW * 0.2 * k, cy + AH * 0.22 * k],
              0, 360, fill=(*LINE, 90), width=3)
    fr = [(cx - AW * 0.16, cy + AH * 0.04), (cx + AW * 0.17, cy - AH * 0.02)]
    d.line([fr[0], (cx - 40, cy + 30), (cx + 60, cy - 10), fr[1]],
           fill=(*RED, 235), width=9)
    d.text((cx, cy + AH * 0.29), "破断面に残された疲労亀裂", font=font(50, "black"),
           fill=(*AMB, 240), anchor="mm")
    img = corner_marks(img, "RECOVERED EVIDENCE", "回収された圧力隔壁")
    return finish(img, seed=seed)


def section_card(seed, jp, en, accent=RED):
    img = board(seed, glow=(AW * 0.5, AH * 0.5, AW * 0.5))
    d = ImageDraw.Draw(img, "RGBA")
    d.line([AW * 0.14, AH * 0.62, AW * 0.86, AH * 0.62], fill=(*accent, 200), width=6)
    d.text((AW * 0.5, AH * 0.75), en, font=font(46, "bold"), fill=(*GRID, 180),
           anchor="mm")
    return finish(img, seed=seed, vig=0.55)


def card_why(seed=47):
    return section_card(seed, "", "WHY DID IT CRASH ?", AMB)


def card_conspiracy(seed=48):
    return section_card(seed, "", "THE CONSPIRACY NARRATIVE", RED)


def card_verify(seed=49):
    return section_card(seed, "", "EXAMINING THE CLAIMS", LINE)


def card_conclusion(seed=50):
    return section_card(seed, "", "THE MOST RATIONAL CONCLUSION", AMB)


def card_hole(seed=51):
    return section_card(seed, "", "ONE QUESTION REMAINS", RED)


def news_chaos(seed=52):
    """Conflicting early reports — abstract newspaper/TV fragments."""
    img = board(seed, grid=False)
    rng = np.random.default_rng(seed)
    for i in range(9):
        w = int(AW * rng.uniform(0.20, 0.30))
        h = int(AH * rng.uniform(0.20, 0.30))
        card = Image.new("RGBA", (w, h), (*PAPER, 240))
        cd = ImageDraw.Draw(card, "RGBA")
        cd.rectangle([0, 0, w, h * 0.16], fill=(60, 66, 76, 255))
        for k in range(int(h * 0.7 // 28)):
            cd.rectangle([w * 0.08, h * 0.24 + k * 28, w * 0.08 + w * rng.uniform(0.3, 0.84),
                          h * 0.24 + k * 28 + 10], fill=(110, 112, 118, 220))
        card = card.rotate(rng.uniform(-14, 14), expand=True)
        img.paste(card, (int(rng.uniform(-40, AW - w)), int(rng.uniform(-30, AH - h))), card)
    img = B.add_glow(img, AW * 0.5, AH * 0.5, AW * 0.5, (20, 40, 60), 0.5)
    return finish(img, seed=seed, vig=0.55)


def location_confusion(seed=53):
    img = board(seed, gstep=120)
    d = ImageDraw.Draw(img, "RGBA")
    d.polygon([(AW * 0.14, AH * 0.22), (AW * 0.50, AH * 0.18), (AW * 0.56, AH * 0.56),
               (AW * 0.20, AH * 0.66)], fill=(26, 38, 52, 255), outline=(*GRID, 150))
    d.polygon([(AW * 0.50, AH * 0.18), (AW * 0.86, AH * 0.28), (AW * 0.82, AH * 0.68),
               (AW * 0.56, AH * 0.56)], fill=(30, 42, 58, 255), outline=(*GRID, 150))
    d.text((AW * 0.32, AH * 0.40), "長野県側?", font=font(64, "black"),
           fill=(*LINE, 200), anchor="mm")
    d.text((AW * 0.68, AH * 0.42), "群馬県側?", font=font(64, "black"),
           fill=(*LINE, 200), anchor="mm")
    for px, py in ((AW * 0.42, AH * 0.44), (AW * 0.60, AH * 0.38), (AW * 0.55, AH * 0.50)):
        for rr, aa in ((40, 200), (80, 90)):
            d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=(*RED, aa), width=5)
    img = corner_marks(img, "位置情報の混乱", "1985.08.12 19:00-")
    return finish(img, seed=seed)


def night_search(seed=54):
    img = ridge_night(seed + 3)
    d = ImageDraw.Draw(img, "RGBA")
    hx, hy = AW * 0.62, AH * 0.26
    d.ellipse([hx - 70, hy - 22, hx + 70, hy + 22], fill=(30, 36, 46, 255))
    d.line([hx - 130, hy - 40, hx + 130, hy - 40], fill=(*STEEL, 220), width=7)
    d.line([hx, hy - 40, hx, hy - 20], fill=(*STEEL, 220), width=7)
    d.line([hx - 60, hy + 16, hx - 140, hy + 40], fill=(*STEEL, 200), width=6)
    img = B.light_cone(img, (hx, hy + 20), (AW * 0.34, AH * 0.86), (AW * 0.70, AH * 0.92),
                       (150, 160, 140), alpha=70, blur=70)
    img = B.add_glow(img, AW * 0.42, AH * 0.62, 200, (150, 90, 40), 0.5)
    return finish(img, seed=seed, vig=0.55)


def dawn_rescue(seed=55):
    img = B.new_canvas((88, 92, 108), (30, 36, 48))
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    for depth, (yb, col) in enumerate(((0.54, (52, 60, 74)), (0.66, (34, 42, 54)),
                                       (0.78, (22, 28, 38)))):
        pts = [(0, AH * yb)]
        x = 0
        while x < AW:
            x += rng.uniform(200, 360)
            pts.append((x, AH * (yb - rng.uniform(0.05, 0.14))))
        pts += [(AW, AH * yb), (AW, AH), (0, AH)]
        d.polygon(pts, fill=col)
    img = B.fog_bands(img, seed, 0.5, (120, 128, 140), y0=0.42)
    img = B.add_glow(img, AW * 0.66, AH * 0.30, AW * 0.4, (150, 130, 110), 0.5)
    return finish(img, seed=seed, sat=0.7, vig=0.45)


def claim_card(seed, text, tag="説"):
    img = board(seed, glow=(AW * 0.5, AH * 0.5, AW * 0.42))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([AW * 0.12, AH * 0.34, AW * 0.88, AH * 0.66], radius=24,
                        fill=(30, 22, 26, 210), outline=(*RED, 190), width=6)
    d.rounded_rectangle([AW * 0.12, AH * 0.34, AW * 0.20, AH * 0.66], radius=0,
                        fill=(*RED, 210))
    d.text((AW * 0.16, AH * 0.50), tag, font=font(64, "black"), fill=(240, 232, 232),
           anchor="mm")
    return finish(img, seed=seed, vig=0.5)


def claim_missile(seed=56):
    return claim_card(seed, "", "説")


def claim_drone(seed=57):
    return claim_card(seed, "", "説")


def claim_f4(seed=58):
    return claim_card(seed, "", "説")


def claim_coverup(seed=59):
    return claim_card(seed, "", "説")


def orange_object(seed=60):
    """A grainy 'photograph' with an unidentifiable orange smear."""
    img = board(seed, grid=False)
    ph = Image.new("RGB", (int(AW * 0.62), int(AH * 0.62)), (56, 62, 74))
    pd = ImageDraw.Draw(ph, "RGBA")
    pd.rectangle([0, ph.height * 0.62, ph.width, ph.height], fill=(38, 44, 54))
    b747_side(pd, ph.width * 0.44, ph.height * 0.42, ph.width * 0.5, col=(96, 106, 122))
    n = np.random.default_rng(seed).normal(0, 26, (ph.height // 2, ph.width // 2, 3))
    n = Image.fromarray(np.clip(n + 128, 0, 255).astype(np.uint8)).resize(ph.size)
    ph = ImageChops.add(ph, ImageChops.subtract(n, Image.new("RGB", ph.size, (128,) * 3)))
    ph = ph.filter(ImageFilter.GaussianBlur(2.2))
    ox, oy = ph.width * 0.72, ph.height * 0.40
    glow = Image.new("RGB", ph.size, (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([ox - 46, oy - 30, ox + 46, oy + 30], fill=(230, 130, 40))
    glow = glow.filter(ImageFilter.GaussianBlur(26))
    ph = ImageChops.screen(ph, glow)
    img.paste(ph, (int(AW * 0.19), int(AH * 0.16)))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([AW * 0.19, AH * 0.16, AW * 0.19 + ph.width, AH * 0.16 + ph.height],
                outline=(*LINE, 150), width=5)
    bx, by = AW * 0.19 + ox, AH * 0.16 + oy
    d.rectangle([bx - 110, by - 90, bx + 110, by + 90], outline=(*AMB, 235), width=5)
    d.text((bx + 130, by - 110), "?", font=font(90, "black"), fill=(*AMB, 240), anchor="lm")
    return finish(img, seed=seed, vig=0.5)


def abnormal_force_doc(seed=61):
    img = report_doc(seed, "事故調査報告書 付録", "1987", lines=11, seal=False)
    d = ImageDraw.Draw(img, "RGBA")
    hx, hy = AW * 0.36, AH * 0.52
    d.rectangle([hx, hy - 32, hx + AW * 0.28, hy + 32], fill=(*AMB, 90))
    d.rectangle([hx, hy - 32, hx + AW * 0.28, hy + 32], outline=(*AMB, 235), width=4)
    d.text((hx + AW * 0.14, hy), "異常外力", font=font(52, "black"),
           fill=(60, 40, 12), anchor="mm")
    return img


def fdr_device(seed=62):
    img = board(seed, glow=(AW * 0.5, AH * 0.52, AW * 0.4))
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = AW * 0.46, AH * 0.52
    d.rounded_rectangle([cx - 420, cy - 200, cx + 420, cy + 200], radius=26,
                        fill=(180, 96, 30, 255), outline=(220, 140, 60, 255), width=8)
    for x in np.linspace(cx - 380, cx + 380, 14):
        d.line([x, cy - 200, x, cy + 200], fill=(150, 76, 22, 180), width=6)
    d.rounded_rectangle([cx - 300, cy - 90, cx + 60, cy + 90], radius=12,
                        fill=(60, 44, 30, 255))
    d.text((cx - 120, cy), "FLIGHT\nRECORDER", font=font(48, "black"),
           fill=(240, 226, 200, 240), anchor="mm", align="center")
    img = B.add_glow(img, cx, cy, 520, (120, 62, 20), 0.5)
    return finish(img, seed=seed)


def fdr_bits(seed=63):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    y0 = AH * 0.24
    for r in range(9):
        for c in range(52):
            x = AW * 0.10 + c * AW * 0.0155
            y = y0 + r * AH * 0.055
            v = rng.random()
            if v < 0.12:
                col = (*RED, 200)
            elif v < 0.55:
                col = (*LINE, 210)
            else:
                col = (*GRID, 90)
            d.rectangle([x, y, x + AW * 0.010, y + AH * 0.030], fill=col)
    # magnified read head
    d.rectangle([AW * 0.30, AH * 0.68, AW * 0.70, AH * 0.86], fill=(18, 24, 34, 235),
                outline=(*AMB, 220), width=5)
    d.text((AW * 0.5, AH * 0.77), "1 0 1 1 0 0 1 0 1 1 0 1", font=font(56, "bold"),
           fill=(*AMB, 240), anchor="mm")
    img = corner_marks(img, "DAMAGED RECORD / 目視による復元", "BIT BY BIT")
    return finish(img, seed=seed)


def fdr_trace(seed=64):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    x0, x1 = AW * 0.12, AW * 0.92
    ymid = AH * 0.50
    d.line([x0, ymid, x1, ymid], fill=(*GRID, 160), width=4)
    d.line([x0, AH * 0.22, x0, AH * 0.80], fill=(*GRID, 160), width=4)
    xs = np.linspace(0, 1, 500)
    fwd = np.where(xs < 0.36, 0, np.exp(-(xs - 0.38) ** 2 * 900) * 0.9)
    dwn = np.where(xs < 0.44, 0, -np.exp(-(xs - 0.52) ** 2 * 500) * 0.75)
    for series, col, lab in ((fwd, AMB, "前後加速度"), (dwn, (120, 180, 230), "上下加速度")):
        pts = [(x0 + (x1 - x0) * x, ymid - v * AH * 0.24) for x, v in zip(xs, series)]
        d.line(pts, fill=(*col, 230), width=6)
    d.line([x0 + (x1 - x0) * 0.36, AH * 0.22, x0 + (x1 - x0) * 0.36, AH * 0.80],
           fill=(*RED, 180), width=4)
    d.text((x0 + (x1 - x0) * 0.36, AH * 0.185), "異常発生", font=font(38, "black"),
           fill=(*RED, 235), anchor="mm")
    img = corner_marks(img, "FDR / 数秒間の記録", "ACCELERATION")
    return finish(img, seed=seed)


def reaction_physics(seed=65):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = AW * 0.5, AH * 0.48
    b747_side(d, cx, cy, AW * 0.56, col=(28, 36, 48), outline=(120, 170, 200),
              no_tail=True)
    u = (AW * 0.56) / 100.0
    for i in range(5):
        y = cy - 6 * u + i * 3 * u
        d.line([cx - 33 * u, y, cx - 33 * u - 240, y], fill=(*RED, 180), width=8)
        d.polygon([(cx - 33 * u - 280, y), (cx - 33 * u - 244, y - 18),
                   (cx - 33 * u - 244, y + 18)], fill=(*RED, 180))
    d.line([cx + 20 * u, cy - 20 * u, cx + 20 * u + 300, cy - 20 * u],
           fill=(*AMB, 235), width=12)
    d.polygon([(cx + 20 * u + 350, cy - 20 * u), (cx + 20 * u + 300, cy - 20 * u - 26),
               (cx + 20 * u + 300, cy - 20 * u + 26)], fill=(*AMB, 235))
    d.text((cx + 20 * u + 150, cy - 24 * u), "反作用で機体は前方へ", font=font(40, "black"),
           fill=(*AMB, 240), anchor="mm")
    img = corner_marks(img, "REACTION", "空気の噴出 ⇄ 機体")
    return finish(img, seed=seed)


def diet_2025(seed=66):
    img = board(seed, grid=False, glow=(AW * 0.5, AH * 0.45, AW * 0.44))
    d = ImageDraw.Draw(img, "RGBA")
    # chamber: tiered desks + podium silhouette
    for i in range(5):
        t = i / 5
        y = AH * (0.52 + t * 0.11)
        w = AW * (0.30 + t * 0.32)
        d.rounded_rectangle([AW * 0.5 - w / 2, y, AW * 0.5 + w / 2, y + AH * 0.055],
                            radius=10, fill=(38 + i * 4, 44 + i * 4, 56 + i * 5, 255))
    d.rounded_rectangle([AW * 0.44, AH * 0.30, AW * 0.56, AH * 0.52], radius=12,
                        fill=(52, 60, 74, 255))
    d.ellipse([AW * 0.485, AH * 0.24, AW * 0.515, AH * 0.30], fill=(70, 80, 96, 255))
    img = B.add_glow(img, AW * 0.5, AH * 0.30, AW * 0.28, (60, 72, 92), 0.5)
    return finish(img, seed=seed, vig=0.55)


def evidence_convergence(seed=67):
    img = board(seed, glow=(AW * 0.5, AH * 0.5, AW * 0.4))
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = AW * 0.72, AH * 0.50
    items = ["圧力隔壁の疲労破壊", "誤った修理", "垂直尾翼の破壊", "油圧4系統の喪失",
             "FDRの挙動"]
    for i, it in enumerate(items):
        y = AH * (0.22 + i * 0.14)
        d.rounded_rectangle([AW * 0.06, y - 46, AW * 0.42, y + 46], radius=14,
                            fill=(24, 32, 44, 235), outline=(*LINE, 170), width=4)
        d.line([AW * 0.43, y, cx - 130, cy + (y - cy) * 0.18], fill=(*LINE, 130), width=5)
    d.ellipse([cx - 130, cy - 130, cx + 130, cy + 130], fill=(30, 42, 56, 255),
              outline=(*AMB, 230), width=7)
    img = B.add_glow(img, cx, cy, 300, (110, 80, 30), 0.5)
    return finish(img, seed=seed)


def rescue_critique(seed=68):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(4):
        y = AH * (0.26 + i * 0.15)
        d.rounded_rectangle([AW * 0.14, y - 52, AW * 0.86, y + 52], radius=14,
                            fill=(28, 26, 24, 220), outline=(*AMB, 150), width=4)
        d.rectangle([AW * 0.14, y - 52, AW * 0.155, y + 52], fill=(*AMB, 220))
    img = corner_marks(img, "検証すべき問題", "RESCUE DELAY")
    return finish(img, seed=seed)


def gap_diagram(seed=69):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    y = AH * 0.48
    for x, lab, col in ((AW * 0.24, "救助が\n遅れた", LINE),
                        (AW * 0.76, "意図的に\n遅らせた", RED)):
        d.ellipse([x - 210, y - 210, x + 210, y + 210], fill=(24, 32, 44, 235),
                  outline=(*col, 210), width=6)
        d.text((x, y), lab, font=font(56, "black"), fill=(*col, 240), anchor="mm",
               align="center")
    for i in range(9):
        xx = AW * (0.36 + i * 0.032)
        d.line([xx, y, xx + AW * 0.018, y], fill=(*GRID, 150), width=5)
    d.text((AW * 0.5, y - 300), "証拠の距離", font=font(52, "black"),
           fill=(*GRID, 210), anchor="mm")
    return finish(img, seed=seed)


def fuel_fire(seed=70):
    img = ridge_night(seed + 5)
    img = B.add_glow(img, AW * 0.46, AH * 0.60, AW * 0.30, (170, 80, 30), 0.7)
    img = B.add_glow(img, AW * 0.56, AH * 0.62, AW * 0.18, (200, 110, 40), 0.55)
    return finish(img, seed=seed, vig=0.5)


def distrust_diagram(seed=71):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    srcs = ["情報の混乱", "救助の遅れ", "説明不足", "520人という犠牲"]
    for i, s in enumerate(srcs):
        y = AH * (0.24 + i * 0.16)
        d.rounded_rectangle([AW * 0.08, y - 48, AW * 0.36, y + 48], radius=14,
                            fill=(26, 32, 44, 230), outline=(*STEEL, 170), width=4)
        d.line([AW * 0.37, y, AW * 0.52, AH * 0.50], fill=(*STEEL, 120), width=5)
    d.rounded_rectangle([AW * 0.54, AH * 0.36, AW * 0.92, AH * 0.64], radius=20,
                        fill=(38, 24, 28, 235), outline=(*RED, 200), width=6)
    img = B.add_glow(img, AW * 0.73, AH * 0.5, 340, (100, 34, 38), 0.45)
    return finish(img, seed=seed)


def doc_timeline(seed=72):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    y = AH * 0.52
    d.line([AW * 0.08, y, AW * 0.92, y], fill=(*GRID, 190), width=6)
    marks = [("1978", "修理", LINE), ("1985", "事故", RED), ("1987", "報告書", LINE),
             ("2024", "掲載", AMB), ("2026", "削除・謝罪", RED)]
    for i, (yr, lab, col) in enumerate(marks):
        x = AW * (0.12 + i * 0.19)
        d.line([x, y - 26, x, y + 26], fill=(*col, 230), width=6)
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=(*col, 240))
        up = i % 2 == 0
        ly = y - 130 if up else y + 130
        d.line([x, y, x, ly], fill=(*col, 150), width=4)
        d.text((x, ly + (-40 if up else 40)), yr, font=font(52, "black"),
               fill=(*col, 245), anchor="mm")
        d.text((x, ly + (-92 if up else 92)), lab, font=font(36, "bold"),
               fill=(*col, 200), anchor="mm")
    return finish(img, seed=seed)


def report_1987(seed=80):
    return report_doc(seed, "航空事故調査報告書", "1987年 公表", lines=13, seal=True)


def ntsb_doc(seed=81):
    return report_doc(seed, "NTSB 安全勧告", "SAFETY RECOMMENDATION", lines=11,
                      seal=False)


def us_testimony(seed=82):
    return report_doc(seed, "元米軍関係者の証言", "1990年代 報道", lines=9, seal=False)


def boeing_doc(seed=73):
    return report_doc(seed, "安全教育用資料", "2024", lines=10, seal=False)


def deleted_doc(seed=74):
    img = report_doc(seed, "安全教育用資料", "2026", lines=10, seal=False)
    d = ImageDraw.Draw(img, "RGBA")
    d.line([AW * 0.24, AH * 0.28, AW * 0.76, AH * 0.80], fill=(*RED, 220), width=18)
    d.line([AW * 0.76, AH * 0.28, AW * 0.24, AH * 0.80], fill=(*RED, 220), width=18)
    d.rounded_rectangle([AW * 0.30, AH * 0.48, AW * 0.70, AH * 0.60], radius=14,
                        fill=(30, 16, 18, 235), outline=(*RED, 235), width=6)
    d.text((AW * 0.5, AH * 0.54), "削除", font=font(78, "black"), fill=(240, 220, 220),
           anchor="mm")
    return img


def faa_doc(seed=75):
    return report_doc(seed, "FAA 安全資料", "現在も掲載", lines=12, seal=False)


def final_page(seed=76):
    img = board(seed, grid=False, glow=(AW * 0.5, AH * 0.5, AW * 0.5))
    d = ImageDraw.Draw(img, "RGBA")
    px, py = AW * 0.30, AH * 0.14
    pw, ph = AW * 0.40, AH * 0.72
    d.rectangle([px + 14, py + 16, px + pw + 14, py + ph + 16], fill=(0, 0, 0, 130))
    d.rectangle([px, py, px + pw, py + ph], fill=(*PAPER, 250))
    rng = np.random.default_rng(seed)
    for i in range(6):
        yy = py + ph * (0.14 + i * 0.05)
        d.rectangle([px + pw * 0.12, yy, px + pw * 0.12 + pw * rng.uniform(0.4, 0.72), yy + 11],
                    fill=(120, 122, 128, 200))
    d.text((px + pw / 2, py + ph * 0.62), "?", font=font(220, "black"),
           fill=(150, 60, 58, 200), anchor="mm")
    img = B.add_glow(img, AW * 0.5, AH * 0.5, AW * 0.34, (60, 50, 40), 0.4)
    return finish(img, seed=seed, vig=0.55)


def memorial(seed=77):
    img = B.new_canvas((26, 34, 48), (10, 14, 22))
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    pts = [(0, AH * 0.66)]
    x = 0
    while x < AW:
        x += rng.uniform(200, 380)
        pts.append((x, AH * (0.66 - rng.uniform(0.04, 0.12))))
    pts += [(AW, AH * 0.66), (AW, AH), (0, AH)]
    d.polygon(pts, fill=(14, 19, 28))
    for i in range(60):
        x = rng.uniform(AW * 0.1, AW * 0.9)
        y = AH * rng.uniform(0.60, 0.74)
        img = B.add_glow(img, x, y, 44, (200, 150, 70), 0.35)
    img = B.add_glow(img, AW * 0.5, AH * 0.34, AW * 0.5, (40, 56, 78), 0.5)
    img = B.fog_bands(img, seed, 0.3, (50, 64, 86), y0=0.5)
    return finish(img, seed=seed, vig=0.55)


def survivors_card(seed=78):
    img = board(seed, glow=(AW * 0.5, AH * 0.5, AW * 0.44))
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(4):
        x = AW * (0.32 + i * 0.12)
        d.ellipse([x - 44, AH * 0.50 - 44, x + 44, AH * 0.50 + 44], fill=(*LINE, 235))
    return finish(img, seed=seed)


def worst_ranking(seed=79):
    img = board(seed)
    d = ImageDraw.Draw(img, "RGBA")
    bars = [("日本航空123便 (1985)", 1.0, RED), ("事故 B", 0.72, STEEL),
            ("事故 C", 0.63, STEEL), ("事故 D", 0.55, STEEL)]
    for i, (lab, v, col) in enumerate(bars):
        y = AH * (0.30 + i * 0.13)
        w = (AW * 0.52) * v
        d.rounded_rectangle([AW * 0.30, y - 40, AW * 0.30 + w, y + 40], radius=10,
                            fill=(*col, 200))
    img = corner_marks(img, "単独機の航空事故", "世界最悪級")
    return finish(img, seed=seed)


BUILDERS = {n: f for n, f in globals().items()
            if callable(f) and not n.startswith("_") and
            n not in ("font", "finish", "board", "corner_marks", "dim_line",
                      "b747_side", "b747_top", "section_card", "claim_card",
                      "report_doc", "bulkhead_front")}
OVERLAYS = {}
