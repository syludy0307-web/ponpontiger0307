"""Still for the report: automatic in-between (optical flow, no generative AI) vs. the real poses."""
import glob, cv2, numpy as np
import mg
from shot3 import HEADS, ANCHOR
fs = sorted(glob.glob("src/muy/ike_*.jpg"))
def load(i):
    g = cv2.imread(fs[i], cv2.IMREAD_GRAYSCALE).astype(np.float32)
    g = (g - g.mean()) / g.std() * 48 + 120
    M = np.float32([[1, 0, ANCHOR - HEADS[i]], [0, 1, 0]])
    return np.clip(cv2.warpAffine(g, M, (960, 545), borderMode=cv2.BORDER_REPLICATE), 0, 255).astype(np.uint8)
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
def mid(a, b):
    fab = dis.calc(a, b, None); fba = dis.calc(b, a, None)
    h, w = a.shape; gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    wa = cv2.remap(a, gx - 0.5 * fab[..., 0], gy - 0.5 * fab[..., 1], cv2.INTER_LINEAR)
    wb = cv2.remap(b, gx - 0.5 * fba[..., 0], gy - 0.5 * fba[..., 1], cv2.INTER_LINEAR)
    return ((wa.astype(np.float32) + wb.astype(np.float32)) / 2).astype(np.uint8)
a, b = load(4), load(5)
m = mid(a, b)
row = np.hstack([a, m, b])
img = cv2.cvtColor(row, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255
canvas = np.zeros((545 + 90, 2880, 3), np.float32); canvas[:] = (0.31, 0.17, 0.11)
canvas[90:] = img
for i, txt in enumerate(["ポーズ画像 5", "自動の中割り（オプティカルフロー）→ 脚が二重になる", "ポーズ画像 6"]):
    s = mg.text_sprite(txt, mg.SANS, 40, 700, color=(1, 1, 1), pad=4)
    mg.blit(canvas, s, i * 960 + (960 - s.shape[1]) / 2, 20)
cv2.imwrite("out/review/interp_compare.jpg", (np.clip(canvas, 0, 1) * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
print("ok")
