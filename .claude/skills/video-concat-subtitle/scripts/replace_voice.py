#!/usr/bin/env python3
"""セリフの声を、別に用意した音声（ElevenLabs などで作った mp3 / wav）に差し替えた音声を作る。

  python replace_voice.py --clips 1.mp4 2.mp4 --voice new.mp3 --at 27.27 --mute 27.66 30.14 --work WORK
  → WORK/voice_mix.wav（動画全体の音声）ができる。
    render.py に --audio WORK/voice_mix.wav を付けて書き出す（映像のエンコードは1回のまま）

- 元の音声の --mute の区間（元のセリフ）を消し、新しい声の話し始めが --at 秒に来るように重ねる
- 新しい声の前後の無音は自動で切る
- 声の大きさは、消した元のセリフに合わせてから --offset-db（既定 -1.0 dB）だけ動かす
  （「少しだけ下げて」と頼まれたときの既定。大きく／小さくと言われたらここを変える）
- 元の声と同じ場所で鳴っているように、ごく軽い部屋の響きと高音の丸めを付ける（--dry で付けない）
- 消す区間の前後は 0.08 秒かけて音量を下げる・戻す（ぶつっと切れないように）
"""
from __future__ import annotations

import argparse
import re
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

SR = 48000
FADE = 0.08                 # 元の音声を消す・戻すときのフェード（秒）
PRE, POST = 0.04, 0.10      # 新しい声の前後に残す余白（秒）
ROOM = ["highpass=f=90", "lowpass=f=11000", "aecho=0.9:0.9:19|31|47:0.12|0.08|0.05"]


def ffmpeg_wav(src, out, filters=(), inputs=None, graph=None) -> None:
    """48kHz・ステレオ・16bit の wav に書き出す。"""
    cmd = [common.ffmpeg(), "-hide_banner", "-v", "error", "-y"]
    if graph:
        cmd += [*inputs, "-filter_complex", graph, "-map", "[out]"]
    else:
        af = ",".join([*filters, "aformat=sample_fmts=s16:sample_rates=48000:channel_layouts=stereo"])
        cmd += ["-i", str(src), "-vn", "-af", af]
    r = common.run(cmd + [str(out)])
    if r.returncode != 0:
        sys.exit(f"音声の書き出しに失敗しました:\n{r.stderr}")


def read(path) -> np.ndarray:
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        return x.reshape(-1, w.getnchannels())


def write(path, x: np.ndarray) -> None:
    y = (np.clip(x, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y.tobytes())


def loudness(path, start=None, end=None):
    """ラウドネス（LUFS）。人の耳の感じ方に近い大きさ。"""
    af = ([f"atrim={start:.3f}:{end:.3f}"] if start is not None else []) + ["ebur128"]
    r = common.run([common.ffmpeg(), "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", ",".join(af),
                    "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None


def speech_bounds(x: np.ndarray, thr_db: float = -45.0):
    """声のある範囲（thr_db を超える 10ms 区間の最初と最後）。"""
    mono = x.mean(axis=1)
    step = int(SR * 0.01)
    n = len(mono) // step
    rms = np.sqrt((mono[:n * step].reshape(n, step) ** 2).mean(axis=1))
    idx = np.where(20 * np.log10(rms + 1e-9) > thr_db)[0]
    if not len(idx):
        sys.exit("新しい声の音声に、声が見つかりません（無音のファイル？）")
    return idx[0] * step / SR, (idx[-1] + 1) * step / SR


def original_audio(clips, out) -> None:
    """render.py と同じ考え方でクリップの音声をつなぐ（音声の無いクリップは無音、各クリップの尺に揃える）。"""
    inputs, parts = [], []
    for i, c in enumerate(clips):
        inputs += ["-i", c["path"]]
        d = c["duration"]
        if c["has_audio"]:
            parts.append(f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                         f"apad=whole_dur={d:.3f},atrim=0:{d:.3f}[a{i}]")
        else:
            parts.append(f"aevalsrc=0|0:d={d:.3f}:s=48000:c=stereo,aformat=sample_fmts=fltp[a{i}]")
    parts.append("".join(f"[a{i}]" for i in range(len(clips)))
                 + f"concat=n={len(clips)}:v=0:a=1,aformat=sample_fmts=s16:channel_layouts=stereo[out]")
    ffmpeg_wav(None, out, inputs=inputs, graph=";".join(parts))


def main() -> None:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clips", nargs="+", required=True, help="クリップ（番号順。render.py に渡すのと同じ）")
    ap.add_argument("--voice", required=True, help="新しい声の音声ファイル（mp3 / wav など）")
    ap.add_argument("--at", type=float, required=True, help="新しい声の話し始めを置く時刻（連結後の通し時刻・秒）")
    ap.add_argument("--mute", type=float, nargs=2, required=True, metavar=("FROM", "TO"),
                    help="元の音声を消す区間（元のセリフ。連結後の通し時刻・秒）")
    ap.add_argument("--offset-db", type=float, default=-1.0, help="元のセリフの大きさからの差（既定 -1.0 dB）")
    ap.add_argument("--dry", action="store_true", help="部屋の響き・高音の丸めを付けない")
    ap.add_argument("--work", required=True)
    a = ap.parse_args()

    work = Path(a.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    clips = [common.probe(c) for c in a.clips]
    total = sum(c["duration"] for c in clips)
    m0, m1 = a.mute
    if not (0 <= m0 < m1 <= total + 0.01):
        sys.exit(f"--mute は 0〜{total:.2f} 秒の範囲で「始め 終わり」の順に（今: {m0} {m1}）")

    # 1) 元の音声と、消すセリフの大きさ
    orig_wav = work / "voice_orig.wav"
    original_audio(clips, orig_wav)
    x = read(orig_wav)
    l_old = loudness(orig_wav, m0, min(m1, total))

    # 2) 新しい声: 前後の無音を切り、響きを付ける
    raw_wav = work / "voice_new_raw.wav"
    ffmpeg_wav(a.voice, raw_wav)
    s0, s1 = speech_bounds(read(raw_wav))
    raw_len = len(read(raw_wav)) / SR
    pre, post = min(PRE, s0), min(POST, raw_len - s1)
    trim = [f"atrim={s0 - pre:.3f}:{s1 + post:.3f}", "asetpts=PTS-STARTPTS"]
    new_wav = work / "voice_new.wav"
    ffmpeg_wav(raw_wav, new_wav, trim + ([] if a.dry else ROOM))
    v = read(new_wav)

    # 3) 大きさを元のセリフに合わせる
    l_new = loudness(new_wav)
    if l_old is None or l_new is None:
        sys.exit("音の大きさを測れませんでした（--mute の区間が短すぎる？ 0.5 秒以上にする）")
    gain_db = (l_old + a.offset_db) - l_new
    v = v * (10 ** (gain_db / 20))
    fi, fo = int(0.01 * SR), int(0.05 * SR)
    v[:fi] *= np.linspace(0, 1, fi)[:, None]
    v[-fo:] *= np.linspace(1, 0, fo)[:, None]

    # 4) 置く場所を確かめる（話し終わりが動画の終わりを越えないこと）
    speech = s1 - s0
    start = a.at - pre
    if start < 0:
        sys.exit(f"--at が早すぎます（{pre:.2f} 秒以上にする）")
    if a.at + speech > total - 0.02:
        sys.exit(f"新しい声（話している長さ {speech:.2f} 秒）が動画の終わり（{total:.2f} 秒）までに入りません。"
                 f"--at を {total - 0.02 - speech:.2f} 秒以下にしてください")
    i0 = int(round(start * SR))
    v = v[:len(x) - i0]                 # 動画の終わりを越える分（後ろの余白）は切る

    # 5) 元のセリフを消して、新しい声を重ねる
    t = np.arange(len(x)) / SR
    keep = np.clip(np.maximum((m0 - t) / FADE, (t - m1) / FADE), 0.0, 1.0)
    y = x * keep[:, None]
    y[i0:i0 + len(v)] += v
    peak = float(np.abs(y).max())
    if peak > 0.99:
        y *= 0.99 / peak
    out = work / "voice_mix.wav"
    write(out, y)

    print(f"元のセリフの大きさ   {l_old:6.1f} LUFS（{m0:.2f}〜{m1:.2f} 秒）")
    print(f"新しい声の大きさ     {l_new:6.1f} LUFS → {gain_db:+.1f} dB 動かして {l_old + a.offset_db:.1f} LUFS に"
          f"（元より {a.offset_db:+.1f} dB）")
    print(f"新しい声の位置       話し始め {a.at:.2f} 秒 → 話し終わり {a.at + speech:.2f} 秒"
          f"（話している長さ {speech:.2f} 秒）{'' if a.dry else ' / 部屋の響き・高音の丸めあり'}")
    print(f"元の音声を消した区間 {m0:.2f}〜{m1:.2f} 秒（前後 {FADE:.2f} 秒でフェード）"
          + ("" if peak <= 0.99 else f" / 音割れ防止で全体を {20 * np.log10(0.99 / peak):.1f} dB 下げた"))
    print(f"保存: {out}")
    print(f"→ lines.json のこのセリフは start {a.at:.2f} / end {a.at + speech:.2f} にして make_subs.py を作り直し、"
          f"render.py に --audio {out} を付けて書き出す")


if __name__ == "__main__":
    main()
