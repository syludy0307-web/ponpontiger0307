"""Evening forest walk — built only from still images + code (no video generation).
S1 side-forest establishing (foreground parallax)   S2 walking away down the path (back view)
S3 close-up moment                                   S4 far away into the sunset + fade"""
import math
import numpy as np
import cv2
from engine import (W, H, Cam, Handle, Layer, warp_coords, sample, poly_mask, noise_table, keys, flick, smooth,
                    soft_disc, add_sprite, bloom, vignette_map, GX, GY)
from blink import Eye, blink_curve

import os
D = os.environ.get("FOREST_DIR", "input/forest")


def load_rgb(name):
    return cv2.imread(f"{D}/{name}.png").astype(np.float32) / 255.0


def layer_from(name, pre_blur=0.0):
    F = np.load(f"{D}/{name}_fg.npy"); a = np.load(f"{D}/{name}_a.npy")
    if pre_blur > 0:
        F = cv2.GaussianBlur(F * a[..., None], (0, 0), pre_blur)
        a = cv2.GaussianBlur(a, (0, 0), pre_blur)
        L = Layer(np.zeros_like(F), a)
        L.rgba[..., :3] = F
        return L
    return Layer(F, a)


def affine_from_cam(cam):
    """2x3 matrix mapping source -> screen for cv2.warpAffine (no rotation used here)"""
    return np.float32([[cam.z, 0, W / 2 + cam.ox - cam.z * cam.cx], [0, cam.z, H / 2 + cam.oy - cam.z * cam.cy]])


def warp_img(img, cam, interp=cv2.INTER_LINEAR, border=cv2.BORDER_REFLECT):
    return cv2.warpAffine(img, affine_from_cam(cam), (W, H), flags=interp, borderMode=border)


def radial_rays(img, sun, n=18, spread=0.28, thr=0.72):
    """god rays: bright parts pulled away from the sun (zoom blur), computed once"""
    lum = img.mean(2)
    src = np.clip((lum - thr) / (1 - thr), 0, 1)[..., None] * img
    acc = np.zeros_like(src)
    for i in range(n):
        s = 1 + spread * i / n
        M = np.float32([[s, 0, sun[0] * (1 - s)], [0, s, sun[1] * (1 - s)]])
        acc += cv2.warpAffine(src, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR) * (1 - i / n)
    return cv2.GaussianBlur(acc / n, (0, 0), 3)


def angular_shimmer(shape, sun, t, seed=3):
    """slowly moving streak pattern around the sun (multiplies the rays)"""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ang = np.arctan2(yy - sun[1], xx - sun[0])
    return (0.65 + 0.35 * np.sin(ang * 23 + t * 0.6) * np.sin(ang * 9 - t * 0.35 + seed)).astype(np.float32)


def hexbgr(h):
    h = h.lstrip('#')
    return (int(h[4:6], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[0:2], 16) / 255.0)


LEAF_COLS = [hexbgr('#d9622b'), hexbgr('#e8923a'), hexbgr('#c0462a'), hexbgr('#f0b545'), hexbgr('#a8421f')]


def maple(r):
    lobes = [(-90, 1.0), (-35, 0.9), (-145, 0.9), (20, 0.62), (160, 0.62)]
    pts = []
    for i in range(0, 360, 4):
        th = math.radians(i - 90)
        d = math.degrees(th)
        best = 0.0
        for ang, ln in lobes:
            dd = (d - ang + 180) % 360 - 180
            best = max(best, ln * math.exp(-(dd / 24.0) ** 2))
        rr = (0.30 + 0.70 * best) * (1 + 0.07 * math.cos(math.radians(i) * 14))
        if abs(((d - 90) + 180) % 360 - 180) < 16:
            rr = min(rr, 0.28)
        pts.append((math.cos(th) * rr * r, math.sin(th) * rr * r))
    return np.array(pts, np.float32)


class Leaves:
    """falling maple leaves, deterministic; depth -> size, speed, blur"""

    def __init__(self, n, seed, area=(0, W, -200, H), depth=(0.4, 1.4)):
        rng = np.random.RandomState(seed)
        self.L = [dict(x=rng.uniform(area[0], area[1]), y0=rng.uniform(area[2], area[3]), z=rng.uniform(*depth),
                       vy=rng.uniform(55, 95), sway=rng.uniform(25, 70), f=rng.uniform(0.25, 0.6),
                       ph=rng.uniform(0, 6.28), rot=rng.uniform(0, 6.28), vr=rng.uniform(-1.6, 1.6),
                       spin=rng.uniform(1.5, 3.5), col=LEAF_COLS[rng.randint(len(LEAF_COLS))]) for _ in range(n)]
        self.shape = maple(1.0)

    def draw(self, img, t, front=None, light=1.0, wind=18.0):
        for L in self.L:
            if front is not None and (L["z"] > 1.0) != front:
                continue
            z = L["z"]
            y = (L["y0"] + L["vy"] * z * t) % (H + 260) - 130
            x = L["x"] + L["sway"] * z * math.sin(L["f"] * 6.283 * t + L["ph"]) + wind * z * t
            x = (x + 100) % (W + 200) - 100
            r = 11 * z
            c, s = math.cos(L["rot"] + L["vr"] * t), math.sin(L["rot"] + L["vr"] * t)
            flip = math.cos(L["spin"] * t + L["ph"])
            P = self.shape * r
            P = np.stack([P[:, 0] * (0.35 + 0.65 * abs(flip)), P[:, 1]], 1)
            pts = np.stack([P[:, 0] * c - P[:, 1] * s + x, P[:, 0] * s + P[:, 1] * c + y], 1)
            x0, y0 = int(max(0, pts[:, 0].min() - 8)), int(max(0, pts[:, 1].min() - 8))
            x1, y1 = int(min(W, pts[:, 0].max() + 8)), int(min(H, pts[:, 1].max() + 8))
            if x1 <= x0 or y1 <= y0:
                continue
            m = np.zeros((y1 - y0, x1 - x0), np.float32)
            cv2.fillPoly(m, [np.int32((pts - [x0, y0]) * 16)], 1.0, cv2.LINE_AA, shift=4)
            blur = abs(z - 0.9) * 2.2
            if blur > 0.4:
                m = cv2.GaussianBlur(m, (0, 0), blur)
            shade = (0.55 + 0.45 * abs(flip)) * light
            col = np.array(L["col"], np.float32) * shade
            k = 0.95 if z > 0.7 else 0.75
            reg = img[y0:y1, x0:x1]
            reg *= (1 - k * m[..., None])
            reg += (k * m)[..., None] * col


class Motes:
    def __init__(self, n, seed, box=(0, W, 0, H)):
        rng = np.random.RandomState(seed)
        self.m = [dict(x=rng.uniform(box[0], box[1]), y=rng.uniform(box[2], box[3]), vx=rng.uniform(-6, 12),
                       vy=rng.uniform(-12, -2), r=float(rng.choice([1.6, 2.2, 3.2])), k=rng.uniform(0.2, 0.6),
                       ph=rng.uniform(0, 6.28)) for _ in range(n)]
        self.spr = {r: soft_disc(r) for r in (1.6, 2.2, 3.2)}

    def draw(self, img, t, glow_map):
        for m in self.m:
            x = (m["x"] + m["vx"] * t + 7 * math.sin(0.8 * t + m["ph"])) % W
            y = (m["y"] + m["vy"] * t) % H
            g = float(glow_map[int(y), int(x)])
            tw = 0.55 + 0.45 * math.sin(2.1 * t + 3 * m["ph"])
            add_sprite(img, self.spr[m["r"]], x, y, (0.72, 0.9, 1.0), m["k"] * tw * g)


def grade(img, lift=0.012, warm=1.0):
    img = img * np.float32([0.97, 1.0, 1.035]) if warm else img
    return img + lift * (1 - img)


def comp(dst, rgbp, a):
    return rgbp + dst * (1 - a[..., None])


# =====================================================================================  S1
class S1Establish:
    """side view of the forest; camera slides right, foreground grass/birches pass faster"""
    dur = 3.5

    def __init__(self):
        self.bg = load_rgb("bg_side")
        self.sun = (1375, 250)
        self.rays = radial_rays(self.bg, self.sun, n=20, spread=0.35, thr=0.70)
        self.fg = layer_from("fg_grass", pre_blur=2.2)
        self.leaves = Leaves(14, 5, depth=(0.5, 1.3))
        self.motes = Motes(30, 6)
        self.glow = None
        self.vig = vignette_map(0.3, 2.0)

    def frame(self, t):
        e = t / self.dur
        z = W / 1672 * 1.10
        cam = Cam(760 + 110 * e, 470 - 8 * e, z)
        img = warp_img(self.bg, cam)
        rays = warp_img(self.rays, cam)
        sun_s = cam.to_screen(*self.sun)
        sh = angular_shimmer((H, W), sun_s, t)
        img = img + rays * sh[..., None] * 0.9
        if self.glow is None:
            self.glow = np.exp(-(((GX - sun_s[0]) / 700) ** 2 + ((GY - sun_s[1]) / 520) ** 2)).astype(np.float32)
        self.leaves.draw(img, t + 3, front=False, light=0.9)
        self.motes.draw(img, t, self.glow)
        # foreground layer: bigger, moves ~2.3x faster (closer to the camera), silhouetted by the backlight
        zf = W / 1672 * 1.28
        camf = Cam(700 + 110 * e * 2.3, 445, zf)
        u, v = camf.inverse_grid()
        rgbp, a = self.fg.render(u, v)
        rgbp = rgbp * 0.62
        img = comp(img, rgbp, a)
        self.leaves.draw(img, t + 3, front=True, light=0.8)
        img = bloom(img, 0.8, 0.3, 24)
        return grade(img) * self.vig[..., None]


# =====================================================================================  walk-away helpers
class BackWalkers:
    """the back-view still of the trio made to walk: body bob/sway, alternating legs (mirror trick),
    tail/hair swing. Everything in the source image's coordinates."""

    def __init__(self):
        F = np.load(f"{D}/trio_back_fg.npy"); a = np.load(f"{D}/trio_back_a.npy")
        self.layer = Layer(F, a)
        self.a = a
        S = a.shape
        self.S = S
        self.feet = (800.0, 905.0)          # ground anchor (between the woman's and the dog's feet)
        self.w_c = 872.0                     # woman's leg axis
        self.d_c = 616.0                     # dog's leg axis
        self.w_legs = poly_mask(S, [[[790, 640], [985, 640], [985, 941], [790, 941]]], 6)
        self.w_knee = 655.0
        self.d_legs = poly_mask(S, [[[505, 745], [735, 745], [735, 941], [505, 941]]], 6)
        self.d_knee = 770.0
        self.woman = Handle(poly_mask(S, [[[700, 0], [1060, 0], [1060, 941], [700, 941]]], 20), (870, 905))
        self.dog = Handle(poly_mask(S, [[[480, 370], [745, 370], [745, 941], [480, 941]]], 16), (615, 905))
        self.hair = poly_mask(S, [[[770, 120], [965, 120], [975, 390], [790, 390]]], 10) * \
            np.clip((np.arange(S[0], dtype=np.float32)[:, None] - 120) / 260, 0, 1)
        self.tail = Handle(poly_mask(S, [[[500, 505], [650, 505], [650, 650], [500, 650]]], 14), (600, 640))
        self.kitten = Handle(poly_mask(S, [[[925, 95], [1035, 95], [1035, 205], [925, 205]]], 8), (975, 200))
        self.handles = [self.tail, self.kitten, self.woman, self.dog]

    def set_pose(self, t, step_w=0.52, step_d=0.40):
        pw = (t / step_w) % 2.0          # 0..2: two steps per cycle
        pd = (t / step_d + 0.3) % 2.0
        def switch(p):  # 0 = original legs, 1 = mirrored legs; flips quickly at the passing moments
            return smooth(0.40, 0.60, p) if p < 1 else 1 - smooth(1.40, 1.60, p)
        self.sw = switch(pw)
        self.sd = switch(pd)
        bob_w = abs(math.sin(math.pi * pw))              # high at passing
        bob_d = abs(math.sin(math.pi * pd))
        self.woman.dy = -9.0 * bob_w + 4
        self.woman.dx = 5.0 * math.sin(math.pi * pw)
        self.woman.rot = math.radians(0.9 * math.sin(math.pi * pw))
        self.dog.dy = -6.0 * bob_d + 3
        self.dog.dx = 4.0 * math.sin(math.pi * pd)
        self.dog.rot = math.radians(1.2 * math.sin(math.pi * pd))
        self.tail.rot = math.radians(-6.0 * math.sin(math.pi * pd + 0.6))
        self.kitten.rot = math.radians(2.0 * math.sin(math.pi * pw + 1.0))
        self.phase_w = pw

    def fields(self, t):
        def hair(u, v):
            w = sample(self.hair, u, v)
            sway = 6.0 * math.sin(math.pi * self.phase_w - 0.7)
            return w * sway * np.clip((v - 120) / 260, 0, 1), np.zeros_like(v)
        return [hair]

    def render(self, t, anchor_xy, scale):
        """draw the walkers with their ground anchor at screen anchor_xy, source->screen scale"""
        self.set_pose(t)
        u = (GX - anchor_xy[0]) / scale + self.feet[0]
        v = (GY - anchor_xy[1]) / scale + self.feet[1]
        uu, vv = warp_coords(u.astype(np.float32), v.astype(np.float32), self.handles, self.fields(t))
        rgb, a = self.layer.render(uu, vv)
        mw = sample(self.w_legs, uu, vv) * np.clip((vv - self.w_knee) / 30.0, 0, 1) * self.sw
        md = sample(self.d_legs, uu, vv) * np.clip((vv - self.d_knee) / 25.0, 0, 1) * self.sd
        if self.sw > 1e-3:
            r2, a2 = self.layer.render((2 * self.w_c - uu).astype(np.float32), vv)
            rgb = rgb * (1 - mw[..., None]) + r2 * mw[..., None]
            a = a * (1 - mw) + a2 * mw
        if self.sd > 1e-3:
            r3, a3 = self.layer.render((2 * self.d_c - uu).astype(np.float32), vv)
            rgb = rgb * (1 - md[..., None]) + r3 * md[..., None]
            a = a * (1 - md) + a3 * md
        return rgb, a


def long_shadow(a, feet_y, length=1.35, shear=-0.35, strength=0.42, blur=7):
    """backlit scene: shadows fall toward the camera (down the screen), a little to the left"""
    M = np.float32([[1, shear * length * -1, 0], [0, -length, (1 + length) * feet_y]])
    M[0, 2] = -M[0, 1] * feet_y
    sh = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR)
    sh = cv2.GaussianBlur(sh, (0, 0), blur)
    fade = np.clip(1 - (GY - feet_y) / (H - feet_y + 1e-3) * 0.85, 0, 1) * (GY >= feet_y - 6)
    return np.clip(sh * fade * strength, 0, 0.8)


# =====================================================================================  S2 / S4
class SPathWalk:
    """background: the forest path; the trio walks away from the camera"""

    def __init__(self, d0, d1, dur, cam_zoom=(1.0, 1.05), flare=(0.0, 0.0), seed=11):
        self.dur = dur
        self.bg = load_rgb("bg_path")
        self.sun = (1300, 292)
        self.rays = radial_rays(self.bg, self.sun, n=20, spread=0.4, thr=0.66)
        self.walk = BackWalkers()
        self.d0, self.d1 = d0, d1
        self.cam_zoom, self.flare = cam_zoom, flare
        self.leaves = Leaves(16, seed, depth=(0.45, 1.35))
        self.motes = Motes(36, seed + 1)
        self.vig = vignette_map(0.3, 2.0)
        self.flare_spr = soft_disc(90.0)

    def frame(self, t):
        e = t / self.dur
        zb = W / 1672 * (self.cam_zoom[0] + (self.cam_zoom[1] - self.cam_zoom[0]) * smooth(0, 1, e))
        vp = (830.0, 432.0)
        cam = Cam(836, 470 - 6 * e, zb)
        img = warp_img(self.bg, cam)
        rays = warp_img(self.rays, cam)
        sun_s = cam.to_screen(*self.sun)
        sh = angular_shimmer((H, W), sun_s, t, seed=7)
        img = img + rays * sh[..., None] * 1.0
        glow = np.exp(-(((GX - sun_s[0]) / 650) ** 2 + ((GY - sun_s[1]) / 480) ** 2)).astype(np.float32)
        # the trio: distance grows as they walk away (camera follows a bit slower)
        d = self.d0 + (self.d1 - self.d0) * e
        vps = cam.to_screen(*vp)
        feet_y = vps[1] + (H * 0.93 - vps[1]) * (self.d0 / d) * 1.0 * 0.98
        x = vps[0] - 30 * (self.d0 / d)
        scale = 0.60 * (self.d0 / d) * (zb / (W / 1672))
        rgbp, a = self.walk.render(t, (x, feet_y), scale)
        # grade the characters into the scene: a bit darker/warmer (backlit), rim on the sun side
        rgbp = rgbp * np.float32([0.80, 0.86, 0.95])
        ab = cv2.GaussianBlur(a, (0, 0), 3)
        gx_ = cv2.Sobel(ab, cv2.CV_32F, 1, 0, ksize=3)
        gy_ = cv2.Sobel(ab, cv2.CV_32F, 0, 1, ksize=3)
        rim = np.clip((-gx_ * 0.6 + gy_ * 0.5) * 2.5, 0, 1) * a
        rgbp = rgbp + rim[..., None] * np.array(hexbgr('#ffc47a'), np.float32) * 0.35
        shadow = long_shadow(a, feet_y, length=1.4, shear=-0.30, strength=0.45, blur=5 + 4 * scale)
        img = img * (1 - shadow[..., None] * np.float32([0.9, 0.95, 1.0]))
        img = comp(img, rgbp, a)
        self.leaves.draw(img, t + 1.5 * self.dur, front=None, light=0.95)
        self.motes.draw(img, t, glow)
        # sun flare growing (S4)
        fk = self.flare[0] + (self.flare[1] - self.flare[0]) * smooth(0, 1, e)
        if fk > 0:
            add_sprite(img, self.flare_spr, sun_s[0], sun_s[1], (0.55, 0.8, 1.0), fk)
            img += glow[..., None] * np.float32([0.25, 0.45, 0.75]) * fk * 0.5
        img = bloom(img, 0.78, 0.32, 26)
        return grade(img) * self.vig[..., None]


# =====================================================================================  S3
class S3Close:
    """close-up: she smiles down at Gen, Gen looks up, Moka in her arms. Over a defocused forest."""
    dur = 4.5

    def __init__(self):
        F = np.load(f"{D}/trio_close_fg.npy"); a = np.load(f"{D}/trio_close_a.npy")
        self.layer = Layer(F, a)
        S = a.shape
        bg = load_rgb("bg_side")
        self.bg = cv2.GaussianBlur(bg, (0, 0), 16)
        self.sun = (1375, 250)
        # woman
        self.w_head = Handle(poly_mask(S, [[[430, 0], [915, 0], [915, 300], [860, 420], [650, 440], [470, 360]]], 24),
                             (700, 560))
        self.w_ear = Handle(poly_mask(S, [[[510, 218], [555, 218], [555, 290], [510, 290]]], 3), (533, 225))
        self.w_breath = Handle(poly_mask(S, [[[0, 330], [915, 330], [915, 941], [0, 941]]], 60), (450, 900))
        self.hair = (poly_mask(S, [[[250, 100], [470, 60], [480, 600], [300, 600]],
                                   [[800, 0], [915, 0], [915, 900], [800, 900]]], 10) *
                     np.clip((np.arange(S[0], dtype=np.float32)[:, None] - 80) / 500, 0, 1)).astype(np.float32)
        self.eyes_w = [Eye(690, 263, 22, 26, -7, 9, 14, meet=0.95, band=2.5, lash=0.25, lash_w=1.8),
                       Eye(776, 284, 24, 23, -7, 9, 13, meet=0.95, band=2.5, lash=0.25, lash_w=1.8)]
        # Moka
        self.k_head = Handle(poly_mask(S, [[[228, 600], [460, 600], [462, 790], [240, 800]]], 10), (360, 840))
        self.k_ear = Handle(poly_mask(S, [[[262, 615], [335, 615], [335, 685], [262, 685]]], 5), (310, 680))
        self.eyes_k = [Eye(371, 701, -5, 17, -13, 13, 26, meet=0.8, band=3.5, lash=0.45, lash_w=2.2),
                       Eye(432, 688, -12, 13, -12, 12, 24, meet=0.8, band=3.5, lash=0.45, lash_w=2.2)]
        # Gen
        self.d_head = Handle(poly_mask(S, [[[895, 225], [1360, 225], [1365, 700], [900, 700]]], 22), (1150, 820))
        self.d_ear_l = Handle(poly_mask(S, [[[980, 228], [1105, 228], [1105, 390], [985, 390]]], 7), (1060, 380))
        self.d_ear_r = Handle(poly_mask(S, [[[1195, 290], [1350, 290], [1350, 455], [1200, 455]]], 7), (1235, 440))
        self.d_nose = Handle(poly_mask(S, [[[925, 480], [1000, 480], [1000, 550], [925, 550]]], 9), (960, 515))
        self.eyes_d = [Eye(1103, 470, -18, 23, -11, 13, 30, band=4, lash=0.5, lash_w=2.5)]
        self.handles = [self.w_ear, self.k_ear, self.d_ear_l, self.d_ear_r, self.d_nose, self.w_head, self.k_head,
                        self.d_head, self.w_breath]
        self.eyes = self.eyes_w + self.eyes_k + self.eyes_d
        self.nA = noise_table(1300, 1900, 90, 51)
        self.leaves = Leaves(10, 21, depth=(0.5, 1.5))
        self.motes = Motes(26, 22)
        self.vig = vignette_map(0.28, 2.0)

    def pose(self, t):
        br = 0.5 - 0.5 * math.cos(2 * math.pi * t / 3.9)
        self.w_head.rot = math.radians(-0.9 * math.sin(2 * math.pi * t / 5.5))
        self.w_head.dy = 1.5 * math.sin(2 * math.pi * t / 5.5 + 1)
        self.w_ear.rot = math.radians(4.0 * math.sin(2 * math.pi * t / 1.3) - 2.5 * math.cos(2 * math.pi * t / 5.5))
        self.w_breath.dy = -1.6 * br
        wb = blink_curve(t, 1.2) + blink_curve(t, 3.6)
        for e in self.eyes_w:
            e.c = min(1.0, wb)
        self.k_head.rot = math.radians(keys(t, [(0, 0), (1.6, 0), (2.1, 5.0), (3.4, 5.0), (3.9, 0)]))
        self.k_ear.rot = math.radians(flick(t, 0.7, -5.0))
        kb = blink_curve(t, 2.7, depth=0.9)
        for e in self.eyes_k:
            e.c = kb
        self.d_head.rot = math.radians(-1.2 * math.sin(2 * math.pi * t / 4.8 + 0.4))
        self.d_ear_l.rot = math.radians(flick(t, 1.9, 6.0))
        self.d_ear_r.rot = math.radians(flick(t, 3.1, -6.0))
        sn = sum(math.sin(math.pi * (t - t0) / 0.11) for t0 in (0.45, 0.6, 0.75) if 0 <= t - t0 <= 0.11)
        self.d_nose.dy = -1.6 * sn
        self.d_nose.dx = -1.0 * sn
        db = blink_curve(t, 2.2)
        for e in self.eyes_d:
            e.c = db

    def frame(self, t):
        self.pose(t)
        e = t / self.dur
        z = W / 1672 * (1.015 + 0.04 * smooth(0, 1, e))
        cam = Cam(836 + 10 * e, 470 + 6 * e, z)
        bcam = Cam(900, 360, W / 1672 * 1.25)
        img = warp_img(self.bg, bcam)
        sun_s = bcam.to_screen(*self.sun)
        glow = np.exp(-(((GX - sun_s[0]) / 600) ** 2 + ((GY - sun_s[1]) / 450) ** 2)).astype(np.float32)
        img += glow[..., None] * np.float32([0.25, 0.5, 0.85]) * 0.35
        self.leaves.draw(img, t + 4, front=False, light=0.9)
        u, v = cam.inverse_grid()

        def hair(uu, vv):
            w = sample(self.hair, uu, vv)
            n = sample(self.nA, uu * 0.4 + 50, vv * 0.8 - 55 * t + 300)
            return w * n * 4.0, w * n * 0.8

        uu, vv = warp_coords(u, v, self.handles, [hair] + [ey.field for ey in self.eyes])
        rgbp, a = self.layer.render(uu, vv)
        shade = np.ones_like(u)
        for ey in self.eyes:
            ey.shade(u, v, shade)
        rgbp = rgbp * shade[..., None]
        bgb = cv2.GaussianBlur(img, (0, 0), 10)
        wrap = np.clip(a - cv2.erode(a, np.ones((5, 5), np.uint8)), 0, 1)
        rgbp = rgbp + bgb * 0.3 * wrap[..., None] * a[..., None]
        img = comp(img, rgbp, a)
        self.motes.draw(img, t, glow)
        img = bloom(img, 0.8, 0.28, 24)
        return grade(img) * self.vig[..., None]
