#!/usr/bin/env python3
"""完成品をデスクトップ（または指定フォルダ）にコピーする。上書きはしない。

  python deliver.py WORK/warudakumi_final.mp4 WORK/transcript_warudakumi.txt WORK/transcript_warudakumi.srt
  python deliver.py WORK/xxx_final.mp4 --to "D:/納品"

同じ名前のファイルが既にあれば「名前 (2).mp4」のように別名で置く。
デスクトップにあるのはユーザー本人のファイルなので、決して上書きしない。
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def free_name(dest: Path) -> Path:
    if not dest.exists():
        return dest
    k = 2
    while (dest.with_name(f"{dest.stem} ({k}){dest.suffix}")).exists():
        k += 1
    return dest.with_name(f"{dest.stem} ({k}){dest.suffix}")


def main() -> None:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--to", default=None, help="納品先フォルダ（省略時はデスクトップ）")
    a = ap.parse_args()
    to = Path(a.to).expanduser() if a.to else common.desktop_dir()
    if not to or not Path(to).is_dir():
        sys.exit("納品先のフォルダが見つかりません。--to で指定してください（ユーザーに置き場所を確認する）。")
    for f in a.files:
        src = Path(f)
        if not src.is_file():
            sys.exit(f"ファイルがありません: {src}")
        dest = free_name(Path(to) / src.name)
        shutil.copy2(src, dest)
        note = "" if dest.name == src.name else "  ※同名があったので別名にした"
        print(f"納品: {dest}  ({dest.stat().st_size / 1e6:.1f}MB){note}")


if __name__ == "__main__":
    main()
