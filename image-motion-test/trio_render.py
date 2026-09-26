"""Your own green-screen still -> 8 s living shot (no video generation).
   python trio_render.py input/trio.png            -> out/private/trio_test.mp4 (+ stills)
   (input/ and out/private/ are git-ignored: your character never goes into the public repo)"""
import json, os, subprocess, sys, time
import multiprocessing as mp
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
from engine import W, H, FPS, to_u8

SRC = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "input/trio.png"
OUT = "out/private"
NF = 240
_st = {}


def init():
    from trio_shot import TrioShot
    _st["s"] = TrioShot(f"{OUT}/t_fg.npy", f"{OUT}/t_alpha.npy")


def render(n):
    if not _st:
        init()
    img = _st["s"].frame(n / FPS)
    if n < 6:
        img = img * (n / 6.0)
    if n >= NF - 10:
        img = img * ((NF - 1 - n) / 9.0)
    return to_u8(img)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    subprocess.run([sys.executable, "trio_matte.py", SRC, f"{OUT}/t"], check=True)
    init()
    for n in (15, 60, 87, 150, 178, 225):
        cv2.imwrite(f"{OUT}/f{n:03d}.jpg", render(n), [cv2.IMWRITE_JPEG_QUALITY, 92])
    enc = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf",
                            "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264",
                            "-preset", "slow", "-crf", "16", "-x264-params", "aq-mode=3", "-color_primaries", "bt709",
                            "-color_trc", "bt709", "-colorspace", "bt709", f"{OUT}/_v.mp4"], stdin=subprocess.PIPE)
    with mp.Pool(4, initializer=init) as pool:
        for fr in pool.imap(render, range(NF), chunksize=4):
            enc.stdin.write(fr.tobytes())
    enc.stdin.close(); enc.wait()
    subprocess.run([sys.executable, "audio.py", f"{OUT}/_a.wav", "--trio"], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"{OUT}/_a.wav", "-af",
                        "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    af = ("loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:measured_I={input_i}:measured_TP={input_tp}:"
          "measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}").format(**m)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", f"{OUT}/_v.mp4", "-i", f"{OUT}/_a.wav",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-t", str(NF / FPS), "-movflags", "+faststart", f"{OUT}/trio_test.mp4"], check=True)
    for f in ("_v.mp4", "_a.wav"):
        os.remove(f"{OUT}/{f}")
    print(f"done {time.time() - t0:.0f}s -> {OUT}/trio_test.mp4")


if __name__ == "__main__":
    main()
