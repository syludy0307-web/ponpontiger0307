"""Render the image-only motion test reel (16 s, 1920x1080, 30 fps) -> out/image_motion_test.mp4
   python render.py            full render + encode
   python render.py --review   stills + contact sheet only"""
import json, os, subprocess, sys, time
import multiprocessing as mp
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
from engine import W, H, FPS, to_u8
import mg

NF = 480
CUTS = [(0, 150, "s1"), (150, 360, "s2"), (360, 480, "s3")]
_state = {}


def init():
    from shot1 import Shot1
    from shot2 import Shot2
    from shot3 import Shot3
    _state["s1"] = Shot1("work")
    _state["s2"] = Shot2("work")
    _state["s3"] = Shot3("src/muy")
    _state["tag"] = mg.Tag("動画生成AIなし｜素材は静止画だけ")
    _state["cred12"] = mg.Tag("写真：Wikimedia Commons（CC0）", 20, 500)
    _state["cred3"] = mg.Tag("写真：E. Muybridge『Animal Locomotion』1887（パブリックドメイン）", 20, 500)
    _state["L1"] = mg.Label("① 写真1枚だけ", "呼吸・うとうと・耳・鼻・毛と草の風・光・カメラ（動きはすべてコード）", 64, 40, top=True)
    _state["L2"] = mg.Label("② 切り抜き1枚 ＋ モーショングラフィックス", "頭・口・しっぽ・耳を曲の拍に合わせて動かす（ノリ）", 64, 40, top=True)
    _state["L3"] = mg.Label("③ ポーズ画像8枚をつなぐ", "走る・跳ぶなど大きな動きは、ポーズの数だけ画像が必要（コマ送り）", 64, 1040)


def cut_of(n):
    for a, b, k in CUTS:
        if a <= n < b:
            return a, b, k
    return CUTS[-1]


def render(n):
    if not _state:
        init()
    a, b, k = cut_of(n)
    t = (n - a) / FPS
    dur = (b - a) / FPS
    img = _state[k].frame(t)
    img = np.ascontiguousarray(img, np.float32)
    _state["tag"].draw(img, 1.0)
    cred = _state["cred3"] if k == "s3" else _state["cred12"]
    cred.draw(img, 0.9, 36 + _state["tag"].h + 10)
    L = {"s1": "L1", "s2": "L2", "s3": "L3"}[k]
    _state[L].draw(img, t, 0.35 if k != "s3" else 0.2, dur - 0.25)
    # fade in / out of the whole reel
    if n < 8:
        img *= n / 8.0
    if n >= NF - 12:
        img *= (NF - 1 - n) / 11.0
    return to_u8(img)


def review():
    init()
    os.makedirs("out/review", exist_ok=True)
    picks = [20, 75, 130, 170, 230, 300, 372, 400, 450]
    ims = []
    for n in picks:
        im = render(n)
        cv2.imwrite(f"out/review/f{n:03d}.jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 92])
        ims.append(cv2.resize(im, (640, 360), interpolation=cv2.INTER_AREA))
    rows = [np.hstack(ims[i:i + 3]) for i in range(0, 9, 3)]
    cv2.imwrite("out/review/contact_sheet.jpg", np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print("review ok")


def encode_audio():
    subprocess.run([sys.executable, "audio.py", "out/_audio.wav"], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", "out/_audio.wav", "-af",
                        "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1]
    m = json.loads(js)
    af = ("loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:measured_I={input_i}:measured_TP={input_tp}:"
          "measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}").format(**m)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", "out/_audio.wav", "-af", af,
                    "-ar", "48000", "-c:a", "pcm_f32le", "out/_audio_norm.wav"], check=True)


def main():
    if "--review" in sys.argv:
        review()
        return
    os.makedirs("out", exist_ok=True)
    t0 = time.time()
    enc = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf",
                            "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-x264-params", "aq-mode=3",
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                            "out/_video.mp4"], stdin=subprocess.PIPE)
    with mp.Pool(4, initializer=init) as pool:
        for i, fr in enumerate(pool.imap(render, range(NF), chunksize=4)):
            enc.stdin.write(fr.tobytes())
            if i % 60 == 0:
                print(f"  frame {i}/{NF}  {time.time() - t0:.0f}s", flush=True)
    enc.stdin.close()
    enc.wait()
    t1 = time.time()
    encode_audio()
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", "out/_video.mp4", "-i",
                    "out/_audio_norm.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a",
                    "192k", "-ar", "48000", "-t", "16", "-movflags", "+faststart", "out/image_motion_test.mp4"],
                   check=True)
    for f in ("out/_video.mp4", "out/_audio.wav", "out/_audio_norm.wav"):
        os.remove(f)
    print(f"done: frames {t1 - t0:.0f}s, total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
