# -*- coding: utf-8 -*-
"""Low-level drawing primitives for the illustrated horror scenes.

Everything is stylized "dark graphic novel" rendering: silhouette-driven
composition, fog layers, glows, film grade.  Output stills are 2688x1512
(1.4x overscan of 1080p) so the camera can move without upscaling.
"""
import numpy as np
from PIL import (Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter,
                 ImageFont, ImageOps)

from common import AW, AH, FONT_SANS_TTC, FONT_BLACK_TTC, FONT_SERIF_TTC, FONT_REG_TTC

# ---------------------------------------------------------------- fonts
_font_cache = {}


def _jp_index(path):
    for i in range(8):
        try:
            f = ImageFont.truetype(path, 20, index=i)
        except OSError:
            break
        if "JP" in f.getname()[0]:
            return i
    return 0


_JP_IDX = {}


def font(size, weight="black", serif=False):
    path = FONT_SERIF_TTC if serif else (
        FONT_BLACK_TTC if weight == "black" else
        FONT_SANS_TTC if weight == "bold" else FONT_REG_TTC)
    if path not in _JP_IDX:
        _JP_IDX[path] = _jp_index(path)
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size, index=_JP_IDX[path])
    return _font_cache[key]


# ---------------------------------------------------------------- noise / gradients
def vnoise(w, h, scale, seed, octaves=4, persistence=0.55):
    """Fractal value noise in [0,1] (float32 h x w)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw = max(2, int(scale * (2 ** o)))
        gh = max(2, int(gw * h / max(w, 1)))
        g = (rng.random((gh, gw)) * 255).astype(np.uint8)
        up = Image.fromarray(g).resize((w, h), Image.BILINEAR)
        out += np.asarray(up, np.float32) / 255.0 * amp
        tot += amp
        amp *= persistence
    return out / tot


def streaks(w, h, seed, density=18, blur=3):
    """Vertical grime streaks in [0,1]."""
    rng = np.random.default_rng(seed)
    col = rng.random(w).astype(np.float32)
    img = Image.fromarray((np.tile(col, (h, 1)) * 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(img, np.float32) / 255.0
    a = np.clip((a - 0.45) * density / 10.0, 0, 1)
    fade = np.linspace(0.2, 1.0, h, dtype=np.float32)[:, None]
    return a * fade


def grad_v(w, h, top, bot):
    """Vertical RGB gradient image."""
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top = np.array(top, np.float32)[None, None, :]
    bot = np.array(bot, np.float32)[None, None, :]
    arr = top + (bot - top) * t
    return Image.fromarray(np.tile(arr, (1, w, 1)).astype(np.uint8))


def radial(w, h, cx, cy, r, inner=255, outer=0, power=1.6):
    """Radial falloff mask (L)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(r, 1)
    v = np.clip(1 - d, 0, 1) ** power
    return Image.fromarray((outer + (inner - outer) * v).astype(np.uint8))


# ---------------------------------------------------------------- compositing
def new_canvas(top, bot, w=AW, h=AH):
    return grad_v(w, h, top, bot).convert("RGB")


def screen(base, layer):
    return ImageChops.screen(base, layer)


def add_glow(img, cx, cy, r, color, strength=1.0, power=1.8):
    m = radial(img.width, img.height, cx, cy, r, int(255 * min(strength * 1.35, 1)), 0, power)
    lay = Image.new("RGB", img.size, color)
    return ImageChops.screen(img, ImageChops.multiply(lay, Image.merge("RGB", (m, m, m))))


def light_cone(img, apex, p1, p2, color, alpha=90, blur=40):
    """Soft triangular light beam (apex -> far edge p1..p2)."""
    ov = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.polygon([apex, p1, p2], fill=color)
    ov = ov.filter(ImageFilter.GaussianBlur(blur))
    ov = ImageEnhance.Brightness(ov).enhance(alpha / 255.0)
    return ImageChops.screen(img, ov)


def vignette(img, k=0.55, cx=None, cy=None):
    w, h = img.size
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    m = radial(w, h, cx, cy, max(w, h) * 0.72, 255, int(255 * (1 - k)), power=1.3)
    m = ImageOps.invert(m)  # dark at edges
    dark = Image.new("RGB", img.size, (0, 0, 0))
    return Image.composite(dark, img, m)


def halation(img, thresh=190, radius=26, strength=0.55):
    g = ImageOps.grayscale(img)
    m = g.point(lambda v: 255 if v > thresh else 0)
    hi = Image.composite(img, Image.new("RGB", img.size, 0), m)
    hi = hi.filter(ImageFilter.GaussianBlur(radius))
    hi = ImageEnhance.Brightness(hi).enhance(strength)
    return ImageChops.screen(img, hi)


def grade(img, lift=(8, 10, 14), gain=(235, 240, 246), gamma=1.0, sat=0.82):
    """Filmic-ish grade: per-channel lift/gain + saturation."""
    arr = np.asarray(img, np.float32) / 255.0
    if gamma != 1.0:
        arr = arr ** gamma
    lift = np.array(lift, np.float32) / 255.0
    gain = np.array(gain, np.float32) / 255.0
    arr = lift + arr * (gain - lift)
    out = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    if sat != 1.0:
        out = ImageEnhance.Color(out).enhance(sat)
    return out


def dirt(img, seed, amount=0.06):
    n = vnoise(img.width // 2, img.height // 2, 90, seed, octaves=2)
    n = Image.fromarray((n * 255).astype(np.uint8)).resize(img.size)
    n = n.point(lambda v: 255 if v > 236 else 0).filter(ImageFilter.GaussianBlur(0.6))
    spec = Image.new("RGB", img.size, (190, 188, 180))
    m = n.point(lambda v: int(v * amount))
    return Image.composite(spec, img, m)


def fog_bands(img, seed, strength=0.5, color=(120, 135, 145), y0=0.45):
    """Layered horizontal fog rising from y0."""
    w, h = img.size
    n = vnoise(w // 3, h // 3, 7, seed, octaves=4)
    n = Image.fromarray((n * 255).astype(np.uint8)).resize((w, h)).filter(
        ImageFilter.GaussianBlur(12))
    band = np.linspace(0, 1, h, dtype=np.float32)
    band = np.clip((band - y0) / max(1e-4, (1 - y0)), 0, 1) ** 1.4
    m = (np.asarray(n, np.float32) / 255.0) * band[:, None]
    m = Image.fromarray((m * 255 * strength).astype(np.uint8))
    fogc = Image.new("RGB", img.size, color)
    return Image.composite(fogc, img, m)


def mist_top(img, strength=0.35, color=(90, 105, 118)):
    w, h = img.size
    band = np.clip(np.linspace(1, -0.6, h, dtype=np.float32), 0, 1) ** 1.8
    m = Image.fromarray((band[:, None] * 255 * strength).astype(np.uint8) *
                        np.ones((1, w), np.uint8))
    return Image.composite(Image.new("RGB", img.size, color), img, m)


# ---------------------------------------------------------------- architecture
def draw_building(img, x0, y0, x1, y1, pal, seed, floors=4, bays=8,
                  lit=(), broken_p=0.25, sign=None, roofbox=True, glass=(26, 34, 44)):
    """Parametric decayed facade with a window grid.  Returns img (RGB)."""
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(img, "RGBA")
    wall = pal["wall"]
    d.rectangle([x0, y0, x1, y1], fill=wall)
    # parapet
    d.rectangle([x0 - 6, y0 - 12, x1 + 6, y0 + 6], fill=tuple(int(c * 0.8) for c in wall))
    if roofbox:
        bw = (x1 - x0) * 0.16
        bx = x0 + (x1 - x0) * rng.uniform(0.55, 0.75)
        d.rectangle([bx, y0 - 54, bx + bw, y0 - 8], fill=tuple(int(c * 0.72) for c in wall))
        d.line([bx + bw * 0.8, y0 - 54, bx + bw * 0.8, y0 - 100], fill=tuple(int(c * 0.7) for c in wall), width=4)
    # windows
    gw, gh = x1 - x0, y1 - y0
    mx, my = gw * 0.06, gh * 0.09
    ww = (gw - 2 * mx) / bays
    wh = (gh - 2 * my) / floors
    for f in range(floors):
        for b in range(bays):
            wx0 = x0 + mx + b * ww + ww * 0.16
            wy0 = y0 + my + f * wh + wh * 0.18
            wx1 = wx0 + ww * 0.68
            wy1 = wy0 + wh * 0.58
            state = rng.random()
            if (f, b) in lit:
                d.rectangle([wx0, wy0, wx1, wy1], fill=(198, 176, 96))
            elif state < broken_p:
                d.rectangle([wx0, wy0, wx1, wy1], fill=tuple(int(c * 0.5) for c in glass))
                for _ in range(3):
                    px = rng.uniform(wx0, wx1); py = rng.uniform(wy0, wy1)
                    d.polygon([(px, py), (px + rng.uniform(-9, 9), py + rng.uniform(-9, 9)),
                               (px + rng.uniform(-9, 9), py + rng.uniform(-9, 9))],
                              fill=(148, 158, 165, 120))
            elif state < broken_p + 0.08:
                d.rectangle([wx0, wy0, wx1, wy1], fill=(58, 50, 40))
            else:
                d.rectangle([wx0, wy0, wx1, wy1], fill=glass)
                d.polygon([(wx0, wy0), (wx1, wy0), (wx0, wy1 - (wy1 - wy0) * 0.4)],
                          fill=(*[min(255, c + 22) for c in glass], 110))
            d.rectangle([wx0, wy0, wx1, wy1], outline=tuple(int(c * 0.6) for c in wall), width=2)
    # grime
    st = streaks(int(gw), int(gh), seed + 1, density=16, blur=4)
    dk = Image.new("RGB", (int(gw), int(gh)), (0, 0, 0))
    reg = img.crop((int(x0), int(y0), int(x0) + int(gw), int(y0) + int(gh)))
    mm = Image.fromarray((st * 130).astype(np.uint8))
    img.paste(Image.composite(dk, reg, mm), (int(x0), int(y0)))
    if sign:
        f = font(int(gh * 0.055), "bold")
        d2 = ImageDraw.Draw(img, "RGBA")
        tw = d2.textlength(sign, font=f)
        sx = x0 + gw * 0.5 - tw / 2
        sy = y0 + gh * 0.035
        d2.rectangle([sx - 18, sy - 10, sx + tw + 18, sy + gh * 0.055 + 12],
                     fill=(210, 205, 192, 46))
        d2.text((sx, sy), sign, font=f, fill=(214, 208, 196, 130))
    return img


def draw_house(d, x, y, w, h, pal, lit=True, seed=0):
    """Suburban gabled house silhouette with warm windows."""
    body = pal.get("house", (16, 20, 26))
    d.rectangle([x, y - h, x + w, y], fill=body)
    d.polygon([(x - w * 0.08, y - h), (x + w / 2, y - h - h * 0.45), (x + w * 1.08, y - h)], fill=body)
    if lit:
        rng = np.random.default_rng(seed)
        for _ in range(rng.integers(1, 3)):
            wx = x + w * rng.uniform(0.15, 0.65)
            wy = y - h * rng.uniform(0.3, 0.75)
            d.rectangle([wx, wy, wx + w * 0.16, wy + h * 0.18], fill=(212, 178, 104))


def draw_pole(d, x, y_ground, h, color=(10, 12, 16)):
    d.line([x, y_ground, x, y_ground - h], fill=color, width=8)
    d.line([x - 46, y_ground - h * 0.92, x + 46, y_ground - h * 0.92], fill=color, width=5)
    d.line([x - 34, y_ground - h * 0.83, x + 34, y_ground - h * 0.83], fill=color, width=4)


def wires(d, x0, x1, y, sag=26, color=(8, 10, 13), n=3):
    for i in range(n):
        yy = y + i * 10
        pts = [(x0 + (x1 - x0) * t, yy + sag * 4 * t * (1 - t)) for t in np.linspace(0, 1, 24)]
        d.line(pts, fill=color, width=3)


def tree_blob(img, cx, cy, r, color, seed):
    rng = np.random.default_rng(seed)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for _ in range(14):
        a = rng.uniform(0, 6.283)
        rr = r * rng.uniform(0.25, 0.6)
        x = cx + np.cos(a) * r * rng.uniform(0, 0.7)
        y = cy + np.sin(a) * r * rng.uniform(0, 0.5)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(*color, 255))
    d.line([cx, cy + r * 0.2, cx, cy + r * 1.15], fill=(*color, 255), width=int(r * 0.09) + 3)
    ov = ov.filter(ImageFilter.GaussianBlur(2.5))
    img.alpha_composite(ov) if img.mode == "RGBA" else img.paste(ov, (0, 0), ov)
    return img


# ---------------------------------------------------------------- corridor / rooms
def corridor_geometry(img, pal, seed, vp=(0.5, 0.52), hw=0.42, cam_h=0.32,
                      doors=5, end="black", lights=3, debris=0.5, k=0.9):
    """One-point-perspective corridor.  All coords normalized to image size."""
    w, h = img.size
    vx, vy = vp[0] * w, vp[1] * h
    d = ImageDraw.Draw(img, "RGBA")

    def proj(z, X, Y):
        """z: 0..inf distance; X lateral (-1..1)*hw*w ; Y vertical from eye."""
        f = k / (k + z)
        return vx + X * w * hw * f, vy + Y * h * f

    zfar = 14.0
    # walls / floor / ceiling quads
    fl, fr = proj(0, -1, 1.02), proj(0, 1, 1.02)
    ffl, ffr = proj(zfar, -1, 1.02), proj(zfar, 1, 1.02)
    cl, cr = proj(0, -1, -0.92), proj(0, 1, -0.92)
    fcl, fcr = proj(zfar, -1, -0.92), proj(zfar, 1, -0.92)
    d.polygon([fl, fr, ffr, ffl], fill=pal["floor"])
    d.polygon([cl, cr, fcr, fcl], fill=pal["ceil"])
    d.polygon([fl, ffl, fcl, cl], fill=pal["wallL"])
    d.polygon([fr, ffr, fcr, cr], fill=pal["wallR"])
    # end wall
    ex0, ey0 = proj(zfar, -1, -0.92)
    ex1, ey1 = proj(zfar, 1, 1.02)
    endc = (4, 5, 7) if end == "black" else pal.get("end", (30, 40, 46))
    d.rectangle([ex0, ey0, ex1, ey1], fill=endc)
    if end == "window":
        wx0, wy0 = proj(zfar, -0.4, -0.55)
        wx1, wy1 = proj(zfar, 0.4, 0.45)
        d.rectangle([wx0, wy0, wx1, wy1], fill=(96, 118, 128))
    # doors both sides
    rng = np.random.default_rng(seed)
    for i in range(doors):
        z0 = 0.9 + i * (zfar * 0.8 / doors)
        z1 = z0 + 0.55
        for side in (-1, 1):
            if rng.random() < 0.2:
                continue
            a = proj(z0, side, 1.0)
            b = proj(z1, side, 1.0)
            c = proj(z1, side, -0.62)
            e = proj(z0, side, -0.62)
            shade = rng.uniform(0.55, 0.9)
            base = pal["door"]
            col = tuple(int(cc * shade) for cc in base)
            if rng.random() < 0.25:  # open door: black gap
                col = (5, 6, 8)
            d.polygon([a, b, c, e], fill=col)
    # ceiling light panels
    for i in range(lights):
        z0 = 1.2 + i * (zfar * 0.65 / max(lights, 1))
        a = proj(z0, -0.28, -0.9)
        b = proj(z0, 0.28, -0.9)
        c = proj(z0 + 0.5, 0.28, -0.9)
        e = proj(z0 + 0.5, -0.28, -0.9)
        on = pal.get("light_on", None)
        col = on if (on and i == pal.get("flicker_idx", 0)) else pal.get("light_off", (30, 34, 38))
        d.polygon([a, b, c, e], fill=col)
        if on and i == pal.get("flicker_idx", 0):
            gx, gy = (a[0] + c[0]) / 2, (a[1] + c[1]) / 2
            img_g = add_glow(img, gx, gy, w * 0.13, pal.get("glow", (120, 140, 130)), 0.75)
            img.paste(img_g)
    # floor reflection stripe + debris
    st = streaks(w, h, seed + 5, density=10, blur=6)
    refl = Image.new("RGB", img.size, pal.get("refl", (40, 48, 52)))
    mband = np.zeros((h, w), np.float32)
    yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
    mband = np.clip((yy / h - vp[1]) * 2.2, 0, 1) * 0.25
    m = Image.fromarray((st * mband * 255).astype(np.uint8))
    img.paste(Image.composite(refl, img, m))
    dd = ImageDraw.Draw(img, "RGBA")
    for _ in range(int(16 * debris)):
        z = rng.uniform(0.8, 9)
        X = rng.uniform(-0.92, 0.92)
        x, y = proj(z, X, 1.0)
        s = 26 * k / (k + z)
        dd.polygon([(x, y), (x + s * rng.uniform(.5, 1.4), y - s * rng.uniform(.1, .5)),
                    (x + s * rng.uniform(-.4, .8), y + s * .3)],
                   fill=(*pal.get("debris", (12, 14, 16)), 220))
    # depth fade: darker toward the vanishing point
    dm = radial(w, h, vx, vy, w * 0.52, 210, 0, power=1.5)
    img.paste(Image.composite(Image.new("RGB", img.size, (2, 3, 4)), img, dm))
    # light pool on floor under the lit panel
    if pal.get("light_on"):
        i = pal.get("flicker_idx", 0)
        z0 = 1.2 + i * (zfar * 0.65 / max(lights, 1)) + 0.25
        px, py = proj(z0, 0, 1.0)
        img = add_glow(img, px, py, w * 0.15, pal.get("glow", (120, 140, 130)), 0.35,
                       power=2.4)
    return img, proj


def room_box(img, pal, seed, horizon=0.52, back=0.62):
    """Simple 3-wall room: back wall + angled sides + floor/ceiling."""
    w, h = img.size
    d = ImageDraw.Draw(img)
    bx0, by0 = w * (0.5 - back / 2), h * (horizon - back * 0.42)
    bx1, by1 = w * (0.5 + back / 2), h * (horizon + back * 0.40)
    d.polygon([(0, 0), (bx0, by0), (bx0, by1), (0, h)], fill=pal["wallL"])
    d.polygon([(w, 0), (bx1, by0), (bx1, by1), (w, h)], fill=pal["wallR"])
    d.polygon([(0, 0), (w, 0), (bx1, by0), (bx0, by0)], fill=pal["ceil"])
    d.polygon([(0, h), (w, h), (bx1, by1), (bx0, by1)], fill=pal["floor"])
    d.rectangle([bx0, by0, bx1, by1], fill=pal["back"])
    n = vnoise(w // 2, h // 2, 30, seed, 4)
    n = Image.fromarray((n * 46).astype(np.uint8)).resize((w, h))
    img.paste(ImageChops.subtract(img, Image.merge("RGB", (n, n, n))))
    return img, (bx0, by0, bx1, by1)


# ---------------------------------------------------------------- figures (RGBA)
def _body(d, cx, hgt, w, top_y, shoulder_w, hip_w, color):
    """Torso: shoulders ellipse + tapering robe/trunk to the ground."""
    d.polygon([(cx - shoulder_w, top_y + hgt * 0.06), (cx + shoulder_w, top_y + hgt * 0.06),
               (cx + hip_w, hgt), (cx - hip_w, hgt)], fill=color)
    d.ellipse([cx - shoulder_w, top_y, cx + shoulder_w, top_y + hgt * 0.14], fill=color)


def fig_humanoid(hgt=900, kind="shadow", seed=3):
    """Ghost silhouettes as RGBA layers on transparent canvas."""
    w = int(hgt * 0.62)
    img = Image.new("RGBA", (w, int(hgt * 1.06)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w / 2
    hd = hgt * 0.30
    if kind == "robe":
        body = (226, 224, 214, 235)
        _body(d, cx, hgt, w, hgt * 0.155, w * 0.235, w * 0.40, body)
        d.ellipse([cx - hd * 0.30, hgt * 0.02, cx + hd * 0.30, hgt * 0.02 + hd * 0.62], fill=body)
        d.ellipse([cx - hd * 0.17, hgt * 0.055, cx + hd * 0.17, hgt * 0.055 + hd * 0.44],
                  fill=(8, 6, 8, 255))
    elif kind == "pale":
        body = (208, 214, 218, 200)
        _body(d, cx, hgt, w, hgt * 0.165, w * 0.21, w * 0.30, body)
        hair = (12, 10, 12, 255)
        d.polygon([(cx - hd * 0.34, hgt * 0.05), (cx + hd * 0.34, hgt * 0.05),
                   (cx + hd * 0.42, hgt * 0.58), (cx - hd * 0.42, hgt * 0.58)], fill=hair)
        d.ellipse([cx - hd * 0.36, hgt * 0.0, cx + hd * 0.36, hgt * 0.05 + hd * 0.5], fill=hair)
        d.ellipse([cx - hd * 0.16, hgt * 0.075, cx + hd * 0.10, hgt * 0.075 + hd * 0.34],
                  fill=(206, 210, 212, 255))
    elif kind == "boy":
        body = (10, 11, 14, 235)
        _body(d, cx, hgt, w, hgt * 0.19, w * 0.185, w * 0.22, body)
        d.ellipse([cx - hd * 0.28, hgt * 0.05, cx + hd * 0.28, hgt * 0.05 + hd * 0.56], fill=body)
    elif kind == "reach":
        body = (16, 8, 10, 240)
        _body(d, cx, hgt, w, hgt * 0.155, w * 0.225, w * 0.33, body)
        d.ellipse([cx - hd * 0.30, hgt * 0.03, cx + hd * 0.30, hgt * 0.03 + hd * 0.62], fill=body)
        d.line([cx + hd * 0.1, hgt * 0.34, cx + w * 0.52, hgt * 0.20], fill=body,
               width=int(hgt * 0.05))
        d.ellipse([cx + w * 0.45, hgt * 0.14, cx + w * 0.59, hgt * 0.25], fill=body)
    else:  # shadow
        body = (6, 7, 10, 235)
        _body(d, cx, hgt, w, hgt * 0.145, w * 0.225, w * 0.31, body)
        d.ellipse([cx - hd * 0.31, hgt * 0.02, cx + hd * 0.31, hgt * 0.02 + hd * 0.64], fill=body)
    img = img.filter(ImageFilter.GaussianBlur(hgt * 0.012))
    return img


def paste_center(base, layer, cx, cy, scale=1.0):
    l = layer if scale == 1.0 else layer.resize(
        (max(1, int(layer.width * scale)), max(1, int(layer.height * scale))))
    base.paste(l, (int(cx - l.width / 2), int(cy - l.height / 2)), l)
    return base
