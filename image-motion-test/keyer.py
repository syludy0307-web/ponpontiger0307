"""Green-screen keys for the forest set (classical, no AI).
   diff key  : subjects without green (people, dogs, cats)
   chroma key: foliage that is itself greenish (grass/ferns) -> distance to the screen colour in CrCb"""
import cv2, numpy as np


def screen_color(I, boxes):
    s = np.concatenate([I[y0:y1, x0:x1].reshape(-1, 3) for (x0, y0, x1, y1) in boxes])
    return np.median(s, axis=0)


def edge_fix(F, alpha):
    w = (alpha > 0.97).astype(np.float32)
    Fi = np.zeros_like(F); D = np.zeros(alpha.shape, np.float32)
    for sig in (2, 4, 8, 16):
        num = cv2.GaussianBlur(F * w[..., None], (0, 0), sig); den = cv2.GaussianBlur(w, (0, 0), sig)
        take = (D < 1e-3) & (den > 1e-3)
        Fi[take] = num[take] / den[take][..., None]; D[take] = den[take]
    edge = (alpha < 0.97) & (alpha > 0)
    lum_o = F.mean(2, keepdims=True); lum_f = Fi.mean(2, keepdims=True)
    F2 = np.clip(Fi * (0.6 + 0.4 * lum_o / np.maximum(lum_f, 1e-3)), 0, 1)
    return np.where(edge[..., None] & (D[..., None] > 1e-3), F2, F).astype(np.float32)


def key_diff(I, C, d_fg=0.06, choke=True):
    b, g, r = I[..., 0], I[..., 1], I[..., 2]
    d = g - np.maximum(r, b)
    d_bg = float(C[1] - max(C[0], C[2]))
    a = np.clip((d_bg - d) / (d_bg - d_fg), 0, 1)
    a = np.where(a < 0.03, 0, np.where(a > 0.97, 1, a)).astype(np.float32)
    near = cv2.dilate((a > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51))) > 0
    a[(~near) & (a < 0.35)] = 0
    F = (I - (1 - a[..., None]) * C[None, None, :]) / np.maximum(a[..., None], 0.04)
    F = np.clip(F, 0, 1)
    F[..., 1] = np.minimum(F[..., 1], (F[..., 0] + F[..., 2]) * 0.5 + 0.03)
    F = np.where(a[..., None] > 0, F, 0)
    F = edge_fix(F, a)
    if choke:
        er = cv2.GaussianBlur(cv2.erode(a, np.ones((3, 3), np.uint8)), (0, 0), 0.7)
        a = np.minimum(a, np.maximum(er, (a > 0.99).astype(np.float32)))
    return F.astype(np.float32), a.astype(np.float32)


def key_chroma(I, C, r1=10.0, r2=34.0):
    y = cv2.cvtColor((I * 255).astype(np.uint8), cv2.COLOR_BGR2YCrCb).astype(np.float32)
    cs = cv2.cvtColor((C.reshape(1, 1, 3) * 255).astype(np.uint8), cv2.COLOR_BGR2YCrCb).astype(np.float32)[0, 0]
    dist = np.sqrt((y[..., 1] - cs[1]) ** 2 + (y[..., 2] - cs[2]) ** 2)
    a = np.clip((dist - r1) / (r2 - r1), 0, 1).astype(np.float32)
    near = cv2.dilate((a > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))) > 0
    a[(~near) & (a < 0.4)] = 0
    F = (I - (1 - a[..., None]) * C[None, None, :]) / np.maximum(a[..., None], 0.05)
    F = np.clip(F, 0, 1)
    edge = a < 0.95
    # mild despill only on semi-transparent edges (the foliage itself is allowed to be green)
    lim = np.maximum(F[..., 0], F[..., 2]) * 0.5 + (F[..., 0] + F[..., 2]) * 0.25 + 0.12
    F[..., 1] = np.where(edge, np.minimum(F[..., 1], lim), F[..., 1])
    F = np.where(a[..., None] > 0, F, 0)
    return edge_fix(F, a), a


if __name__ == "__main__":
    import os
    D = os.environ.get("FOREST_DIR", "input/forest")
    for name, mode, boxes in [
        ("trio_back", "diff", [(20, 20, 400, 300), (1300, 20, 1650, 400)]),
        ("trio_close", "diff", [(1400, 20, 1660, 300), (20, 20, 300, 250)]),
        ("fg_grass", "chroma", [(600, 20, 1250, 300), (1500, 20, 1660, 300)]),
    ]:
        I = cv2.imread(f"{D}/{name}.png").astype(np.float32) / 255.0
        C = screen_color(I, boxes)
        F, a = key_diff(I, C) if mode == "diff" else key_chroma(I, C)
        np.save(f"{D}/{name}_fg.npy", F); np.save(f"{D}/{name}_a.npy", a)
        chk = F * a[..., None] + (1 - a[..., None]) * np.float32([0.55, 0.35, 0.75])
        cv2.imwrite(f"{D}/{name}_key.jpg", cv2.resize((chk * 255).astype(np.uint8), None, fx=0.6, fy=0.6), [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(name, C.round(3), float(a.mean()))
