"""Shot 3 — several pose images -> big motion. 8 public-domain Muybridge frames (1887):
pose sheet -> zoom into panel 1 -> playback 'on twos' (15 poses/s), aligned on the head."""
import glob
import math
import numpy as np
import cv2
from engine import W, H, smooth, vignette_map, GX, GY
import mg
from shot2 import NAVY, ORANGE, CREAM, hexbgr

HEADS = [760, 670, 660, 720, 745, 820, 700, 660]  # head x in each 960px frame (hand-measured)
ANCHOR = 720
SEPIA_LO = np.array(hexbgr('#231a14'), np.float32)
SEPIA_HI = np.array(hexbgr('#f3e3c6'), np.float32)


class Shot3:
    dur = 4.0

    def __init__(self, src_dir):
        fs = sorted(glob.glob(f"{src_dir}/ike_*.jpg"))
        self.frames = []
        for f, hx in zip(fs, HEADS):
            g = cv2.imread(f, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
            g = (g - g.mean()) / (g.std() + 1e-6) * 0.19 + 0.47  # match exposure across the 8 photos
            g = np.clip(g, 0, 1)
            M = np.float32([[1, 0, ANCHOR - hx], [0, 1, 0]])
            g = cv2.warpAffine(g, M, (960, 545), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            col = SEPIA_LO * (1 - g[..., None]) + SEPIA_HI * g[..., None]
            self.frames.append(col.astype(np.float32))
        self.vig = vignette_map(0.25, 2.0)
        self.num = [mg.text_sprite(str(i + 1), mg.SANS, 30, 800, color=CREAM, pad=2) for i in range(8)]
        self.badge = mg.rounded_rect(46, 46, 23, ORANGE, 1.0)
        self.hdr = mg.text_sprite("POSE SHEET  ·  8 IMAGES", mg.SANS, 30, 800, color=CREAM, pad=2, tracking=6)
        rng = np.random.RandomState(31)
        self.lines = [dict(y=rng.uniform(0, H), len=rng.uniform(180, 620), v=rng.uniform(1400, 2600),
                           x0=rng.uniform(0, 4000), th=rng.choice([2, 3, 4]), k=rng.uniform(0.06, 0.18))
                      for _ in range(38)]
        # sheet layout
        self.pw, self.ph = 400, 227
        gap = 24
        tw, th = 4 * self.pw + 3 * gap, 2 * self.ph + gap
        x0, y0 = (W - tw) / 2, 290
        self.cells = [(x0 + (i % 4) * (self.pw + gap), y0 + (i // 4) * (self.ph + gap)) for i in range(8)]
        # playback panel
        self.big = (W / 2 - 700, H / 2 - 394 + 10, 1400, 788)

    def panel(self, idx, w, h):
        """frame idx cropped/scaled to fill w x h (head-aligned)"""
        f = self.frames[idx]
        s = max(w / 960.0, h / 545.0) * 1.12
        M = np.float32([[s, 0, w / 2 - s * 480], [0, s, h / 2 - s * 262]])
        return cv2.warpAffine(f, M, (int(w), int(h)), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    def put(self, img, pic, x, y, k=1.0, radius=14, border=None):
        h, w = pic.shape[:2]
        rr = mg.rounded_rect(w, h, radius, (1, 1, 1), 1.0)[..., 3]
        spr = np.dstack([pic * rr[..., None], rr]).astype(np.float32)
        if border is not None:
            b = mg.rounded_rect(w + 8, h + 8, radius + 4, border, 1.0)
            mg.blit(img, b, x - 4, y - 4, k)
        mg.blit(img, spr, x, y, k)

    def frame(self, t):
        img = np.empty((H, W, 3), np.float32)
        img[:] = np.array(NAVY, np.float32)
        # speed lines (the dog runs to the right -> lines stream left)
        run = smooth(0.9, 1.4, t)
        for L in self.lines:
            x = W + 700 - ((L["x0"] + L["v"] * t) % (W + 1400))
            k = L["k"] * (0.35 + 0.65 * run)
            x1 = int(x + L["len"])
            cv2.line(img, (int(x), int(L["y"])), (x1, int(L["y"])), tuple(float(c) * 0.0 + (0.97 * k + NAVY[i] * (1 - k))
                     for i, c in enumerate(CREAM)), int(L["th"]), cv2.LINE_AA)
        if t < 1.35:
            # pose sheet
            fade_out = 1 - smooth(0.95, 1.2, t)
            mg.blit(img, self.hdr, (W - self.hdr.shape[1]) / 2, 200, smooth(0.0, 0.25, t) * fade_out)
            for i, (cx, cy) in enumerate(self.cells):
                ti = 0.05 * i
                e = smooth(ti, ti + 0.22, t)
                if e <= 0:
                    continue
                if i == 0 and t > 0.95:
                    continue
                sc = 0.86 + 0.14 * e
                w, h = int(self.pw * sc), int(self.ph * sc)
                pic = self.panel(i, w, h)
                x = cx + (self.pw - w) / 2
                y = cy + (self.ph - h) / 2
                self.put(img, pic, x, y, e * fade_out, 12, ORANGE)
                mg.blit(img, self.badge, x - 12, y - 12, e * fade_out)
                n = self.num[i]
                mg.blit(img, n, x - 12 + 23 - n.shape[1] / 2, y - 12 + 23 - n.shape[0] / 2, e * fade_out)
            if t > 0.95:
                u = smooth(0.95, 1.35, t)
                u = 1 - (1 - u) ** 3
                cx, cy = self.cells[0]
                bx, by, bw, bh = self.big
                x, y = cx + (bx - cx) * u, cy + (by - cy) * u
                w, h = self.pw + (bw - self.pw) * u, self.ph + (bh - self.ph) * u
                pic = self.panel(0, int(w), int(h))
                self.put(img, pic, x, y, 1.0, 12 + 10 * u, ORANGE)
        else:
            idx = int((t - 1.35) * 15) % 8
            bx, by, bw, bh = self.big
            pic = self.panel(idx, bw, bh)
            self.put(img, pic, bx, by, 1.0, 22, ORANGE)
            n = self.num[idx]
            mg.blit(img, self.badge, bx + 22, by + 22)
            mg.blit(img, n, bx + 22 + 23 - n.shape[1] / 2, by + 22 + 23 - n.shape[0] / 2)
        img = img * self.vig[..., None]
        return img
