"""The user's own green-screen still (woman + Gen + Moka) -> 8 s living shot, no video generation.
Woman: hair sway, head sway, earrings swing, blinks, breathing.
Gen: ear flicks, nose sniff, blink, head sway, breathing.  Moka: head tilt, ear twitch, slow blink.
Background: warm bokeh room (code)."""
import math
import numpy as np
import cv2
from engine import (W, H, Cam, Handle, Layer, warp_coords, sample, poly_mask, noise_table, keys, flick,
                    smooth, soft_disc, add_sprite, bloom, vignette_map, GX, GY)
from blink import Eye, blink_curve
import mg

U = 2.0


def hexbgr(h):
    h = h.lstrip('#')
    return (int(h[4:6], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[0:2], 16) / 255.0)


def unsharp(img, sigma=1.2, amount=0.35):
    return np.clip(img + amount * (img - cv2.GaussianBlur(img, (0, 0), sigma)), 0, 1)


class TrioShot:
    dur = 8.0

    def __init__(self, fg_path, alpha_path, title=False):
        fg = np.load(fg_path)
        a = np.load(alpha_path)
        h, w = a.shape
        self.h, self.w = h, w
        up = (int(w * U), int(h * U))
        ap = np.clip(cv2.resize(a, up, interpolation=cv2.INTER_LANCZOS4), 0, 1)
        rp = cv2.resize(fg * a[..., None], up, interpolation=cv2.INTER_LANCZOS4)
        rp = unsharp(np.clip(rp, 0, 1), 1.2, 0.3)
        self.subj = Layer(np.zeros_like(rp), ap)
        self.subj.rgba[..., :3] = np.clip(rp, 0, ap[..., None])
        S = (h, w)
        dark = (fg.mean(2) < 0.22).astype(np.float32)

        # ---- woman
        self.w_head = Handle(poly_mask(S, [[[430, 0], [810, 0], [815, 160], [760, 420], [660, 470], [530, 470],
                                            [440, 400], [420, 160]]], 26), (585, 520))
        self.w_ear_l = Handle(poly_mask(S, [[[432, 222], [472, 222], [470, 292], [430, 292]]], 3), (452, 228))
        self.w_ear_r = Handle(poly_mask(S, [[[664, 342], [702, 342], [702, 402], [664, 402]]], 3), (686, 347))
        self.w_breath = Handle(poly_mask(S, [[[0, 240], [835, 240], [835, 700], [0, 700]]], 60), (420, 700))
        hl = poly_mask(S, [[[92, 300], [175, 250], [330, 210], [440, 120], [470, 160], [420, 300], [340, 380],
                            [250, 380], [178, 430], [172, 900], [92, 900]]], 6) * dark
        ramp_l = np.clip((np.arange(h, dtype=np.float32)[:, None] - 230) / 520, 0.15, 1.0)
        self.hair_l = (cv2.GaussianBlur(hl, (0, 0), 4) * ramp_l).astype(np.float32)
        hr = poly_mask(S, [[[700, 120], [805, 0], [832, 200], [826, 560], [800, 630], [722, 630], [690, 420]]], 6) * dark
        ramp_r = np.clip((np.arange(h, dtype=np.float32)[:, None] - 200) / 380, 0.1, 1.0) * \
            np.clip((640 - np.arange(h, dtype=np.float32)[:, None]) / 90, 0, 1)
        self.hair_r = (cv2.GaussianBlur(hr, (0, 0), 4) * ramp_r).astype(np.float32)
        self.eyes_w = [Eye(560, 233, 20, 22, -12, 14, 16, band=2.5, lash=0.25, lash_w=1.8),
                       Eye(663, 285, 16, 23, -10, 12, 14, band=2.5, lash=0.25, lash_w=1.8)]

        # ---- Moka (kitten)
        self.k_head = Handle(poly_mask(S, [[[636, 628], [722, 622], [885, 636], [890, 760], [855, 828], [760, 842],
                                            [655, 806], [630, 720]]], 9), (765, 870))
        self.k_ear_l = Handle(poly_mask(S, [[[650, 648], [714, 648], [716, 716], [654, 714]]], 5), (698, 708))
        self.k_ear_r = Handle(poly_mask(S, [[[834, 634], [888, 638], [888, 682], [838, 682]]], 5), (848, 676))
        self.k_breath = Handle(poly_mask(S, [[[560, 820], [850, 820], [850, 1086], [560, 1086]]], 30), (700, 1000))
        self.eyes_k = [Eye(757, 742, -5, 19, -15, 15, 30, meet=0.8, band=3.5, lash=0.45, lash_w=2.2),
                       Eye(834, 736, -10, 16, -14, 14, 28, meet=0.8, band=3.5, lash=0.45, lash_w=2.2)]

        # ---- Gen (dog)
        self.d_head = Handle(poly_mask(S, [[[845, 108], [1300, 108], [1325, 420], [1250, 600], [905, 600],
                                            [828, 420]]], 22), (1075, 740))
        self.d_ear_l = Handle(poly_mask(S, [[[860, 105], [1010, 105], [1018, 305], [868, 305]]], 7), (970, 290))
        self.d_ear_r = Handle(poly_mask(S, [[[1145, 105], [1300, 105], [1295, 305], [1148, 305]]], 7), (1185, 290))
        self.d_nose = Handle(poly_mask(S, [[[1025, 412], [1122, 412], [1128, 500], [1022, 500]]], 10), (1073, 452))
        self.d_breath = Handle(poly_mask(S, [[[850, 620], [1330, 620], [1330, 1000], [850, 1000]]], 50), (1080, 800))
        self.eyes_d = [Eye(998, 355, 5, 25, -13, 16, 34, band=4, lash=0.5, lash_w=2.5),
                       Eye(1150, 358, -5, 24, -14, 17, 34, band=4, lash=0.5, lash_w=2.5)]

        # small parts first so the bigger head/body moves carry them
        self.handles = [self.w_ear_l, self.w_ear_r, self.k_ear_l, self.k_ear_r, self.d_ear_l, self.d_ear_r,
                        self.d_nose, self.w_head, self.k_head, self.d_head, self.w_breath, self.k_breath,
                        self.d_breath]
        self.eyes = self.eyes_w + self.eyes_k + self.eyes_d
        self.nA = noise_table(1600, 1900, 90, 41)
        self.nB = noise_table(1600, 1900, 90, 42)

        # ---- background: warm room bokeh (code)
        gy = GY / H
        top, bot = np.array(hexbgr('#f4e4d2'), np.float32), np.array(hexbgr('#e2ae8e'), np.float32)
        self.base = (top * (1 - gy[..., None]) + bot * gy[..., None]).astype(np.float32)
        win = np.exp(-(((GX - 260) / 700.0) ** 2 + ((GY - 60) / 520.0) ** 2)).astype(np.float32)
        self.base += win[..., None] * np.array(hexbgr('#fff3df'), np.float32) * 0.35
        rng = np.random.RandomState(77)
        self.bokeh = []
        for _ in range(30):
            r = float(rng.choice([34, 48, 62, 80, 110, 150]))
            col = [hexbgr('#ffd9a0'), hexbgr('#ffe9c9'), hexbgr('#ffc38a'), hexbgr('#fff6e8'),
                   hexbgr('#cfe3ea')][rng.randint(5)]
            self.bokeh.append(dict(x=rng.uniform(-100, W + 100), y=rng.uniform(-80, H * 0.85), r=r, col=col,
                                   k=rng.uniform(0.06, 0.2), vx=rng.uniform(-6, 6), vy=rng.uniform(-4, 3),
                                   ph=rng.uniform(0, 6.28), f=rng.uniform(0.15, 0.45)))
        self.discs = {}
        for b in self.bokeh:
            r = int(b["r"])
            if r not in self.discs:
                s = 2 * r + 9
                yy, xx = np.mgrid[0:s, 0:s].astype(np.float32) - s / 2
                d = np.sqrt(xx * xx + yy * yy)
                body = np.clip((r - d) / 3.0 + 0.5, 0, 1)
                ring = np.exp(-((d - r * 0.92) / (r * 0.07)) ** 2) * 0.35
                self.discs[r] = (body * 0.75 + ring * body).astype(np.float32)
        self.vig = vignette_map(0.22, 2.2)
        self.spr = {rr: soft_disc(rr) for rr in (1.8, 2.6, 3.6)}
        self.motes = [dict(x=rng.uniform(0, W), y=rng.uniform(0, H), vx=rng.uniform(4, 14), vy=rng.uniform(-14, -4),
                           r=float(rng.choice([1.8, 2.6, 3.6])), k=rng.uniform(0.15, 0.5), ph=rng.uniform(0, 6.28))
                      for _ in range(26)]
        self.title = mg.text_sprite("ゲンとモカ", mg.BRUSH, 112, None, color=hexbgr('#233154'), pad=10) if title else None
        self.title_glow = mg.text_sprite("ゲンとモカ", mg.BRUSH, 112, None, color=hexbgr('#fff7ea'), pad=10) if title else None

    # ------------------------------------------------------------------------------------------ motion
    def pose(self, t):
        br = 0.5 - 0.5 * math.cos(2 * math.pi * t / 4.2)
        # woman
        sw = math.sin(2 * math.pi * t / 6.5)
        self.w_head.rot = math.radians(0.9 * sw)
        self.w_head.dy = 1.0 * math.sin(2 * math.pi * t / 6.5 + 1.1)
        dsw = math.cos(2 * math.pi * t / 6.5)  # head angular velocity drives the earrings a little
        e1 = 4.5 * math.sin(2 * math.pi * t / 1.35) * (0.55 + 0.45 * math.sin(2 * math.pi * t / 5.1)) - 3.0 * dsw
        e2 = 4.0 * math.sin(2 * math.pi * t / 1.28 + 1.3) * (0.55 + 0.45 * math.sin(2 * math.pi * t / 4.7 + 1)) - 3.0 * dsw
        self.w_ear_l.rot = math.radians(e1)
        self.w_ear_r.rot = math.radians(e2)
        self.w_breath.dy = -1.3 * br
        wb = blink_curve(t, 1.55) + blink_curve(t, 5.1) + blink_curve(t, 7.05, depth=0.95)
        for e in self.eyes_w:
            e.c = min(1.0, wb)
        # Moka
        tilt = keys(t, [(0, 0), (1.9, 0), (2.45, 4.2), (3.9, 4.2), (4.45, 0.0)])
        self.k_head.rot = math.radians(tilt)
        self.k_ear_l.rot = math.radians(flick(t, 0.85, -5.0) + flick(t, 6.9, -4.0))
        self.k_ear_r.rot = math.radians(flick(t, 3.05, 5.0))
        self.k_breath.scale = 1 + 0.006 * (0.5 - 0.5 * math.cos(2 * math.pi * t / 2.3))
        slow = keys(t, [(0, 0), (5.35, 0), (5.8, 0.72), (6.2, 0.72), (6.75, 0.0)])
        for e in self.eyes_k:
            e.c = slow + blink_curve(t, 1.2, depth=0.9) * (1 - slow)
        # Gen
        self.d_head.rot = math.radians(1.1 * math.sin(2 * math.pi * t / 7.0 + 0.6))
        self.d_ear_l.rot = math.radians(flick(t, 1.15, -7.0) + flick(t, 6.3, -4.0))
        self.d_ear_r.rot = math.radians(flick(t, 4.45, 7.0))
        sn = 0.0
        for t0 in (2.3, 2.46, 2.62):
            x = t - t0
            if 0 <= x <= 0.11:
                sn += math.sin(math.pi * x / 0.11)
        self.d_nose.dy = -1.8 * sn
        self.d_breath.scale = 1 + 0.006 * br
        db = blink_curve(t, 3.35) + blink_curve(t, 7.35)
        for e in self.eyes_d:
            e.c = min(1.0, db)

    def camera(self, t):
        e = smooth(0, self.dur, t)
        z0 = W / 1448.0
        z = z0 * (1.012 + 0.045 * e)
        return Cam(724 + 14 * e, 505 + 16 * e, z)

    def hair(self, t):
        def f(u, v):
            wl = sample(self.hair_l, u, v)
            wr = sample(self.hair_r, u, v)
            n1 = sample(self.nA, u * 0.35 + 40, v * 0.9 - 70 * t + 300)
            n2 = sample(self.nB, u * 0.35 + 90, v * 0.9 - 60 * t + 500)
            gust = 0.75 + 0.25 * math.sin(2 * math.pi * t / 3.7)
            du = (wl * 6.0 + wr * 3.5) * n1 * gust
            dv = (wl * 1.6 + wr * 1.0) * n2 * gust
            return du, dv
        return f

    def background(self, t, cam):
        img = self.base.copy()
        # bokeh drift with a little parallax against the camera move
        px = (cam.cx - 724) * 0.35 * cam.z
        py = (cam.cy - 505) * 0.35 * cam.z
        for b in self.bokeh:
            x = b["x"] + b["vx"] * t - px
            y = b["y"] + b["vy"] * t - py
            k = b["k"] * (0.75 + 0.25 * math.sin(2 * math.pi * b["f"] * t + b["ph"]))
            d = self.discs[int(b["r"])]
            hs = d.shape[0] // 2
            x0, y0 = int(x) - hs, int(y) - hs
            x1, y1 = x0 + d.shape[1], y0 + d.shape[0]
            sx0, sy0 = max(0, -x0), max(0, -y0)
            sx1, sy1 = d.shape[1] - max(0, x1 - W), d.shape[0] - max(0, y1 - H)
            if sx1 <= sx0 or sy1 <= sy0:
                continue
            reg = img[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1]
            dd = d[sy0:sy1, sx0:sx1, None] * k
            reg += dd * (np.array(b["col"], np.float32) - reg * 0.55)
        return img

    def frame(self, t):
        self.pose(t)
        cam = self.camera(t)
        bg = self.background(t, cam)
        u, v = cam.inverse_grid()
        uu, vv = warp_coords(u, v, self.handles, [self.hair(t)] + [e.field for e in self.eyes])
        rgbp, a = self.subj.render(uu * U, vv * U)
        shade = np.ones_like(u)
        for e in self.eyes:
            e.shade(u, v, shade)
        rgbp = rgbp * shade[..., None]
        # light wrap + warm rim from the window (upper left)
        ab = cv2.GaussianBlur(a, (0, 0), 6)
        edge = np.clip(ab - cv2.GaussianBlur(a, (0, 0), 1.5) * 0 - a * 0.0, 0, 1)
        gx_ = cv2.Sobel(ab, cv2.CV_32F, 1, 0, ksize=3)
        gy_ = cv2.Sobel(ab, cv2.CV_32F, 0, 1, ksize=3)
        rim = np.clip((gx_ * 0.7 + gy_ * 0.7) * 3.0, 0, 1) * a  # facing the upper-left light
        bgb = cv2.GaussianBlur(bg, (0, 0), 12)
        wrap = np.clip(a - cv2.erode(a, np.ones((5, 5), np.uint8)), 0, 1)
        subj = rgbp + (bgb * 0.28 * wrap[..., None]) * a[..., None] \
            + rim[..., None] * np.array(hexbgr('#ffe7c4'), np.float32) * 0.22
        img = subj + bg * (1 - a[..., None])
        # warm grade + motes
        img[..., 2] *= 1.02
        img[..., 0] *= 0.985
        for m in self.motes:
            x = (m["x"] + m["vx"] * t + 8 * math.sin(0.7 * t + m["ph"])) % W
            y = (m["y"] + m["vy"] * t) % H
            tw = 0.6 + 0.4 * math.sin(1.9 * t + m["ph"] * 2)
            add_sprite(img, self.spr[m["r"]], x, y, (0.8, 0.92, 1.0), m["k"] * tw * 0.6)
        img = bloom(img, 0.85, 0.22, 20)
        img = img * self.vig[..., None]
        if self.title is not None:
            e = smooth(5.4, 6.3, t)
            if e > 0:
                y = 70 + 16 * (1 - e)
                mg.blit(img, self.title_glow, 74, y + 3, 0.55 * e)
                mg.blit(img, self.title, 70, y, e)
        return img
