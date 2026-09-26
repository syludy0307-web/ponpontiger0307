"""Cutout + soft matte + clean plate for a still photo (classical CV only, no generative AI).
   GrabCut (with hand-placed hints) -> trimap -> local colour-line alpha -> foreground colour
   decontamination -> background clean plate by inpainting (Telea) + pyramid fill."""
import cv2, numpy as np, sys, json

def box(a, r):
    return cv2.boxFilter(a, -1, (2*r+1, 2*r+1), normalize=False, borderType=cv2.BORDER_REFLECT)

def local_mean(img, w, r):
    num = box(img * w[..., None], r); den = box(w, r)[..., None]
    return num / np.maximum(den, 1e-6), den[..., 0]

def cutout(img_bgr, rect, fg_polys=(), bg_polys=(), pfg_polys=(), band=6, iters=8):
    h, w = img_bgr.shape[:2]
    mask = np.full((h, w), cv2.GC_BGD, np.uint8)
    x0, y0, x1, y1 = rect
    mask[y0:y1, x0:x1] = cv2.GC_PR_FGD
    for p in pfg_polys: cv2.fillPoly(mask, [np.int32(p)], cv2.GC_PR_FGD)
    for p in bg_polys: cv2.fillPoly(mask, [np.int32(p)], cv2.GC_BGD)
    for p in fg_polys: cv2.fillPoly(mask, [np.int32(p)], cv2.GC_FGD)
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.setRNGSeed(7)
    cv2.grabCut(img_bgr, mask, None, bgd, fgd, iters, cv2.GC_INIT_WITH_MASK)
    hard = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
    # keep the biggest component (+ fill holes)
    n, lab, st, _ = cv2.connectedComponentsWithStats(hard, 8)
    if n > 1:
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); hard = (lab == k).astype(np.uint8)
    inv = 1 - hard
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    for i in range(1, n):
        x, y, ww, hh, a = st[i]
        if x > 0 and y > 0 and x + ww < w and y + hh < h and a < 4000: hard[lab == i] = 1
    return hard

def soft_alpha(img_bgr, hard, band=7, r=9):
    I = img_bgr.astype(np.float32) / 255.0
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*band+1, 2*band+1))
    fg_sure = cv2.erode(hard, k).astype(np.float32)
    bg_sure = (1 - cv2.dilate(hard, k)).astype(np.float32)
    unknown = (1 - fg_sure - bg_sure) > 0.5
    F, fden = local_mean(I, fg_sure, r); B, bden = local_mean(I, bg_sure, r)
    # widen the search where the local window saw no sure pixels
    for rr in (2*r, 4*r, 8*r):
        F2, fd2 = local_mean(I, fg_sure, rr); B2, bd2 = local_mean(I, bg_sure, rr)
        F = np.where((fden < 1)[..., None], F2, F); B = np.where((bden < 1)[..., None], B2, B)
        fden = np.maximum(fden, fd2); bden = np.maximum(bden, bd2)
    d = F - B
    a = np.sum((I - B) * d, axis=2) / np.maximum(np.sum(d * d, axis=2), 1e-4)
    a = np.clip(a, 0, 1)
    alpha = np.where(unknown, a, fg_sure).astype(np.float32)
    # gentle guided smoothing to remove speckle but keep fur strands
    alpha = cv2.bilateralFilter(alpha, 5, 0.15, 3)
    alpha = np.clip(alpha, 0, 1)
    # colour decontamination: F_est = (I - (1-a) B) / a
    Fest = (I - (1 - alpha[..., None]) * B) / np.maximum(alpha[..., None], 0.05)
    Fest = np.clip(Fest, 0, 1)
    fg = np.where((alpha[..., None] > 0.98), I, np.where(unknown[..., None], Fest, I))
    # green-spill suppression in the edge band (grass behind fur): G <= max(R, B) + small
    edge = cv2.dilate(unknown.astype(np.uint8), k).astype(bool)
    b_, g_, r_ = fg[..., 0], fg[..., 1], fg[..., 2]
    lim = np.maximum(r_, b_) + 0.02
    g_new = np.where(edge, np.minimum(g_, lim), g_)
    fg = np.stack([b_, g_new, r_], axis=2)
    return alpha, fg, B

def clean_plate(img_bgr, hard, grow=18):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*grow+1, 2*grow+1))
    m = cv2.dilate(hard, k)
    # pyramid (push-pull) fill: smooth, no smearing streaks
    I = img_bgr.astype(np.float32) / 255.0
    wts = (1 - m).astype(np.float32)
    levels = []
    cur, cw = I * wts[..., None], wts.copy()
    while min(cur.shape[:2]) > 8:
        levels.append((cur, cw))
        cur = cv2.pyrDown(cur); cw = cv2.pyrDown(cw)
    fill = cur / np.maximum(cw[..., None], 1e-6)
    for cur, cw in reversed(levels):
        up = cv2.resize(fill, (cur.shape[1], cur.shape[0]), interpolation=cv2.INTER_LINEAR)
        known = cur / np.maximum(cw[..., None], 1e-6)
        wn = np.clip(cw * 4, 0, 1)[..., None]
        fill = known * wn + up * (1 - wn)
    out = I * (1 - m[..., None]) + fill * m[..., None]
    # add back some texture from the surroundings so the fill isn't flat
    return np.clip(out, 0, 1), m

if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    img = cv2.imread(cfg["src"])
    hard = cutout(img, cfg["rect"], cfg.get("fg", []), cfg.get("bg", []), cfg.get("pfg", []))
    for p in cfg.get("hardfg", []):
        cv2.fillPoly(hard, [np.int32(p)], 1)
    alpha, fg, B = soft_alpha(img, hard, cfg.get("band", 7), cfg.get("r", 9))
    # hard zones: dark features against dark background (e.g. a black nose on grass) -> feathered hard mask
    if cfg.get("hardzone"):
        hz = np.zeros(hard.shape, np.uint8)
        for p in cfg["hardzone"]: cv2.fillPoly(hz, [np.int32(p)], 1)
        hz = cv2.GaussianBlur(hz.astype(np.float32), (0, 0), 6)
        feather = cv2.GaussianBlur(hard.astype(np.float32), (0, 0), 1.3)
        alpha = alpha * (1 - hz) + feather * hz
        I = img.astype(np.float32) / 255.0
        fg = fg * (1 - hz[..., None]) + I * hz[..., None]
    plate, m = clean_plate(img, hard, cfg.get("grow", 18))
    if cfg.get("texfill"):
        # borrow high-frequency grass detail from a known strip by tiling (keeps the fill from looking like a blur blob)
        x0, x1 = cfg["texfill"]["src_x"]
        I = img.astype(np.float32) / 255.0
        det = I - cv2.GaussianBlur(I, (0, 0), 5)
        h, w = hard.shape
        xs = np.arange(w); period = x1 - x0
        srcx = x0 + (np.abs(((xs - x0) % (2 * period)) - period)).astype(int)  # mirrored tiling
        srcx = np.clip(srcx, 0, w - 1)
        tiled = det[:, srcx]
        g = plate[..., 1] - np.maximum(plate[..., 0], plate[..., 2])
        grassy = np.clip(g * 12, 0, 1)[..., None]
        mm = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3)[..., None]
        plate = np.clip(plate + tiled * grassy * mm * 0.9, 0, 1)
    out = cfg["out"]
    np.save(out + "_alpha.npy", alpha); np.save(out + "_fg.npy", fg.astype(np.float32)); np.save(out + "_plate.npy", plate.astype(np.float32))
    cv2.imwrite(out + "_alpha.png", (alpha * 255).astype(np.uint8))
    # preview: cutout over magenta and over dark grey, plus plate
    mag = np.zeros_like(fg); mag[:] = (0.6, 0.1, 0.6)
    prev = fg * alpha[..., None] + mag * (1 - alpha[..., None])
    cv2.imwrite(out + "_cut_preview.jpg", (prev * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
    cv2.imwrite(out + "_plate.jpg", (plate * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print("done", out, alpha.shape, float(alpha.mean()))
