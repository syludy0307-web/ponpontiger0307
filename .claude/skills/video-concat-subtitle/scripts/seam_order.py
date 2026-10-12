#!/usr/bin/env python3
"""番号の無いクリップの並び順を、つなぎ目のコマから決める。

Seedance の「Continue seamlessly from the last frame of the video」で作った続きの動画は、
前の動画の最後のコマから始まる。そこで、各クリップの「最後のコマ」と別のクリップの
「最初のコマ」を小さな白黒画像にして比べ、いちばん自然につながる順番を探す。

  python seam_order.py A.mov B.mov C.mov      （順番はばらばらでよい）

数字は 0〜255 の平均の差で、小さいほど同じ絵。続きの動画どうしならふつう 5 以下、
別の場面なら 30 以上になる。結果は frames.py でつなぎ目のコマを並べて目でも確かめる。
"""
from __future__ import annotations

import argparse
import itertools
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

W, H = 90, 160
SAME = 12.0  # これ以下なら「同じ場面で続いている」


def frame(path: str, last: bool) -> np.ndarray:
    pre = ["-sseof", "-0.1"] if last else []
    # 画素をそのまま受け取るので、文字列として扱う common.run ではなく subprocess を直接使う
    r = subprocess.run([common.ffmpeg(), "-v", "error", *pre, "-i", path, "-frames:v", "1",
                        "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                       capture_output=True)
    if r.returncode != 0 or len(r.stdout) < W * H:
        sys.exit(f"コマを取り出せませんでした: {path}")
    return np.frombuffer(r.stdout[:W * H], dtype=np.uint8).astype(np.float32)


def main():
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description="つなぎ目のコマを比べて、番号の無いクリップの順番を決める")
    ap.add_argument("clips", nargs="+", help="クリップ（順番はばらばらでよい）")
    a = ap.parse_args()
    clips = [str(Path(c)) for c in a.clips]
    if len(clips) < 2:
        sys.exit("2本以上のクリップを渡してください")
    if len(clips) > 7:
        sys.exit("一度に比べられるのは7本までです")

    names = [Path(c).name for c in clips]
    first = [frame(c, last=False) for c in clips]
    last = [frame(c, last=True) for c in clips]
    n = len(clips)
    d = np.full((n, n), np.inf)
    for i in range(n):
        for j in range(n):
            if i != j:
                d[i, j] = float(np.mean(np.abs(last[i] - first[j])))

    short = [f"[{k + 1}]" for k in range(n)]
    print("===== クリップ =====")
    for k, nm in enumerate(names):
        print(f"  {short[k]} {nm}")
    print("\n===== 行の最後のコマ → 列の最初のコマ の差（小さいほど続いている） =====")
    print("      " + "".join(f"{s:>8}" for s in short))
    for i in range(n):
        cells = "".join(f"{'-':>8}" if i == j else f"{d[i, j]:8.1f}" for j in range(n))
        print(f"  {short[i]:>4}{cells}")

    best = min(itertools.permutations(range(n)),
               key=lambda p: sum(d[p[k], p[k + 1]] for k in range(n - 1)))
    print("\n===== いちばん自然につながる順番 =====")
    ok = True
    for k, i in enumerate(best):
        print(f"  {k + 1}. {names[i]}")
        if k < n - 1:
            diff = d[i, best[k + 1]]
            good = diff <= SAME
            ok &= good
            print(f"       ↓ つなぎ目の差 {diff:.1f}  {'同じ場面で続いている' if good else '要確認（続いていない）'}")
    if ok:
        print("\nどのつなぎ目も続いています。この順番でスクリプトに渡し、frames.py でつなぎ目のコマも目で確かめてください。")
    else:
        print("\n続いていないつなぎ目があります。別々に撮った場面かもしれません。"
              "ファイル名の番号・内容で順番を決め、わからなければユーザーに聞いてください。")


if __name__ == "__main__":
    main()
