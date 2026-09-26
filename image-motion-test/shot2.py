"""Shot 2 — one cut-out photo + code motion graphics, grooving to the beat (120 BPM).
Motions on the dog: head bob + side tilt, panting jaw, tail wag, ear flicks, chest pant,
body squash/stretch; camera beat punches. Background, text, leaves, rings, ticker are all code."""
import math
import numpy as np
import cv2
from engine import (W, H, Cam, Handle, Layer, warp_coords, sample, poly_mask, keys, flick, smooth,
                    bloom, vignette_map, GX, GY, soft_disc)
import mg

BPM = 120.0
SPB = 60.0 / BPM


def beat_env(t, t0, decay=0.14):
    """sum of decaying pulses on every beat after t0"""
    if t < t0:
        return 0.0
    ph = (t - t0) % SPB
    return math.exp(-ph / decay)


def hexbgr(h):
    h = h.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (b / 255.0, g / 255.0, r / 255.0)


NAVY = hexbgr('#1d2b4f')
ORANGE = hexbgr('#f0874a')
CORAL = hexbgr('#f26b5b')
CREAM = hexbgr('#fbf1e3')
PEACH = hexbgr('#f6cfae')
GOLD = hexbgr('#f5b942')


def maple_poly(r):
    """maple leaf outline (points up), unit radius r: 5 broad lobes with serrated edges + stem notch"""
    lobes = [(-90, 1.0), (-35, 0.9), (-145, 0.9), (20, 0.62), (160, 0.62)]
    pts = []
    for i in range(360):
        th = math.radians(i - 90)
        d = math.degrees(th)
        best = 0.0
        for ang, ln in lobes:
            dd = (d - ang + 180) % 360 - 180
            best = max(best, ln * math.exp(-(dd / 24.0) ** 2))
        rr = 0.30 + 0.70 * best
        rr *= 1 + 0.07 * math.cos(math.radians(i) * 14)  # serration
        if abs(((d - 90) + 180) % 360 - 180) < 16:  # notch where the stem is (bottom)
            rr = min(rr, 0.28)
        pts.append((math.cos(th) * rr * r, math.sin(th) * rr * r))
    pts.append((0.03 * r, 0.28 * r))
    pts.append((0.03 * r, 0.75 * r))
    pts.append((-0.03 * r, 0.75 * r))
    pts.append((-0.03 * r, 0.28 * r))
    return np.array(pts, np.float32)


class Shot2:
    dur = 7.0

    def __init__(self, work):
        fg = np.load(f"{work}/a03_fg.npy")
        a = np.load(f"{work}/a03_alpha.npy")
        # mild pre-blur against aliasing (the dog is shown at ~0.8x)
        self.dog = Layer(cv2.GaussianBlur(fg, (0, 0), 0.5), a)
        self.src_a = a
        S = a.shape
        self.head = Handle(poly_mask(S, [[[722, 262], [1108, 262], [1108, 640], [1070, 772], [758, 782],
                                          [712, 600]]], 38), (905, 800))
        self.jaw = Handle(poly_mask(S, [[[836, 546], [1022, 546], [1016, 628], [848, 628]]], 10), (930, 560))
        self.tail = Handle(poly_mask(S, [[[92, 296], [488, 296], [494, 562], [432, 642], [250, 748],
                                          [92, 740]]], 22), (440, 600))
        self.ear_l = Handle(poly_mask(S, [[[731, 272], [832, 290], [852, 447], [746, 457]]], 9), (800, 445))
        self.ear_r = Handle(poly_mask(S, [[[986, 272], [1100, 268], [1097, 432], [998, 447]]], 9), (1035, 440))
        self.chest = Handle(poly_mask(S, [[[758, 640], [1064, 640], [1064, 1004], [758, 1004]]], 45), (910, 820))
        # order: small parts first so the big head rotation carries them
        self.handles = [self.jaw, self.ear_l, self.ear_r, self.head, self.chest, self.tail]

        self.vig = vignette_map(0.20, 2.4)
        # background gradient (precomputed)
        gx = GX / W
        gy = GY / H
        k = np.clip(0.55 * gx + 0.45 * gy, 0, 1)[..., None]
        self.base = (np.array(CREAM, np.float32) * (1 - k) + np.array(PEACH, np.float32) * k).astype(np.float32)
        # diagonal stripes mask (scrolls)
        self.diag = ((GX + GY) / 1.0).astype(np.float32)
        # halftone dots (bottom-left corner)
        self.dots = np.zeros((H, W), np.float32)
        for yy in range(560, H, 22):
            for xx in range(0, 620, 22):
                d = math.hypot(xx - 0, yy - H) / 700.0
                r = max(0.0, 6.5 * (1 - d))
                if r > 0.6:
                    cv2.circle(self.dots, (xx + (11 if (yy // 22) % 2 else 0), yy), int(round(r)), 1.0, -1, cv2.LINE_AA)
        # text sprites
        self.big = mg.text_sprite("ゲン", mg.BRUSH, 330, None, color=NAVY, pad=10)
        self.big_sh = mg.text_sprite("ゲン", mg.BRUSH, 330, None, color=ORANGE, pad=10)
        self.gen = mg.text_sprite("GEN", mg.SANS, 64, 900, color=NAVY, pad=4, tracking=22)
        self.akita = mg.text_sprite("AKITA INU  ·  秋田犬", mg.SANS, 30, 700, color=NAVY, pad=4, tracking=4)
        self.tick = mg.text_sprite("GEN & MOKA   ·   ゲンとモカ   ·   ", mg.SANS, 40, 800, color=CREAM, pad=4,
                                   tracking=2)
        self.leaf = maple_poly(1.0)
        rng = np.random.RandomState(9)
        self.leaves = [dict(x=rng.uniform(-100, 2000), y0=rng.uniform(-900, 900), vy=rng.uniform(90, 170),
                            sway=rng.uniform(30, 90), f=rng.uniform(0.3, 0.8), ph=rng.uniform(0, 6.28),
                            r=rng.uniform(18, 40), rot=rng.uniform(0, 6.28), vr=rng.uniform(-2.2, 2.2),
                            col=[ORANGE, CORAL, GOLD, hexbgr('#e25a3a')][rng.randint(4)],
                            front=rng.rand() < 0.35) for _ in range(16)]
        self.glow = soft_disc(60.0)

    # --------------------------------------------------------------------------- motion
    def pose(self, t):
        beats = t / SPB
        ph = beats % 1.0
        bob = 0.5 + 0.5 * math.cos(2 * math.pi * ph)  # 1 on the beat
        sway = math.sin(2 * math.pi * t / (4 * SPB))  # tilt left/right over 4 beats
        intro = smooth(0.0, 0.5, t)
        self.head.rot = math.radians(3.2 * sway * intro)
        self.head.dy = 8.0 * bob * intro
        self.head.dx = 3.0 * sway * intro
        pant = 0.5 - 0.5 * math.cos(2 * math.pi * 2 * ph)
        self.jaw.dy = 3.4 * pant
        self.chest.scale = 1 + 0.007 * pant
        self.tail.rot = math.radians(7.5 * math.sin(2 * math.pi * 2 * beats) * intro)
        el = sum(flick(t, (b + 0.02) * SPB, -9.0) for b in (3, 7, 11))
        er = sum(flick(t, (b + 0.02) * SPB, 9.0) for b in (5, 9, 13))
        self.ear_l.rot = math.radians(el)
        self.ear_r.rot = math.radians(er)
        return bob

    def draw_leaf(self, img, x, y, r, rot, col, k=1.0):
        c, s = math.cos(rot), math.sin(rot)
        P = self.leaf * r
        pts = np.stack([P[:, 0] * c - P[:, 1] * s + x, P[:, 0] * s + P[:, 1] * c + y], 1)
        x0, y0 = int(max(0, pts[:, 0].min() - 3)), int(max(0, pts[:, 1].min() - 3))
        x1, y1 = int(min(W, pts[:, 0].max() + 3)), int(min(H, pts[:, 1].max() + 3))
        if x1 <= x0 or y1 <= y0:
            return
        m = np.zeros((y1 - y0, x1 - x0), np.float32)
        cv2.fillPoly(m, [np.int32((pts - [x0, y0]) * 16)], 1.0, cv2.LINE_AA, shift=4)
        reg = img[y0:y1, x0:x1]
        reg *= (1 - k * m[..., None])
        reg += (k * m)[..., None] * np.array(col, np.float32)

    def frame(self, t):
        bob = self.pose(t)
        kick = beat_env(t, 0.0, 0.16)
        down = beat_env(t, 0.0, 0.22) if int(t / SPB) % 2 == 0 else 0.0
        img = self.base.copy()
        # scrolling diagonal stripes
        st = (np.sin((self.diag + 60 * t) / 26.0) > 0.55).astype(np.float32)
        img = img * (1 - 0.05 * st[..., None]) + 0.05 * st[..., None] * np.array(ORANGE, np.float32)
        # halftone dots
        img = img * (1 - 0.12 * self.dots[..., None]) + 0.12 * self.dots[..., None] * np.array(CORAL, np.float32)

        # global camera punch (screen space zoom about centre) + slow push
        zc = 1.0 + 0.018 * down + 0.03 * smooth(0, 7.0, t)
        # sun disc behind the dog
        scx, scy = 1265, 520
        cx_, cy_ = (scx - W / 2) * zc + W / 2, (scy - H / 2) * zc + H / 2
        R = (360 + 14 * kick) * zc
        sun = np.zeros((H, W), np.float32)
        cv2.circle(sun, (int(cx_ * 4), int(cy_ * 4)), int(R * 4), 1.0, -1, cv2.LINE_AA, shift=2)
        glow = cv2.GaussianBlur(sun, (0, 0), 30)
        img = img * (1 - sun[..., None]) + sun[..., None] * np.array(ORANGE, np.float32)
        img += 0.18 * glow[..., None] * np.array(GOLD, np.float32) * (1 - sun[..., None])
        # rings expanding on every beat
        for back in range(3):
            bt = math.floor(t / SPB) - back
            if bt < 0:
                continue
            age = (t - bt * SPB) / (3 * SPB)
            if age > 1:
                continue
            rr = R + (60 + 520 * (1 - (1 - age) ** 2)) * zc
            a = 0.45 * (1 - age)
            ring = np.zeros((H, W), np.float32)
            cv2.circle(ring, (int(cx_ * 4), int(cy_ * 4)), int(rr * 4), 1.0, int(5 * zc), cv2.LINE_AA, shift=2)
            img = img * (1 - a * ring[..., None]) + a * ring[..., None] * np.array(CREAM, np.float32)

        # big brush text (behind), slides in
        e = 1 - (1 - smooth(0.05, 0.7, t)) ** 2
        tx = -420 + 520 * e
        sc = (1.0 + 0.035 * down) * zc
        mg.blit_xform(img, self.big_sh, tx + 10 + 330 / 2 + 150, 430 + 10, sc, -4, 0.9 * e)
        mg.blit_xform(img, self.big, tx + 330 / 2 + 150, 430, sc, -4, e)
        mg.blit(img, self.gen, 132, 690 + 20 * (1 - e), e)
        mg.blit(img, self.akita, 138, 776 + 20 * (1 - e), e)

        # back leaves
        for L in self.leaves:
            if L["front"]:
                continue
            y = (L["y0"] + L["vy"] * (t + 2)) % 1400 - 150
            x = L["x"] + L["sway"] * math.sin(L["f"] * 6.283 * t + L["ph"])
            self.draw_leaf(img, x, y, L["r"] * 0.8, L["rot"] + L["vr"] * t, L["col"], 0.55)

        # the dog (photo cut-out) with rig + squash/stretch on the beat
        zd = 0.70 * zc
        feet = (600.0, 1500.0)
        pos = ((1265 - W / 2) * zc + W / 2, (1100 - H / 2) * zc + H / 2)
        sy = 1 - 0.012 * kick + 0.004 * (1 - bob)
        sx = 1 + 0.006 * kick
        X = (GX - pos[0]) / (zd * sx) + feet[0]
        Y = (GY - pos[1]) / (zd * sy) + feet[1]
        u, v = warp_coords(X.astype(np.float32), Y.astype(np.float32), self.handles)
        rgbp, a = self.dog.render(u, v)
        a_c = np.clip((a - 0.18) / 0.82, 0, 1)
        rgbp = rgbp * (a_c / np.maximum(a, 1e-4))[..., None]
        a = a_c
        # drop shadow on the background
        sh = cv2.GaussianBlur(a, (0, 0), 16)
        M = np.float32([[1, 0, 26], [0, 1, 18]])
        sh = cv2.warpAffine(sh, M, (W, H))
        img = img * (1 - 0.22 * sh[..., None])
        # rim light from the sun behind
        edge = np.clip(a - cv2.GaussianBlur(a, (0, 0), 5), 0, 1) * 2.2
        rim = np.clip(edge, 0, 1)[..., None] * np.array(hexbgr('#ffe2b8'), np.float32) * 0.28
        warm = rgbp * np.array([0.97, 1.0, 1.03], np.float32)
        img = warm + rim * a[..., None] + img * (1 - a[..., None])

        # front leaves
        for L in self.leaves:
            if not L["front"]:
                continue
            y = (L["y0"] + L["vy"] * 1.3 * (t + 2)) % 1400 - 150
            x = L["x"] + L["sway"] * math.sin(L["f"] * 6.283 * t + L["ph"])
            self.draw_leaf(img, x, y, L["r"] * 1.25, L["rot"] + L["vr"] * t, L["col"], 0.95)

        # ticker band at the bottom (hides the paws in the grass)
        by = 972
        img[by:, :] = img[by:, :] * 0.0 + np.array(NAVY, np.float32)
        img[by - 6:by, :] = np.array(ORANGE, np.float32)
        tw = self.tick.shape[1]
        off = -((t * 220) % tw)
        x = off
        while x < W:
            mg.blit(img, self.tick, x, by + 26)
            x += tw
        img = bloom(img, 0.86, 0.18, 16)
        img = img * self.vig[..., None]
        return img
