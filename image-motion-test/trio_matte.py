"""Chroma key for a green-screen still (no AI): colour-difference key + decontamination + despill."""
import cv2, numpy as np, sys
src, out = sys.argv[1], sys.argv[2]
I = cv2.imread(src).astype(np.float32) / 255.0
b, g, r = I[..., 0], I[..., 1], I[..., 2]
d = g - np.maximum(r, b)
# background reference from corners known to be pure screen
samples = np.concatenate([I[5:90, 1320:1440].reshape(-1, 3), I[100:300, 5:80].reshape(-1, 3)])
C = np.median(samples, axis=0)
d_bg = float(C[1] - max(C[0], C[2]))
d_fg = 0.06
alpha = np.clip((d_bg - d) / (d_bg - d_fg), 0, 1)
alpha = np.where(alpha < 0.03, 0, np.where(alpha > 0.97, 1, alpha)).astype(np.float32)
# screen texture far from any subject is not hair: clean it
near = cv2.dilate((alpha > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51))) > 0
alpha[(~near) & (alpha < 0.35)] = 0
# decontaminate: F = (I - (1-a) C) / a, then despill G <= max(R, B)
F = (I - (1 - alpha[..., None]) * C[None, None, :]) / np.maximum(alpha[..., None], 0.04)
F = np.clip(F, 0, 1)
F[..., 1] = np.minimum(F[..., 1], (F[..., 0] + F[..., 2]) * 0.5 + 0.03)  # average despill (kills yellow-green fringe)
F = np.where(alpha[..., None] > 0, F, 0)
# edge colour from the solid interior (removes the thin yellow-green fringe around the fur)
w = (alpha > 0.97).astype(np.float32)
Fi = np.zeros_like(F); D = np.zeros(alpha.shape, np.float32)
for sig in (2, 4, 8, 16):
    num = cv2.GaussianBlur(F * w[..., None], (0, 0), sig); den = cv2.GaussianBlur(w, (0, 0), sig)
    take = (D < 1e-3) & (den > 1e-3)
    Fi[take] = num[take] / den[take][..., None]; D[take] = den[take]
edge = (alpha < 0.97) & (alpha > 0)
lum_o = F.mean(2, keepdims=True); lum_f = Fi.mean(2, keepdims=True)
F2 = np.clip(Fi * (0.6 + 0.4 * lum_o / np.maximum(lum_f, 1e-3)), 0, 1)
F = np.where(edge[..., None] & (D[..., None] > 1e-3), F2, F).astype(np.float32)
# 1 px choke on the animals' side only (x > CHOKE_X), the woman's hair strands stay intact
CHOKE_X = int(sys.argv[3]) if len(sys.argv) > 3 else 830
er = cv2.GaussianBlur(cv2.erode(alpha, np.ones((3, 3), np.uint8)), (0, 0), 0.7)
reg = np.zeros(alpha.shape, np.float32); reg[:, CHOKE_X:] = 1
reg = cv2.GaussianBlur(reg, (0, 0), 10)
alpha = (alpha * (1 - reg) + np.minimum(alpha, er) * reg).astype(np.float32)
np.save(out + "_fg.npy", F.astype(np.float32)); np.save(out + "_alpha.npy", alpha)
chk = F * alpha[..., None] + (1 - alpha[..., None]) * np.float32([0.55, 0.35, 0.75])
cv2.imwrite(out + "_check.jpg", (chk * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
print("bg", C, "d_bg", round(d_bg, 3), "alpha mean", float(alpha.mean()))
