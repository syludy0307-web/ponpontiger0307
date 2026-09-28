"""video-concat-subtitle の共通部品。

ffmpeg・日本語フォント・デスクトップの場所は OS ごとに違うので、
決め打ちせずに探しにいく。Mac / Windows / Linux のどれでも同じ import で使える。
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

SYSTEM = platform.system()  # 'Darwin' / 'Windows' / 'Linux'


def utf8_stdout() -> None:
    """Windows のコンソール（cp932）でも日本語や韓国語の幻聴テキストで落ちないようにする。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def run(cmd, **kw):
    """文字化けしないよう UTF-8 固定で外部コマンドを実行する。"""
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


# ------------------------------------------------------------------ ffmpeg

def _tool_candidates(tool: str) -> list:
    exe = tool + (".exe" if SYSTEM == "Windows" else "")
    found = []
    env = os.environ.get(f"{tool.upper()}_BIN")          # 例: FFMPEG_BIN=/path/to/ffmpeg
    if env:
        found.append(Path(env))
    which = shutil.which(tool)
    if which:
        found.append(Path(which))
    home = Path.home()
    if SYSTEM == "Darwin":
        # アプリから起動したシェルは Homebrew の PATH を持っていないことがある
        found += [Path("/opt/homebrew/bin") / tool, Path("/usr/local/bin") / tool,
                  Path("/opt/homebrew/opt/ffmpeg-full/bin") / tool]
    elif SYSTEM == "Windows":
        local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        # winget install Gyan.FFmpeg の置き場所。インストール直後は PATH に載っていない
        found += sorted((local / "Microsoft" / "WinGet" / "Packages").glob(f"Gyan.FFmpeg*/*/bin/{exe}"))
        found += [local / "Microsoft" / "WinGet" / "Links" / exe,
                  Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "chocolatey" / "bin" / exe,
                  home / "scoop" / "shims" / exe,
                  Path(r"C:\ffmpeg\bin") / exe]
    else:
        found += [Path("/usr/bin") / tool, Path("/usr/local/bin") / tool]
    return found


def find_tool(tool: str):
    for p in _tool_candidates(tool):
        if p.is_file():
            return str(p)
    return None


def ffmpeg() -> str:
    p = find_tool("ffmpeg")
    if not p:
        sys.exit("ffmpeg が見つかりません。scripts/setup_check.py を実行して案内に従ってください。")
    return p


def ffprobe() -> str:
    p = find_tool("ffprobe")
    if not p:
        sys.exit("ffprobe が見つかりません。scripts/setup_check.py を実行して案内に従ってください。")
    return p


def probe(path) -> dict:
    """尺・表示上の解像度（回転を考慮）・fps・コーデック・音声の有無を返す。"""
    r = run([ffprobe(), "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", path])
    if r.returncode != 0:
        sys.exit(f"ffprobe に失敗しました: {path}\n{r.stderr}")
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s.get("codec_type") == "video"), None)
    a = next((s for s in j["streams"] if s.get("codec_type") == "audio"), None)
    if v is None:
        sys.exit(f"映像が入っていません: {path}")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list") or []:
        if "rotation" in sd:
            rot = int(round(float(sd["rotation"])))
    if not rot and (v.get("tags") or {}).get("rotate"):
        rot = int(v["tags"]["rotate"])
    if abs(rot) % 180 == 90:        # iPhone の縦動画など。ffmpeg は自動で回転して扱う
        w, h = h, w
    fr = v.get("r_frame_rate") or "24/1"
    num, den = fr.split("/")
    fps = float(num) / float(den) if float(den) else 24.0
    nb = str(v.get("nb_frames") or "")
    return {
        "path": str(Path(path).resolve()), "name": Path(path).name,
        "duration": float(j["format"].get("duration") or v.get("duration") or 0),
        "width": w, "height": h, "rotation": rot,
        "fps": fps, "fps_str": fr, "frames": int(nb) if nb.isdigit() else None,
        "vcodec": v.get("codec_name"), "profile": v.get("profile"), "pix_fmt": v.get("pix_fmt"),
        "has_audio": a is not None,
        "acodec": a.get("codec_name") if a else None,
        "sample_rate": int(a["sample_rate"]) if a and a.get("sample_rate") else None,
        "channels": int(a.get("channels") or 0) if a else 0,
    }


def clip_number(path) -> tuple:
    """ファイル名の番号で並べるためのキー。'94d49f9c-001.mov' → 1。

    アップロード順やフォルダの表示順は当てにならない（003 が先頭で届いたことがある）。
    先頭のハッシュ風の文字列に含まれる数字に引っぱられないよう、
    拡張子の直前にある数字のかたまりを番号とみなす。
    """
    stem = Path(path).stem
    m = re.search(r"(\d+)\D*$", stem)
    return (int(m.group(1)) if m else 10 ** 9, stem)


# ------------------------------------------------------------------ デスクトップ

def desktop_dir():
    """ユーザーのデスクトップ。Windows で OneDrive に移されている場合にも対応する。"""
    home = Path.home()
    cands = []
    if SYSTEM == "Windows":
        known = _windows_known_desktop()
        if known:
            cands.append(Path(known))
        for key in ("OneDrive", "OneDriveConsumer"):
            od = os.environ.get(key)
            if od:
                cands += [Path(od) / "Desktop", Path(od) / "デスクトップ"]
    cands += [home / "Desktop", home / "デスクトップ"]
    for c in cands:
        if c.is_dir():
            return c
    return None


def _windows_known_desktop():
    try:
        import ctypes
        import uuid
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                        ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]

        u = uuid.UUID("{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}")    # FOLDERID_Desktop
        guid = GUID(u.fields[0], u.fields[1], u.fields[2], (ctypes.c_ubyte * 8)(*u.bytes[8:]))
        out = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(out)):
            return None
        path = out.value
        ctypes.windll.ole32.CoTaskMemFree(out)
        return path
    except Exception:
        return None


# ------------------------------------------------------------------ 日本語フォント

FONT_DIRS = {
    "Darwin": ["~/Library/Fonts", "/Library/Fonts", "/System/Library/Fonts",
               "/System/Library/Fonts/Supplemental"],
    "Windows": ["%LOCALAPPDATA%/Microsoft/Windows/Fonts", "%WINDIR%/Fonts"],
    "Linux": ["~/.local/share/fonts", "~/.fonts", "/usr/local/share/fonts", "/usr/share/fonts"],
}

# 上ほど優先。ハウススタイルは Noto Sans CJK JP Bold（無料で、どの OS でも見た目が揃う）。
FONT_FILES = [
    "NotoSansCJK-Bold.ttc", "NotoSansCJKjp-Bold.otf", "NotoSansJP-Bold.otf", "NotoSansJP-Bold.ttf",
    "ヒラギノ角ゴシック W6.ttc", "ヒラギノ角ゴシック W7.ttc",     # macOS 標準
    "YuGothB.ttc", "meiryob.ttc", "BIZ-UDGothicB.ttc",           # Windows 標準
    "ipaexg.ttf", "ipag.ttf",                                    # Linux の代替
]


def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", s).lower()      # macOS のファイル名は NFD のことがある


def _walk_fonts():
    for d in FONT_DIRS.get(SYSTEM, []):
        base = Path(os.path.expandvars(os.path.expanduser(d)))
        if base.is_dir():
            for root, _dirs, files in os.walk(base):
                for f in files:
                    yield Path(root) / f


def find_jp_font():
    """太字の日本語フォントを探して {path, index, family, style} を返す。無ければ None。

    環境変数 JP_FONT にフォントファイルのパスを入れると、それを優先する。
    """
    from PIL import ImageFont

    files = []
    override = os.environ.get("JP_FONT")
    if override and Path(override).is_file():
        files.append(Path(override))
    wanted = {_norm(n): rank for rank, n in enumerate(FONT_FILES)}
    files += [p for _r, p in sorted((wanted[_norm(p.name)], p) for p in _walk_fonts()
                                    if _norm(p.name) in wanted)]
    for p in files:
        best = None
        for idx in range(16):
            try:
                f = ImageFont.truetype(str(p), 40, index=idx)
            except Exception:
                break
            fam, style = f.getname()
            if best is None:
                best = (idx, fam, style)
            if "JP" in fam:           # Noto CJK の .ttc には JP 以外の字形も入っている
                best = (idx, fam, style)
                break
        if best:
            idx, fam, style = best
            return {"path": str(p), "index": idx, "family": fam, "style": style}
    return None


def load_font(font_info, size):
    from PIL import ImageFont
    return ImageFont.truetype(font_info["path"], size, index=font_info["index"])
