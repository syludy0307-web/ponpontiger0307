#!/usr/bin/env python3
"""連結・タイトル・字幕を1回のエンコードで書き出し、検品まで行う。

  python render.py --clips 001.mov 002.mov 003.mov --title "悪だくみ" \
                   --ass WORK/subs.ass --work WORK --out WORK/warudakumi_final.mp4

- クリップは渡した順に連結する（番号順に並べて渡す）。1本だけでもよい
- 解像度と fps は1本目に合わせる。大きさの違うクリップは縮小＋余白で揃える
- 音声の無いクリップは無音で埋める
- タイトルは冒頭 --title-seconds 秒（既定 5 秒）。--title を省けばタイトルなし
- --audio を渡すと、クリップの音声の代わりにその音声を使う（replace_voice.py で声を差し替えたとき）
- 書き出したら尺・フレーム数・デコードエラー・音量を検査し、
  タイトルと各字幕の場面を並べたレビュー画像（WORK/review.jpg）を作る。必ず目で見ること
"""
from __future__ import annotations

import argparse
import math
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import frames  # noqa: E402
from make_title import make_title  # noqa: E402


def build_graph(clips, W, H, fps_str, title=None, T=5.0, ass_name=None, audio=True):
    parts = []
    for i, c in enumerate(clips):
        chain = []
        if (c["width"], c["height"]) != (W, H):
            chain += [f"scale={W}:{H}:force_original_aspect_ratio=decrease", f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2"]
        chain += [f"fps={fps_str}", "format=yuv420p", "setsar=1"]
        parts.append(f"[{i}:v]{','.join(chain)}[v{i}]")
        if not audio:
            continue
        if c["has_audio"]:
            parts.append(f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a{i}]")
        else:
            parts.append(f"aevalsrc=0|0:d={c['duration']:.3f}:s=48000:c=stereo,aformat=sample_fmts=fltp[a{i}]")
    n = len(clips)
    if audio:
        parts.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    else:
        parts.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vc]")
    cur = "[vc]"
    if title:
        ys, yf, drift = -title["h"], title["yf"], title["drift"]
        hold_end = T - 0.5
        # 0〜0.55秒: 上からスライドイン（少し行き過ぎて戻る ease-out-back）/ 最後の0.5秒: 上へ抜けながら消える
        y = (f"if(lt(t,0.55),{ys}+{yf - ys}*(1+2.70158*pow(t/0.55-1,3)+1.70158*pow(t/0.55-1,2)),"
             f"if(lt(t,{hold_end:.2f}),{yf},{yf}-{drift}*pow((t-{hold_end:.2f})/0.5,2)))")
        parts.append(f"[{n}:v]format=rgba,fade=t=in:st=0:d=0.35:alpha=1,"
                     f"fade=t=out:st={T - 0.45:.2f}:d=0.45:alpha=1[ttl]")
        parts.append(f"{cur}[ttl]overlay=eval=frame:eof_action=pass:x=(W-w)/2:y='{y}':"
                     f"enable='between(t,0,{T:.2f})'[vt]")
        cur = "[vt]"
    if ass_name:
        parts.append(f"{cur}subtitles=filename={ass_name}[vs]")
        cur = "[vs]"
    return ";".join(parts), cur


def mean_volume(path):
    r = common.run([common.ffmpeg(), "-hide_banner", "-i", path, "-vn", "-af", "volumedetect", "-f", "null", "-"])
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", r.stderr)
    return float(m.group(1)) if m else None


def ass_cues(path):
    cues = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("Dialogue:"):
            f = line.split(",", 9)

            def sec(x):
                h, m, s = x.strip().split(":")
                return int(h) * 3600 + int(m) * 60 + float(s)

            cues.append((sec(f[1]), sec(f[2]), re.sub(r"\{[^}]*\}", "", f[9]).replace("\\N", " ")))
    return cues


def main() -> None:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clips", nargs="+", required=True, help="クリップ（番号順）")
    ap.add_argument("--title", default=None, help="タイトル文字列（「」は付けない）")
    ap.add_argument("--title-seconds", type=float, default=5.0)
    ap.add_argument("--ass", default=None, help="make_subs.py が作った subs.ass")
    ap.add_argument("--work", required=True, help="作業フォルダ（中間ファイルとレビュー画像の置き場）")
    ap.add_argument("--out", required=True, help="書き出す mp4")
    ap.add_argument("--audio", default=None, help="クリップの音声の代わりに使う音声（replace_voice.py の voice_mix.wav）")
    a = ap.parse_args()

    work = Path(a.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    out = Path(a.out).resolve()
    clips = [common.probe(c) for c in a.clips]
    W, H = clips[0]["width"], clips[0]["height"]
    fps_str = clips[0]["fps_str"]
    total = sum(c["duration"] for c in clips)
    T = min(a.title_seconds, max(1.0, total - 0.5))

    title = None
    if a.title:
        d = make_title(a.title, work / "title.png", W)
        # 文字の上端が画面の高さの 110/1280 に来る位置（これまでの完成品と同じ）
        title = {"h": d["h"], "yf": round(110 * H / 1280) - d["opaque_bbox"][1], "drift": round(40 * H / 1280)}
    ass_name = None
    if a.ass:
        ass_name = "_render_subs.ass"   # 作業フォルダ内の相対パスで渡す（Windows のドライブ名のエスケープ地獄を避ける）
        shutil.copyfile(a.ass, work / ass_name)

    graph, vout = build_graph(clips, W, H, fps_str, title, T, ass_name, audio=not a.audio)
    cmd = [common.ffmpeg(), "-hide_banner", "-v", "error", "-nostats", "-y"]
    for c in clips:
        cmd += ["-i", c["path"]]
    if title:
        cmd += ["-framerate", fps_str, "-loop", "1", "-t", f"{T:.2f}", "-i", str(work / "title.png")]
    aout, limit = "[ac]", []
    if a.audio:                         # 差し替えた音声を使う。長さは動画（素材の合計）に合わせる
        cmd += ["-i", str(Path(a.audio).resolve())]
        aout, limit = f"{len(clips) + (1 if title else 0)}:a", ["-t", f"{total:.3f}"]
    cmd += ["-filter_complex", graph, "-map", vout, "-map", aout, *limit,
            "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out)]
    (work / "render_cmd.txt").write_text(" ".join(f'"{x}"' if " " in x else x for x in cmd), encoding="utf-8")
    print(f"書き出し中 … {len(clips)}本 / {W}x{H} / {total:.2f}秒（数分かかる）", flush=True)
    r = common.run(cmd, cwd=str(work))
    if r.returncode != 0 or not out.exists():
        sys.exit(f"書き出しに失敗しました。\n{r.stderr}\n（コマンドは {work / 'render_cmd.txt'}）")

    # ---------------------------------------------------------------- 検品
    p = common.probe(out)
    ok = True

    def row(name, value, good):
        nonlocal ok
        ok &= good
        print(f"  {name:<8} {value:<40} {'OK' if good else '要確認'}")

    print("検品:")
    row("尺", f"{p['duration']:.2f} 秒（素材の合計 {total:.2f}）", abs(p["duration"] - total) < 0.25)
    same_fps = all(abs(c["fps"] - clips[0]["fps"]) < 0.01 for c in clips)
    if same_fps and p["frames"] and all(c["frames"] for c in clips):
        exp = sum(c["frames"] for c in clips)
        row("フレーム", f"{p['frames']}（素材の合計 {exp}）", abs(p["frames"] - exp) <= 2)
    dec = common.run([common.ffmpeg(), "-v", "error", "-i", out, "-f", "null", "-"])
    row("デコード", "エラーなし" if not dec.stderr.strip() else dec.stderr.strip()[:60], not dec.stderr.strip())
    row("解像度", f"{p['width']}x{p['height']}", (p["width"], p["height"]) == (W, H))
    mv_out = mean_volume(out)
    srcs = [(mean_volume(c["path"]), c["duration"]) for c in clips if c["has_audio"]]
    srcs = [(m, d) for m, d in srcs if m is not None]
    if mv_out is not None and srcs:
        # 無音のクリップも尺のぶんだけ平均に入れる（連結後の平均音量と比べるため）
        power = sum(10 ** (m / 10) * d for m, d in srcs) / total
        mv_src = 10 * math.log10(power) if power > 0 else -99
        row("音量", f"{mv_out:.1f} dB（素材 {mv_src:.1f} dB）", abs(mv_out - mv_src) < 1.5)

    cues = ass_cues(work / ass_name) if ass_name else []
    times = ([min(2.0, T * 0.4)] if title else []) + [round((s0 + e0) / 2, 2) for s0, e0, _ in cues]
    labels = ([f"タイトル {a.title}"] if title else []) + [f"{i}. {t}" for i, (_s, _e, t) in enumerate(cues, 1)]
    if times:
        frames.sheet_from_video(str(out), times, labels, work / "review.jpg")
        print(f"レビュー画像: {work / 'review.jpg'}  ← Read で開いて、タイトルと字幕の色・位置・改行を目で確認する")
    print(f"書き出し: {out}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
