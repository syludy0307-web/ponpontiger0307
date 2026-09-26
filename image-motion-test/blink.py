"""Blink from a single image (no closed-eye picture).
The skin/fur above the eye slides down over the eyeball (inverse map in the eye's local frame:
s along the eye axis, q toward the chin). A short blend band + a soft lash-line shade hide the seam."""
import math
import numpy as np


class Eye:
    def __init__(self, cx, cy, angle_deg, a, v_up, v_lo, L, meet=0.9, low_rise=0.15, band=3.0,
                 lash=0.3, lash_w=2.0):
        self.cx, self.cy = cx, cy
        self.ca, self.sa = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
        self.a, self.v_up, self.v_lo, self.L = a, v_up, v_lo, L
        self.meet, self.low_rise, self.band = meet, low_rise, band
        self.lash, self.lash_w = lash, lash_w
        self.c = 0.0
        pad = max(a * 1.5, L + abs(v_up) + v_lo) * 1.3
        self.box = (cx - pad, cy - pad, cx + pad, cy + pad)

    def _local(self, u, v):
        x0, y0, x1, y1 = self.box
        m = (u > x0) & (u < x1) & (v > y0) & (v < y1)
        U, V = u[m] - self.cx, v[m] - self.cy
        s = U * self.ca + V * self.sa
        q = -U * self.sa + V * self.ca
        prof = np.clip(1 - (s / (self.a * 1.08)) ** 2, 0, 1) ** 0.8
        wx = np.clip(1 - (np.abs(s) - self.a) / (0.35 * self.a), 0, 1)
        open_h = self.v_lo - self.v_up
        drop = self.c * self.meet * open_h * prof
        rise = self.c * self.low_rise * open_h * prof
        edge = self.v_up + drop
        return m, s, q, prof, wx, drop, rise, edge

    def field(self, u, v):
        du = np.zeros_like(u)
        dv = np.zeros_like(v)
        if self.c <= 1e-4:
            return du, dv
        m, s, q, prof, wx, drop, rise, edge = self._local(u, v)
        if not m.any():
            return du, dv
        v_top = self.v_up - self.L
        low_edge = np.maximum(self.v_lo - rise, edge + self.band)
        L2 = self.L * 0.5
        k = self.L / (self.L + drop + 1e-6)
        src = q.copy()
        up = (q >= v_top) & (q <= edge)
        src = np.where(up, v_top + (q - v_top) * k, src)                 # lid skin slides/stretches down
        bnd = (q > edge) & (q < edge + self.band)
        tb = np.clip((q - edge) / self.band, 0, 1)
        src = np.where(bnd, self.v_up * (1 - tb) + q * tb, src)             # short blend: no hard seam
        lo = (q >= low_edge) & (q <= self.v_lo + L2)
        src = np.where(lo, self.v_lo + (q - low_edge) * (L2 / np.maximum(self.v_lo + L2 - low_edge, 1e-3)), src)
        dq = (src - q) * wx
        du[m] = -self.sa * dq
        dv[m] = self.ca * dq
        return du, dv

    def shade(self, u, v, out):
        """multiply 'out' (same shape as u) by a soft lash-line darkening along the moving lid edge"""
        if self.c <= 1e-4:
            return
        m, s, q, prof, wx, drop, rise, edge = self._local(u, v)
        if not m.any():
            return
        g = np.exp(-((q - edge - self.band * 0.5) / self.lash_w) ** 2) * wx * prof * min(1.0, self.c * 2.5)
        out[m] *= (1 - self.lash * g)


def blink_curve(t, t0, close=0.075, hold=0.04, open_=0.13, depth=1.0):
    x = t - t0
    if x < 0 or x > close + hold + open_:
        return 0.0
    if x < close:
        u = x / close
        return depth * (u * u * (3 - 2 * u))
    if x < close + hold:
        return depth
    u = (x - close - hold) / open_
    return depth * (1 - u * u * (3 - 2 * u))
