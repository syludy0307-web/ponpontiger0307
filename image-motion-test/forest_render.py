"""Evening forest walk v1 (17.5 s) -> out/private/forest_walk_v1.mp4   (private: your characters)"""
import json, os, subprocess, sys, time
import multiprocessing as mp
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
from engine import W, H, FPS, to_u8, smooth

OUT = "out/private"
NF = 525
SHOTS = [("s1", 0, 114), ("s2", 96, 278), ("s3", 262, 414), ("s4", 396, 525)]
_st = {}


def init():
    import forest_shots as fs
    _st["s1"] = fs.S1Establish()
    _st["s2"] = fs.SPathWalk(1.0, 1.6, (278 - 96) / FPS, cam_zoom=(1.0, 1.05))
    s3 = fs.S3Close(); s3.dur = (414 - 262) / FPS
    _st["s3"] = s3
    _st["s4"] = fs.SPathWalk(2.4, 4.0, (525 - 396) / FPS, cam_zoom=(1.05, 1.1), flare=(0.12, 0.55), seed=31)


def render(n):
    if not _st:
        init()
    acc = None
    wsum = 0.0
    act = [(k, a, b) for (k, a, b) in SHOTS if a <= n < b]
    for k, a, b in act:
        w = 1.0
        for k2, a2, b2 in SHOTS:  # overlap with a later shot -> fade out; with an earlier -> fade in
            if k2 != k and a2 <= n < b2:
                if a2 > a:
                    w = 1 - smooth(a2, b, n)
                else:
                    w = smooth(a, b2, n)
        img = _st[k].frame((n - a) / FPS)
        acc = img * w if acc is None else acc + img * w
        wsum += w
    img = acc / max(wsum, 1e-6)
    if n < 15:
        img = img * (n / 15.0)
    if n >= NF - 36:
        img = img * max(0.0, (NF - 1 - n) / 35.0)
    return to_u8(img)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    init()
    picks = [40, 150, 230, 300, 360, 460]
    ims = []
    for n in picks:
        im = render(n)
        cv2.imwrite(f"{OUT}/forest_f{n:03d}.jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 92])
        ims.append(cv2.resize(im, (640, 360), interpolation=cv2.INTER_AREA))
    cv2.imwrite(f"{OUT}/forest_contact.jpg", np.vstack([np.hstack(ims[:3]), np.hstack(ims[3:])]), [cv2.IMWRITE_JPEG_QUALITY, 90])
    if "--review" in sys.argv:
        return
    enc = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf",
                            "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264",
                            "-preset", "slow", "-crf", "16", "-x264-params", "aq-mode=3", "-color_primaries", "bt709",
                            "-color_trc", "bt709", "-colorspace", "bt709", f"{OUT}/_fv.mp4"], stdin=subprocess.PIPE)
    with mp.Pool(4, initializer=init) as pool:
        for i, fr in enumerate(pool.imap(render, range(NF), chunksize=3)):
            enc.stdin.write(fr.tobytes())
            if i % 100 == 0:
                print(f"  frame {i}/{NF} {time.time() - t0:.0f}s", flush=True)
    enc.stdin.close(); enc.wait()
    subprocess.run([sys.executable, "audio_forest.py", f"{OUT}/_fa.wav"], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"{OUT}/_fa.wav", "-af",
                        "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    af = ("loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:measured_I={input_i}:measured_TP={input_tp}:"
          "measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}").format(**m)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", f"{OUT}/_fv.mp4", "-i", f"{OUT}/_fa.wav",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-t", str(NF / FPS), "-movflags", "+faststart", f"{OUT}/forest_walk_v1.mp4"], check=True)
    for f in ("_fv.mp4", "_fa.wav"):
        os.remove(f"{OUT}/{f}")
    print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
