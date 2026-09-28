#!/usr/bin/env python3
"""作業前の環境チェック。足りないものがあれば、その OS 用の入れ方を表示する。

  python setup_check.py

全部そろっていれば終了コード 0、足りなければ 1。
必ずこのスクリプトを動かしたのと同じ python で、以降のスクリプトも動かすこと。
"""
from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

FIX = {
    "Darwin": {
        "ffmpeg": "brew install ffmpeg\n"
                  "   （Homebrew が無ければ https://brew.sh のトップにある1行コマンドで先に入れる）",
        "libass": "字幕の焼き込みに必要な libass が入っていない ffmpeg です。libass 入りに入れ替えてください:\n"
                  "   brew install ffmpeg-full\n"
                  "   それで入らなければ: brew tap homebrew-ffmpeg/ffmpeg && brew install homebrew-ffmpeg/ffmpeg/ffmpeg\n"
                  "   入れ替え後もこのチェックが古い ffmpeg を拾うなら、環境変数 FFMPEG_BIN / FFPROBE_BIN に\n"
                  "   新しい ffmpeg / ffprobe のフルパスを入れて実行する",
        "python": "python3 -m venv ~/video-tools-venv\n"
                  "   ~/video-tools-venv/bin/pip install faster-whisper Pillow\n"
                  "   以降は ~/video-tools-venv/bin/python でスクリプトを実行する\n"
                  "   （Homebrew の python に直接 pip すると externally-managed-environment で断られるため）",
        "font": "brew install --cask font-noto-sans-cjk-jp\n"
                "   （入れなくてもヒラギノ角ゴシックで動く。見た目を揃えたいなら入れる）",
    },
    "Windows": {
        "ffmpeg": "winget install --id Gyan.FFmpeg -e\n"
                  "   （入れた直後は PATH に載らないことがあるが、このチェックが WinGet の置き場所から探す）",
        "libass": "字幕の焼き込みに必要な libass が入っていない ffmpeg です。\n"
                  "   winget install --id Gyan.FFmpeg -e で入る版（libass 入り）を使い、\n"
                  "   環境変数 FFMPEG_BIN / FFPROBE_BIN にそのフルパスを入れて実行する",
        "python": "py -m venv %USERPROFILE%\\video-tools-venv\n"
                  "   %USERPROFILE%\\video-tools-venv\\Scripts\\pip install faster-whisper Pillow\n"
                  "   以降は %USERPROFILE%\\video-tools-venv\\Scripts\\python でスクリプトを実行する\n"
                  "   （python 自体が無ければ先に: winget install --id Python.Python.3.12 -e）",
        "font": "Noto Sans JP を入れる: https://fonts.google.com/noto/specimen/Noto+Sans+JP\n"
                "   → ダウンロードした zip の static/NotoSansJP-Bold.ttf を右クリック →「インストール」\n"
                "   （入れなくても游ゴシック / メイリオで動く。見た目を揃えたいなら入れる）",
    },
    "Linux": {
        "ffmpeg": "sudo apt-get install -y ffmpeg",
        "libass": "libass 入りの ffmpeg を入れる（Ubuntu/Debian の apt 版は入っている）",
        "python": "pip install faster-whisper Pillow（必要なら python3 -m venv で仮想環境を作ってから）",
        "font": "sudo apt-get install -y fonts-noto-cjk",
    },
}


def main() -> int:
    common.utf8_stdout()
    fixes = FIX.get(platform.system(), FIX["Linux"])
    need = []
    print(f"OS      : {platform.system()} {platform.release()}")
    print(f"Python  : {sys.version.split()[0]}  ({sys.executable})")

    ff, fp = common.find_tool("ffmpeg"), common.find_tool("ffprobe")
    if ff and fp:
        ver = common.run([ff, "-hide_banner", "-version"]).stdout.splitlines()[:1]
        print(f"ffmpeg  : OK  {ff}  {ver[0] if ver else ''}")
        filters = common.run([ff, "-hide_banner", "-filters"]).stdout
        if " subtitles " in filters:
            print("libass  : OK  （字幕を焼き込める）")
        else:
            print("libass  : なし")
            need.append("libass")
    else:
        print(f"ffmpeg  : なし（ffmpeg={ff} ffprobe={fp}）")
        need.append("ffmpeg")

    missing_py = []
    for mod in ("faster_whisper", "PIL", "numpy"):
        try:
            importlib.import_module(mod)
        except Exception:
            missing_py.append(mod)
    if missing_py:
        print(f"Python  : 足りない → {', '.join(missing_py)}")
        need.append("python")
    else:
        import faster_whisper
        print(f"パッケージ: OK  faster-whisper {faster_whisper.__version__} / Pillow / numpy")

    if "PIL" not in missing_py:
        font = common.find_jp_font()
        if font:
            best = font["family"].startswith("Noto Sans")
            print(f"フォント : OK  {font['family']} {font['style']}  ({font['path']})"
                  + ("" if best else "  ※ハウススタイルは Noto Sans CJK JP。これでも動く"))
        else:
            print("フォント : 日本語の太字フォントが見つからない")
            need.append("font")

    desk = common.desktop_dir()
    print(f"デスクトップ: {desk if desk else '見つからない（納品先をユーザーに確認する）'}")

    cache = Path.home() / ".cache" / "huggingface" / "hub" / "models--Systran--faster-whisper-large-v3"
    print("Whisper : " + ("large-v3 ダウンロード済み" if cache.exists()
                          else "large-v3 未ダウンロード（初回の文字起こしで約3GBを自動取得。数分かかる）"))

    if not need:
        print("\n準備OK。")
        return 0
    print("\n足りないもの:")
    for k in need:
        print(f" - {k}:\n   {fixes[k]}")
    print("\n入れ終わったら、もう一度このスクリプトを実行して確認する。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
