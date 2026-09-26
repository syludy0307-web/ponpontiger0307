"""Motion-graphics helpers: text sprites (PIL), premultiplied blits, labels."""
import math
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SANS = os.path.join(HERE, "fonts", "NotoSansJP-VF.ttf")
BRUSH = os.path.join(HERE, "fonts", "YujiSyuku-Regular.ttf")
_font_cache = {}


def font(path, size, weight=None):
    key = (path, size, weight)
    if key not in _font_cache:
        f = ImageFont.truetype(path, size)
        if weight is not None:
            try:
                f.set_variation_by_axes([weight])
            except Exception:
                pass
        _font_cache[key] = f
    return _font_cache[key]


def text_sprite(text, path, size, weight=None, color=(1, 1, 1), pad=8, stroke=0, stroke_color=(0, 0, 0), tracking=0):
    """-> premultiplied BGRA float32 sprite"""
    f = font(path, size, weight)
    # measure
    tmp = Image.new("L", (10, 10))
    d = ImageDraw.Draw(tmp)
    if tracking:
        widths = [d.textlength(ch, font=f) for ch in text]
        tw = int(sum(widths) + tracking * (len(text) - 1)) + 1
    else:
        tw = int(d.textlength(text, font=f)) + 1
    asc, desc = f.getmetrics()
    th = asc + desc
    Wd, Hd = tw + 2 * pad + 2 * stroke, th + 2 * pad + 2 * stroke
    fill = Image.new("L", (Wd, Hd), 0)
    df = ImageDraw.Draw(fill)
    strk = Image.new("L", (Wd, Hd), 0)
    ds = ImageDraw.Draw(strk)
    x = pad + stroke
    if tracking:
        for ch, wch in zip(text, widths):
            if stroke:
                ds.text((x, pad + stroke), ch, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
            df.text((x, pad + stroke), ch, font=f, fill=255)
            x += wch + tracking
    else:
        if stroke:
            ds.text((x, pad + stroke), text, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
        df.text((x, pad + stroke), text, font=f, fill=255)
    a_fill = np.asarray(fill, np.float32) / 255.0
    out = np.zeros((Hd, Wd, 4), np.float32)
    if stroke:
        a_st = np.asarray(strk, np.float32) / 255.0
        out[..., :3] = a_st[..., None] * np.array(stroke_color, np.float32)
        out[..., 3] = a_st
    # fill over stroke (premultiplied)
    out[..., :3] = a_fill[..., None] * np.array(color, np.float32) + out[..., :3] * (1 - a_fill[..., None])
    out[..., 3] = a_fill + out[..., 3] * (1 - a_fill)
    return out


def rounded_rect(w, h, r, color, alpha):
    w, h, r = int(round(w)), int(round(h)), int(round(r))
    m = np.zeros((h * 4, w * 4), np.uint8)
    R = r * 4
    cv2.rectangle(m, (R, 0), (w * 4 - R, h * 4), 255, -1)
    cv2.rectangle(m, (0, R), (w * 4, h * 4 - R), 255, -1)
    for cx, cy in ((R, R), (w * 4 - R, R), (R, h * 4 - R), (w * 4 - R, h * 4 - R)):
        cv2.circle(m, (cx, cy), R, 255, -1)
    a = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0 * alpha
    out = np.zeros((h, w, 4), np.float32)
    out[..., :3] = a[..., None] * np.array(color, np.float32)
    out[..., 3] = a
    return out


def blit(img, spr, x, y, k=1.0):
    """premultiplied over; x,y = top-left (float ok -> rounded)"""
    if k <= 0:
        return
    hs, ws = spr.shape[:2]
    H, W = img.shape[:2]
    x0, y0 = int(round(x)), int(round(y))
    x1, y1 = x0 + ws, y0 + hs
    sx0, sy0 = max(0, -x0), max(0, -y0)
    sx1, sy1 = ws - max(0, x1 - W), hs - max(0, y1 - H)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    s = spr[sy0:sy1, sx0:sx1] * k
    reg = img[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1]
    reg *= (1 - s[..., 3:4])
    reg += s[..., :3]


def blit_xform(img, spr, cx, cy, scale=1.0, rot_deg=0.0, k=1.0):
    """premultiplied over with scale/rotation about the sprite centre placed at cx,cy"""
    if k <= 0 or scale <= 0:
        return
    H, W = img.shape[:2]
    hs, ws = spr.shape[:2]
    M = cv2.getRotationMatrix2D((ws / 2, hs / 2), -rot_deg, scale)
    M[0, 2] += cx - ws / 2
    M[1, 2] += cy - hs / 2
    # bounding box on screen
    corners = np.array([[0, 0, 1], [ws, 0, 1], [0, hs, 1], [ws, hs, 1]], np.float32) @ M.T
    x0 = max(0, int(math.floor(corners[:, 0].min())) - 2)
    y0 = max(0, int(math.floor(corners[:, 1].min())) - 2)
    x1 = min(W, int(math.ceil(corners[:, 0].max())) + 2)
    y1 = min(H, int(math.ceil(corners[:, 1].max())) + 2)
    if x1 <= x0 or y1 <= y0:
        return
    M2 = M.copy()
    M2[0, 2] -= x0
    M2[1, 2] -= y0
    warped = cv2.warpAffine(spr, M2, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)) * k
    reg = img[y0:y1, x0:x1]
    reg *= (1 - warped[..., 3:4])
    reg += warped[..., :3]


class Label:
    """two-line caption pill, bottom-left, slides in/out"""

    def __init__(self, title, sub, x=64, y=900, top=False):
        self.t1 = text_sprite(title, SANS, 46, 800, color=(1, 1, 1), pad=4)
        self.t2 = text_sprite(sub, SANS, 28, 500, color=(0.93, 0.96, 1.0), pad=4)
        w = max(self.t1.shape[1], self.t2.shape[1]) + 56
        h = self.t1.shape[0] + self.t2.shape[0] + 34
        self.bg = rounded_rect(w, h, 18, (0.16, 0.11, 0.08), 0.62)  # BGR navy-ish
        self.bar = rounded_rect(8, h - 36, 4, (0.25, 0.55, 0.98), 1.0)  # orange accent (BGR)
        self.x, self.y, self.h = x, (y if top else y - h), h

    def draw(self, img, t, t_in, t_out):
        a = min(1.0, max(0.0, (t - t_in) / 0.35)) * min(1.0, max(0.0, (t_out - t) / 0.3))
        if a <= 0:
            return
        e = 1 - (1 - a) ** 3
        dx = (1 - e) * -60
        blit(img, self.bg, self.x + dx, self.y, e)
        blit(img, self.bar, self.x + dx + 20, self.y + 18, e)
        blit(img, self.t1, self.x + dx + 38, self.y + 12, e)
        blit(img, self.t2, self.x + dx + 38, self.y + 12 + self.t1.shape[0] + 2, e)


class Tag:
    def __init__(self, text, size=26, weight=600):
        self.t = text_sprite(text, SANS, size, weight, color=(1, 1, 1), pad=3)
        w, h = self.t.shape[1] + 36, self.t.shape[0] + 16
        self.bg = rounded_rect(w, h, h // 2, (0.10, 0.07, 0.05), 0.55)
        self.w, self.h = w, h

    def draw(self, img, k=1.0, y=36):
        W = img.shape[1]
        x = W - self.w - 40
        blit(img, self.bg, x, y, k)
        blit(img, self.t, x + 18, y + 8, k)
