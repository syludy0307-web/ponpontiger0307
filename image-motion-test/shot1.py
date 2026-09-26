"""Shot 1 — one photo only: dozing Akita close-up.
Motions: breathing, slow nod + 'catch', ear flicks, nose sniffs, fur flutter, grass wind,
push-in with parallax, warm light, dust motes."""
import math
import numpy as np
import cv2
from engine import (W, H, Cam, Handle, Layer, warp_coords, sample, poly_mask, noise_table, keys, flick,
                    smooth, soft_disc, add_sprite, bloom, vignette_map, GX, GY)

U = 2.0  # pre-upscale factor of the source layers


def unsharp(img, sigma=1.2, amount=0.45):
    return np.clip(img + amount * (img - cv2.GaussianBlur(img, (0, 0), sigma)), 0, 1)


class Shot1:
    dur = 5.0

    def __init__(self, work):
        fg = np.load(f"{work}/a02_fg.npy")
        a = np.load(f"{work}/a02_alpha.npy")
        plate = np.load(f"{work}/a02_plate.npy")
        h, w = a.shape
        self.h, self.w = h, w
        up = (int(w * U), int(h * U))
        ap = cv2.resize(a, up, interpolation=cv2.INTER_LANCZOS4)
        rp = cv2.resize(fg * a[..., None], up, interpolation=cv2.INTER_LANCZOS4)
        rp = unsharp(rp, 1.3, 0.35)
        ap = np.clip(ap, 0, 1)
        self.fg = Layer(np.zeros_like(rp), ap)
        self.fg.rgba[..., :3] = np.clip(rp, 0, ap[..., None])
        # background: depth-of-field blur, then upscale
        pb = cv2.GaussianBlur(plate, (0, 0), 2.6)
        self.bg = Layer(cv2.resize(pb, up, interpolation=cv2.INTER_CUBIC))

        S = (h, w)
        self.breath = Handle(poly_mask(S, [[[600, 430], [1024, 280], [1024, 768], [540, 768]]], 70), (830, 640))
        self.head = Handle(poly_mask(S, [[[240, 55], [560, 75], [820, 140], [900, 380], [760, 620], [560, 768],
                                          [180, 740], [172, 560], [230, 420]]], 45), (905, 730))
        self.ear_n = Handle(poly_mask(S, [[[575, 186], [640, 194], [722, 282], [765, 400], [700, 428], [600, 345],
                                           [570, 250]]], 10), (705, 398))
        self.ear_f = Handle(poly_mask(S, [[[250, 58], [330, 76], [445, 116], [450, 238], [352, 260],
                                           [294, 170]]], 10), (425, 236))
        self.nose = Handle(poly_mask(S, [[[185, 575], [305, 575], [330, 705], [185, 705]]], 22), (250, 640))
        self.handles = [self.breath, self.head, self.ear_n, self.ear_f, self.nose]

        # fur flutter: only the outer rim of the silhouette moves with the wind
        hard = (a > 0.5).astype(np.uint8)
        core = cv2.erode(hard, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))).astype(np.float32)
        band = np.clip(cv2.GaussianBlur(1 - core, (0, 0), 6) * cv2.GaussianBlur(hard.astype(np.float32), (0, 0), 6), 0, 1)
        self.band = band.astype(np.float32)
        self.nA = noise_table(1400, 1800, 46, 11)
        self.nB = noise_table(1400, 1800, 46, 12)
        self.gA = noise_table(1400, 1800, 70, 21)
        self.gB = noise_table(1400, 1800, 70, 22)
        self.vig = vignette_map(0.24, 2.0)
        # light: soft sun glow from the top right + faint beams
        d2 = (GX - 2050) ** 2 + (GY + 200) ** 2
        self.glow = np.exp(-d2 / (2 * 780.0 ** 2)).astype(np.float32)
        ang = math.radians(-38)
        proj = (GX - 2050) * math.cos(ang) - (GY + 200) * math.sin(ang)
        self.proj = proj.astype(np.float32)
        # dust motes (deterministic)
        rng = np.random.RandomState(5)
        n = 34
        self.motes = [dict(x=rng.uniform(600, 2000), y=rng.uniform(-50, 1100), vx=rng.uniform(8, 26),
                           vy=rng.uniform(-22, -6), a=rng.uniform(6, 22), f=rng.uniform(0.2, 0.6),
                           ph=rng.uniform(0, 6.28), r=rng.choice([1.6, 2.2, 3.0, 4.2, 9.0, 16.0],
                                                                  p=[.26, .26, .2, .14, .09, .05]),
                           k=rng.uniform(0.25, 0.9)) for _ in range(n)]
        self.spr = {r: soft_disc(r) for r in (1.6, 2.2, 3.0, 4.2, 9.0, 16.0)}

    # ------------------------------------------------------------------ animation curves
    def pose(self, t):
        b = 0.5 - 0.5 * math.cos(2 * math.pi * t / 3.4)
        self.breath.scale = 1 + 0.007 * b
        self.breath.dy = -1.2 * b
        nod = keys(t, [(0, 0), (0.6, 0), (3.2, -1.6)]) if t < 3.2 else (
            keys(t, [(3.2, -1.6), (3.36, 0.55), (4.2, -0.25), (5.0, -0.7)]))
        self.head.rot = math.radians(nod)
        self.head.dy = -0.8 * b
        self.ear_n.rot = math.radians(flick(t, 1.35, 6.0) + flick(t, 3.24, 4.5) + 0.8 * smooth(3.2, 3.4, t))
        self.ear_f.rot = math.radians(flick(t, 2.45, 5.0) + flick(t, 3.27, 3.0))
        sn = 0.0
        for t0 in (1.95, 2.13, 2.31, 4.35, 4.53):
            tau = t - t0
            if 0 <= tau <= 0.12:
                sn += math.sin(math.pi * tau / 0.12)
        self.nose.dx = -1.1 * sn
        self.nose.dy = -2.3 * sn

    def camera(self, t):
        e = smooth(0, 5.0, t)
        z = 1.875 * (1.0 + 0.06 * e)
        cx, cy = lerp_(512, 532, e), lerp_(400, 416, e)
        fgcam = Cam(cx, cy, z)
        zb = 1.875 * (1.0 + 0.6 * 0.06 * e)
        bgcam = Cam(512 + 0.6 * (cx - 512), 400 + 0.6 * (cy - 400), zb)
        return fgcam, bgcam

    def frame(self, t):
        self.pose(t)
        fgcam, bgcam = self.camera(t)
        # background (wind in the grass)
        u, v = bgcam.inverse_grid()
        gx = sample(self.gA, u * 0.9 + 28 * t, v * 0.9 + 6 * t)
        gy = sample(self.gB, u * 0.9 + 28 * t + 300, v * 0.9 + 6 * t)
        low = np.clip((u - 0) / 1.0, 0, 1)  # (kept simple: uniform)
        ub, vb = u + 2.0 * gx * low, v + 0.8 * gy
        bg_rgb, _ = self.bg.render(ub * U, vb * U)
        # foreground dog
        u, v = fgcam.inverse_grid()

        def fur(uu, vv):
            w = sample(self.band, uu, vv)
            nx = sample(self.nA, uu * 1.0 + 55 * t, vv + 10 * t)
            ny = sample(self.nB, uu * 1.0 + 55 * t + 400, vv + 10 * t)
            return 1.3 * w * nx, 0.9 * w * ny

        uf, vf = warp_coords(u, v, self.handles, (fur,))
        rgbp, a = self.fg.render(uf * U, vf * U)
        img = rgbp + bg_rgb * (1 - a[..., None])

        # light: warm glow + slow beams (screen space), a little stronger on the fur than on the grass
        flick_l = 1 + 0.05 * math.sin(2 * math.pi * t / 2.7)
        beams = 0.5 + 0.5 * np.cos(self.proj / 95.0 + t * 0.35) * np.cos(self.proj / 37.0 - t * 0.2)
        L = self.glow * (0.13 + 0.07 * beams) * flick_l
        warm = np.array([0.55, 0.80, 1.0], np.float32)
        img = img + L[..., None] * warm * (0.7 + 0.5 * a[..., None])
        # dust motes, only where the light is
        for m in self.motes:
            x = (m["x"] + m["vx"] * t + m["a"] * math.sin(m["f"] * 6.283 * t + m["ph"])) % 2100 - 90
            y = (m["y"] + m["vy"] * t + 0.5 * m["a"] * math.cos(m["f"] * 5.1 * t + m["ph"])) % 1200 - 60
            gl = float(np.exp(-((x - 2050) ** 2 + (y + 200) ** 2) / (2 * 900.0 ** 2)))
            tw = 0.6 + 0.4 * math.sin(2.2 * t + m["ph"] * 3)
            k = m["k"] * gl * tw * (0.5 if m["r"] >= 9 else 1.0) * (0.25 if m["r"] >= 16 else 1.0)
            add_sprite(img, self.spr[m["r"]], x, y, (0.75, 0.9, 1.0), k)
        # grade
        img = bloom(img, 0.78, 0.28, 22)
        img = img * self.vig[..., None]
        img[..., 2] *= 1.03
        img[..., 0] *= 0.975
        return img


def lerp_(a, b, t):
    return a + (b - a) * t
