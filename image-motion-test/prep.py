"""Prepare the layers from the still photos (classical image processing only, no generative AI).
   1. fonts (OFL) -> fonts/
   2. a02 (close-up): GrabCut matte + clean plate -> paint out the leash chain
   3. a03 (full body): GrabCut matte -> remove a dark sliver at the ear tip
   4. both: edge colour decontamination + green despill (grass bounce light)
   Output: work/*.npy  (used by render.py)"""
import os, subprocess, sys, urllib.request
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
FONTS = {
    "fonts/NotoSansJP-VF.ttf": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf",
    "fonts/OFL_NotoSansJP.txt": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosansjp/OFL.txt",
    "fonts/YujiSyuku-Regular.ttf": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/yujisyuku/YujiSyuku-Regular.ttf",
    "fonts/OFL_YujiSyuku.txt": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/yujisyuku/OFL.txt",
}


def fetch_fonts():
    os.makedirs("fonts", exist_ok=True)
    for path, url in FONTS.items():
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            continue
        print("  download", path, flush=True)
        with urllib.request.urlopen(url, timeout=120) as r:
            open(path, "wb").write(r.read())


def fix_chain_a02():
    """the gold leash chain (top right) is not part of the dog: remove it from plate and fur edge"""
    fg = np.load("work/a02_fg.npy"); a = np.load("work/a02_alpha.npy"); plate = np.load("work/a02_plate.npy")
    img = cv2.imread("src/akita_02.jpg")
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    corr = np.zeros(a.shape, np.uint8)
    cv2.fillPoly(corr, [np.int32([[850, 0], [950, 0], [905, 205], [858, 205]])], 1)
    bright = (hsv[..., 2] > 55).astype(np.uint8)
    gold = ((hsv[..., 0] > 8) & (hsv[..., 0] < 38) & (hsv[..., 1] > 80) & (hsv[..., 2] > 70)).astype(np.uint8)
    chain = cv2.dilate(corr * np.maximum(bright, gold), np.ones((5, 5), np.uint8))
    chain_fg = cv2.dilate(corr * gold * (hsv[..., 1] > 110), np.ones((3, 3), np.uint8))
    p8 = (np.clip(plate, 0, 1) * 255).astype(np.uint8)
    p8 = cv2.inpaint(p8, cv2.dilate(chain, np.ones((9, 9), np.uint8)), 7, cv2.INPAINT_TELEA)
    np.save("work/a02_plate.npy", p8.astype(np.float32) / 255)
    a2 = a.copy()
    a2[chain_fg > 0] = 0
    soft = cv2.GaussianBlur(a2, (0, 0), 1.2)
    near = cv2.dilate(chain_fg, np.ones((9, 9), np.uint8)) > 0
    np.save("work/a02_alpha.npy", np.where(near, np.minimum(a2, soft), a2).astype(np.float32))


def fix_eartip_a03():
    fg = np.load("work/a03_fg.npy"); a = np.load("work/a03_alpha.npy")
    reg = np.zeros(a.shape, bool)
    reg[250:330, 722:765] = True
    a[reg & (fg.mean(2) < 0.33)] = 0
    a = np.where(reg, np.minimum(a, cv2.GaussianBlur(a, (0, 0), 0.8)), a)
    np.save("work/a03_alpha.npy", a.astype(np.float32))


def edgefix(name):
    """semi-transparent edge pixels take the colour of nearby solid fur (no background tint in the fringe)"""
    fg = np.load(f"work/{name}_fg.npy"); a = np.load(f"work/{name}_alpha.npy")
    w = (a > 0.97).astype(np.float32)
    F = np.zeros_like(fg); D = np.zeros(a.shape, np.float32)
    for sig in (3, 6, 12, 24):
        num = cv2.GaussianBlur(fg * w[..., None], (0, 0), sig); den = cv2.GaussianBlur(w, (0, 0), sig)
        take = (D < 1e-3) & (den > 1e-3)
        F[take] = num[take] / den[take][..., None]; D[take] = den[take]
    edge = a < 0.97
    lum_o = fg.mean(2, keepdims=True); lum_f = F.mean(2, keepdims=True)
    F2 = np.clip(F * (0.75 + 0.25 * lum_o / np.maximum(lum_f, 1e-3)), 0, 1)
    np.save(f"work/{name}_fg.npy", np.where(edge[..., None] & (D[..., None] > 1e-3), F2, fg).astype(np.float32))


def despill(name):
    """grass bounce light makes shaded white fur green: G <= max(R, B), then warm the neutralised shade"""
    fg = np.load(f"work/{name}_fg.npy")
    b, g, r = fg[..., 0], fg[..., 1], fg[..., 2]
    g2 = np.minimum(g, np.maximum(r, b))
    out = np.stack([b, g2, r], 2)
    shade = np.clip((g - g2) * 6, 0, 1)[..., None]
    out = out * (1 - 0.35 * shade) + 0.35 * shade * out * np.float32([0.96, 1.0, 1.05])
    np.save(f"work/{name}_fg.npy", np.clip(out, 0, 1).astype(np.float32))


def main():
    fetch_fonts()
    os.makedirs("work", exist_ok=True)
    for name in ("a02", "a03"):
        print("  matte", name, flush=True)
        subprocess.run([sys.executable, "matte.py", f"cutouts/{name}.json"], check=True)
    fix_chain_a02()
    fix_eartip_a03()
    for name in ("a03", "a02"):
        edgefix(name)
    for name in ("a03", "a02"):
        despill(name)
    print("prep ok")


if __name__ == "__main__":
    main()
