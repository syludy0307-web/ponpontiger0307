# -*- coding: utf-8 -*-
"""ffmpeg orchestration: aux clips -> scene clips -> concat -> final mux.

Usage:
    python3 render.py aux            # fog + stinger clips
    python3 render.py scenes [id..]  # render all (or named) scene clips
    python3 render.py concat         # build master.mp4
    python3 render.py final          # burn subs + mux audio -> output/
    python3 render.py all
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import AUDIO_PATH, BUILD, CLIPS, FPS, OUT, STILLS, ensure_dirs
from scenes import SCENES

FOG = os.path.join(BUILD, "fog.mp4")
STINGER = os.path.join(BUILD, "stinger.mp4")
MASTER = os.path.join(BUILD, "master.mp4")
FINAL = os.path.join(OUT, "haibyouin_top5_16x9.mp4")


def run(cmd, quiet=True):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        sys.stderr.write(" ".join(cmd)[:2000] + "\n")
        sys.stderr.write(r.stderr.decode()[-3000:] + "\n")
        raise SystemExit(1)
    return r


# ---------------------------------------------------------------- aux clips
def gen_fog(dur=24, w=480, h=270):
    import numpy as np
    frames = dur * FPS
    big = None
    rng = np.random.default_rng(7)
    # two drifting fractal layers over a big tile
    def noise_tile(tw, th, scale, seed):
        r = np.random.default_rng(seed)
        out = np.zeros((th, tw), np.float32)
        amp, tot = 1.0, 0.0
        from PIL import Image
        for o in range(4):
            gw = max(2, int(scale * (2 ** o)))
            gh = max(2, int(gw * th / tw))
            g = (r.random((gh, gw)) * 255).astype(np.uint8)
            up = Image.fromarray(g).resize((tw, th), Image.BILINEAR)
            out += np.asarray(up, np.float32) / 255.0 * amp
            tot += amp
            amp *= 0.55
        return out / tot
    tw, th = w * 3, h * 2
    n1 = noise_tile(tw, th, 6, 11)
    n2 = noise_tile(tw, th, 11, 23)
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
         "-r", str(FPS), "-i", "-", "-vf", f"scale=1920:1080:flags=bicubic,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", FOG],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(frames):
        t = i / frames
        x1 = int((tw - w) * t)
        x2 = int((tw - w) * (1 - t))
        y1 = int((th - h) * 0.3 * (1 + np.sin(t * 6.283)) / 2)
        y2 = int((th - h) * 0.6)
        a = n1[y1:y1 + h, x1:x1 + w]
        b = n2[y2:y2 + h, x2:x2 + w]
        m = np.clip((a * 0.65 + b * 0.55) - 0.28, 0, 1) * 1.5
        frame = (np.clip(m, 0, 1) * 210).astype(np.uint8)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    print("fog:", FOG)


def gen_stinger(dur=0.30, w=480, h=270):
    import numpy as np
    frames = max(6, int(dur * FPS))
    rng = np.random.default_rng(3)
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
         "-r", str(FPS), "-i", "-", "-vf", "scale=1920:1080:flags=neighbor,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", STINGER],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(frames):
        f = (rng.random((h, w)) * 255).astype(np.uint8)
        # rolling tear bands
        for _ in range(3):
            y = int(rng.random() * (h - 8))
            f[y:y + rng.integers(2, 7)] = rng.integers(0, 60)
        proc.stdin.write(f.tobytes())
    proc.stdin.close()
    proc.wait()
    print("stinger:", STINGER)


# ---------------------------------------------------------------- scene render
def frame_bounds(sc):
    f0 = round(sc["t0"] * FPS)
    f1 = round(sc["t1"] * FPS)
    return f0, f1 - f0


def scene_filter(sc, nframes):
    m = sc["motion"]
    fx = sc.get("fx", {})
    dur = nframes / FPS
    N = max(nframes - 1, 1)
    z0, z1 = m["z0"], m["z1"]
    wob = m.get("wob", 0.6) * 3.0  # px at art scale
    prog = f"(min(on,{N})/{N})"
    zexpr = f"{z0}+({z1}-{z0})*{prog}"
    cxe = f"({m['cx0']}+({m['cx1']}-{m['cx0']})*{prog})"
    cye = f"({m['cy0']}+({m['cy1']}-{m['cy0']})*{prog})"
    if m["kind"] == "hand":
        wx = (f"{wob}*sin(on/7.3)+{wob * 0.7}*sin(on/3.1)+{wob * 0.4}*sin(on/1.7)")
        wy = (f"{wob}*cos(on/6.1)+{wob * 0.7}*sin(on/2.6)+{wob * 0.4}*cos(on/1.3)")
    else:
        wx = f"{wob}*sin(on/23)+{wob * 0.6}*sin(on/9.7)"
        wy = f"{wob}*cos(on/19)+{wob * 0.6}*sin(on/7.9)"
    jolt = fx.get("jolt")
    if jolt:
        jt = jolt[0]
        wy += f"+60*exp(-pow((on/{FPS}-{jt})*6,2))*sin(on*2.7)"
        wx += f"+40*exp(-pow((on/{FPS}-{jt})*6,2))*cos(on*3.1)"
    xexpr = f"{cxe}*iw-(iw/zoom)/2+({wx})"
    yexpr = f"{cye}*ih-(ih/zoom)/2+({wy})"
    chains = []
    chains.append(
        f"[0:v]zoompan=z='{zexpr}':x='{xexpr}':y='{yexpr}':d=1:s=1920x1080:fps={FPS}"
        f",format=gbrp[base]")
    cur = "base"
    idx = 1
    # fog blend (in planar RGB: chroma-safe screen)
    fog_op = fx.get("fog", 0)
    if fog_op > 0:
        chains.append(f"[{idx}:v]format=gbrp,setsar=1[fg]")
        chains.append(f"[{cur}][fg]blend=all_mode=screen:all_opacity={fog_op:.2f}[b{idx}]")
        cur = f"b{idx}"
        idx += 1
    # ghost overlays
    for ov in sc.get("overlays", []):
        t_in, d_in = ov["t_in"], ov["d_in"]
        t_out, d_out = ov["t_out"], ov["d_out"]
        sc_f = ov.get("scale", 1.0)
        fades = f"fade=t=in:st={t_in}:d={d_in}:alpha=1"
        if t_out < dur:
            fades += f",fade=t=out:st={t_out}:d={d_out}:alpha=1"
        oa = ov.get("alpha", 1.0)
        if oa < 1.0:
            fades += f",colorchannelmixer=aa={oa:.2f}"
        chains.append(
            f"[{idx}:v]format=rgba,scale=iw*{sc_f:.3f}:-1,{fades}[ov{idx}]")
        ox = f"{ov['cx']}*1920-w/2+({ov.get('dx', 0)})*(t/{dur:.3f})"
        oy = f"{ov['cy']}*1080-h/2+({ov.get('dy', 0)})*(t/{dur:.3f})"
        chains.append(
            f"[{cur}][ov{idx}]overlay=x='{ox}':y='{oy}':enable='lt(t,{min(t_out + d_out + 0.3, dur):.2f})'[b{idx}]")
        cur = f"b{idx}"
        idx += 1
    # to yuv for the color-safe post ops
    chains.append(f"[{cur}]format=yuv420p[yv]")
    cur = "yv"
    # stinger cut-in
    if fx.get("stinger"):
        chains.append(f"[{idx}:v]format=yuv420p,setsar=1[st]")
        chains.append(
            f"[{cur}][st]overlay=enable='lt(t,0.22)':eval=frame[b{idx}]")
        cur = f"b{idx}"
        idx += 1
    post = []
    if fx.get("mono"):
        post.append("hue=s=0.22")
    fl = fx.get("flick", 0)
    if fl > 0:
        amp = 0.030 * fl
        post.append(
            f"eq=brightness='{amp:.4f}*(sin(2*PI*t*11.3)+0.6*sin(2*PI*t*17.7)"
            f"+0.5*sin(2*PI*t*7.1))':eval=frame")
    if fx.get("jolt"):
        jt = fx["jolt"][0]
        post.append(f"eq=brightness='0.5*exp(-pow((t-{jt})*9,2))':eval=frame")
    post.append("noise=alls=7:allf=t+u")
    post.append("vignette=PI/4.6")
    fin = fx.get("fade_in", 0)
    if fin:
        post.append(f"fade=t=in:st=0:d={fin}")
    fout = fx.get("fade_out", 0)
    if fout:
        post.append(f"fade=t=out:st={max(0, dur - fout):.3f}:d={fout}")
    chains.append(f"[{cur}]" + ",".join(post) + "[out]")
    return ";".join(chains)


def render_scene(sc, force=False):
    f0, nframes = frame_bounds(sc)
    outp = os.path.join(CLIPS, f"{sc['id']}.mp4")
    if os.path.exists(outp) and not force:
        return outp
    still = os.path.join(STILLS, sc["art"] + ".png")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", still]
    fx = sc.get("fx", {})
    if fx.get("fog", 0) > 0:
        cmd += ["-stream_loop", "-1", "-i", FOG]
    for ov in sc.get("overlays", []):
        cmd += ["-loop", "1", "-framerate", str(FPS), "-i",
                os.path.join(STILLS, ov["img"] + ".png")]
    if fx.get("stinger"):
        cmd += ["-stream_loop", "-1", "-i", STINGER]
    cmd += ["-filter_complex", scene_filter(sc, nframes), "-map", "[out]",
            "-frames:v", str(nframes), "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
            "-pix_fmt", "yuv420p", outp]
    run(cmd)
    return outp


def render_all(only=None, force=False):
    for i, sc in enumerate(SCENES):
        if only and sc["id"] not in only:
            continue
        p = render_scene(sc, force=force or bool(only))
        print(f"[{i + 1}/{len(SCENES)}] {sc['id']} -> {os.path.basename(p)}", flush=True)


# ---------------------------------------------------------------- assembly
def concat():
    lst = os.path.join(BUILD, "concat.txt")
    with open(lst, "w") as f:
        for sc in SCENES:
            f.write(f"file '{os.path.join(CLIPS, sc['id'] + '.mp4')}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", MASTER])
    print("master:", MASTER)


def final():
    ass = os.path.join(BUILD, "main.ass").replace("\\", "/")
    run(["ffmpeg", "-y", "-i", MASTER, "-i", AUDIO_PATH,
         "-vf", f"eq=saturation=1.08:contrast=1.015,ass={ass}",
         "-c:v", "libx264", "-preset", "faster", "-crf", "21",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-shortest", FINAL])
    print("final:", FINAL)


def dist():
    """Distribution encodes from the pristine final: 1080p / 720p / preview."""
    hq = os.path.join(BUILD, "final_hq.mp4")
    if not os.path.exists(hq):
        os.rename(FINAL, hq)
    run(["ffmpeg", "-y", "-i", hq, "-vf", "hqdn3d=1.6:1.2:3.5:3.0",
         "-c:v", "libx264", "-preset", "faster", "-crf", "25", "-pix_fmt", "yuv420p",
         "-c:a", "copy", "-movflags", "+faststart", FINAL])
    p720 = os.path.join(OUT, "haibyouin_top5_720p.mp4")
    passlog = os.path.join(BUILD, "x264pass")
    common = ["-vf", "scale=1280:720,hqdn3d=2:1.5:4:3.5", "-c:v", "libx264",
              "-preset", "slow", "-b:v", "850k", "-pix_fmt", "yuv420p",
              "-passlogfile", passlog]
    run(["ffmpeg", "-y", "-i", hq] + common + ["-pass", "1", "-an", "-f", "null", "-"])
    run(["ffmpeg", "-y", "-i", hq] + common + ["-pass", "2", "-c:a", "copy",
         "-movflags", "+faststart", p720])
    print("dist:", FINAL, p720)


def _dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], stdout=subprocess.PIPE)
    return float(r.stdout.decode().strip())


def _seg_ts(src, out_ts, w, h, crf, head_fade=0.0, tail_fade=0.0, abr="192k"):
    """Normalize an OP/ED clip to the main video's parameters as MPEG-TS."""
    d = _dur(src)
    vf = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
          f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p")
    af = "anull"
    if head_fade:
        vf += f",fade=t=in:st=0:d={head_fade}"
        af += f",afade=t=in:st=0:d={head_fade}"
    if tail_fade:
        st = max(0, d - tail_fade)
        vf += f",fade=t=out:st={st:.3f}:d={tail_fade}"
        af += f",afade=t=out:st={st:.3f}:d={tail_fade}"
    run(["ffmpeg", "-y", "-i", src, "-vf", vf, "-af", af,
         "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
         "-c:a", "aac", "-b:a", abr, "-ar", "44100", "-ac", "2",
         "-f", "mpegts", out_ts])


def _copy_ts(src, out_ts):
    run(["ffmpeg", "-y", "-i", src, "-c", "copy", "-bsf:v", "h264_mp4toannexb",
         "-f", "mpegts", out_ts])


def attach():
    """Prepend source/op.mp4 and append source/ed.mp4 to every deliverable."""
    from common import SRC
    op = os.path.join(SRC, "op.mp4")
    edv = os.path.join(SRC, "ed.mp4")
    targets = [
        (FINAL, 1920, 1080, 20, "192k"),
        (os.path.join(OUT, "haibyouin_top5_720p.mp4"), 1280, 720, 22, "192k"),
        (os.path.join(BUILD, "haibyouin_top5_preview_540p.mp4"), 960, 540, 30, "64k"),
    ]
    for main, w, h, crf, abr in targets:
        if not os.path.exists(main):
            print("skip (missing):", main)
            continue
        base = os.path.splitext(os.path.basename(main))[0]
        t_op = os.path.join(BUILD, f"op_{h}.ts")
        t_ed = os.path.join(BUILD, f"ed_{h}.ts")
        t_mn = os.path.join(BUILD, f"mn_{base}.ts")
        _seg_ts(op, t_op, w, h, crf, tail_fade=0.35, abr=abr)
        _seg_ts(edv, t_ed, w, h, crf, head_fade=0.35, tail_fade=0.6, abr=abr)
        _copy_ts(main, t_mn)
        tmp = main + ".tmp.mp4"
        run(["ffmpeg", "-y", "-i", f"concat:{t_op}|{t_mn}|{t_ed}",
             "-c", "copy", "-bsf:a", "aac_adtstoasc",
             "-movflags", "+faststart", tmp])
        os.replace(tmp, main)
        print(f"attached OP/ED -> {main} ({_dur(main):.2f}s)")


if __name__ == "__main__":
    ensure_dirs()
    args = sys.argv[1:]
    stage = args[0] if args else "all"
    if stage in ("aux", "all"):
        gen_fog()
        gen_stinger()
    if stage == "scenes":
        render_all(only=args[1:] or None)
    elif stage in ("all",):
        render_all()
    if stage in ("concat", "all"):
        concat()
    if stage in ("final", "all"):
        final()
    if stage == "dist":
        dist()
    if stage == "attach":
        attach()
