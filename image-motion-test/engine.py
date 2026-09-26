"""Image-only motion engine (no video generation): a still photo + code -> moving shot.

Every layer is sampled once per frame through one combined inverse map
(screen -> camera^-1 -> rig warp^-1 -> source pixel), so there is no double resampling.
Deterministic: all noise comes from seeded tables built at start-up.
"""
import math
import numpy as np
import cv2

W, H, FPS = 1920, 1080, 30
GX, GY = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))


# ---------------------------------------------------------------- small math helpers
def clamp01(x):
    return min(1.0, max(0.0, x))


def smooth(a, b, x):
    t = clamp01((x - a) / (b - a)) if b != a else float(x >= b)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def keys(t, pts):
    """piecewise smoothstep keyframes: pts = [(time, value), ...]"""
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1:
            return lerp(v0, v1, smooth(t0, t1, t))
    return pts[-1][1]


def flick(t, t0, amp, attack=0.06, decay=0.16, period=0.34):
    """quick ear flick: fast attack then a damped spring back"""
    tau = t - t0
    if tau <= 0:
        return 0.0
    if tau < attack:
        return amp * math.sin(0.5 * math.pi * tau / attack)
    u = tau - attack
    return amp * math.exp(-u / decay) * math.cos(2 * math.pi * u / period)


def poly_mask(shape, polys, sigma, scale=1.0):
    m = np.zeros(shape, np.float32)
    for p in polys:
        cv2.fillPoly(m, [np.int32(np.array(p, np.float64) * scale)], 1.0, cv2.LINE_AA)
    if sigma > 0:
        m = cv2.GaussianBlur(m, (0, 0), sigma * scale)
    return m


def noise_table(h, w, cell, seed):
    """smooth value noise in [-1, 1], tileable enough for scrolling (built once, seeded)"""
    rng = np.random.RandomState(seed)
    gh, gw = h // cell + 4, w // cell + 4
    g = rng.rand(gh, gw).astype(np.float32) * 2 - 1
    big = cv2.resize(g, (gw * cell, gh * cell), interpolation=cv2.INTER_CUBIC)
    return big


def sample(img, mx, my, interp=cv2.INTER_LINEAR, border=0.0):
    return cv2.remap(img, mx, my, interp, borderMode=cv2.BORDER_CONSTANT, borderValue=border)


# ---------------------------------------------------------------- camera
class Cam:
    """source(x,y) -> screen: S = z * R(rot) * (src - c) + (W/2, H/2)"""

    def __init__(self, cx, cy, z, rot=0.0, ox=0.0, oy=0.0):
        self.cx, self.cy, self.z, self.rot, self.ox, self.oy = cx, cy, z, rot, ox, oy

    def inverse_grid(self):
        c, s = math.cos(-self.rot), math.sin(-self.rot)
        X = (GX - (W / 2 + self.ox)) / self.z
        Y = (GY - (H / 2 + self.oy)) / self.z
        return (c * X - s * Y + self.cx).astype(np.float32), (s * X + c * Y + self.cy).astype(np.float32)

    def to_screen(self, x, y):
        c, s = math.cos(self.rot), math.sin(self.rot)
        dx, dy = x - self.cx, y - self.cy
        return (self.z * (c * dx - s * dy) + W / 2 + self.ox, self.z * (s * dx + c * dy) + H / 2 + self.oy)


# ---------------------------------------------------------------- rig: weighted inverse transforms
class Handle:
    """region (soft mask in source coords) moved by rotation about a pivot, scale, translation"""

    def __init__(self, mask, pivot):
        self.mask = mask
        self.px, self.py = pivot
        self.rot = 0.0
        self.scale = 1.0
        self.dx = 0.0
        self.dy = 0.0

    def active(self):
        return abs(self.rot) > 1e-5 or abs(self.scale - 1) > 1e-5 or abs(self.dx) > 1e-3 or abs(self.dy) > 1e-3


def warp_coords(u, v, handles, fields=()):
    """u,v: source coords reached by the camera. Returns rig-inverted coords."""
    du = np.zeros_like(u)
    dv = np.zeros_like(v)
    for h in handles:
        if not h.active():
            continue
        w = sample(h.mask, u, v)
        c, s = math.cos(-h.rot), math.sin(-h.rot)
        qx = (u - h.px - h.dx) / h.scale
        qy = (v - h.py - h.dy) / h.scale
        ix = c * qx - s * qy + h.px
        iy = s * qx + c * qy + h.py
        du += w * (ix - u)
        dv += w * (iy - v)
    for f in fields:  # f(u, v) -> (du, dv) extra displacement fields (wind, fur flutter)
        a, b = f(u, v)
        du += a
        dv += b
    return u + du, v + dv


# ---------------------------------------------------------------- layer
class Layer:
    """premultiplied RGB + alpha, float32"""

    def __init__(self, rgb, alpha=None):
        if alpha is None:
            alpha = np.ones(rgb.shape[:2], np.float32)
        self.a = alpha.astype(np.float32)
        self.rgba = np.dstack([rgb.astype(np.float32) * self.a[..., None], self.a]).astype(np.float32)

    def render(self, mx, my, interp=cv2.INTER_LINEAR):
        out = sample(self.rgba, mx, my, interp)
        return out[..., :3], out[..., 3]


def over(dst_rgb, src_rgb_p, src_a):
    return src_rgb_p + dst_rgb * (1 - src_a[..., None])


# ---------------------------------------------------------------- finishing
def bloom(img, thr=0.72, k=0.35, sigma=18):
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    b = np.clip(small - thr, 0, None)
    b = cv2.GaussianBlur(b, (0, 0), sigma / 4)
    b = cv2.resize(b, (W, H), interpolation=cv2.INTER_LINEAR)
    return img + k * b


def vignette_map(strength=0.28, power=2.2):
    x = (GX - W / 2) / (W / 2)
    y = (GY - H / 2) / (H / 2)
    r = np.sqrt(x * x * 0.85 + y * y)
    return (1 - strength * np.clip(r, 0, 1.5) ** power).astype(np.float32)


def soft_disc(r):
    s = int(r * 3) | 1
    yy, xx = np.mgrid[-s:s + 1, -s:s + 1].astype(np.float32)
    return np.exp(-(xx * xx + yy * yy) / (2 * r * r)).astype(np.float32)


def add_sprite(img, spr, x, y, color, k):
    """additive blend of a single-channel sprite centred at x,y"""
    hs, ws = spr.shape
    x0, y0 = int(round(x)) - ws // 2, int(round(y)) - hs // 2
    x1, y1 = x0 + ws, y0 + hs
    sx0, sy0 = max(0, -x0), max(0, -y0)
    sx1, sy1 = ws - max(0, x1 - W), hs - max(0, y1 - H)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    img[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1] += spr[sy0:sy1, sx0:sx1, None] * (np.array(color, np.float32) * k)


def to_u8(img_bgr):
    return (np.clip(img_bgr, 0, 1) * 255 + 0.5).astype(np.uint8)
