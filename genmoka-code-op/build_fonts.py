#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ゲンとモカ OP — フォント埋め込みビルド

  1. OFLフォント（Yuji Syuku / Noto Serif JP 可変）を fonts_src/ に用意（無ければ自動取得）
  2. genmoka_op.html から実際に描く文字列（TITLE_MAIN / TITLE_SUB / EPISODE_TITLE）を読み取る
  3. fontTools で使う文字だけにサブセット化（Noto Serif JP は wght=200 / 300 の静的インスタンスを生成）
  4. woff2 → base64 にして HTML の /*@@FONTS_BEGIN@@*/ 〜 /*@@FONTS_END@@*/ に埋め込む

EPISODE_TITLE を差し替えたら、このスクリプトを再実行してください。
  python build_fonts.py
"""
import base64
import io
import os
import re
import sys
import urllib.request

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "genmoka_op.html")
SRC = os.path.join(HERE, "fonts_src")
OUTDIR = os.path.join(HERE, "fonts")

# google/fonts リポジトリ（OFL）の jsDelivr ミラー
SOURCES = {
    "YujiSyuku-Regular.ttf": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/yujisyuku/YujiSyuku-Regular.ttf",
    "NotoSerifJP-VF.ttf": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notoserifjp/NotoSerifJP%5Bwght%5D.ttf",
    "OFL_YujiSyuku.txt": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/yujisyuku/OFL.txt",
    "OFL_NotoSerifJP.txt": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notoserifjp/OFL.txt",
}

# 明朝体には差し替えに備えて、かな・数字・約物も常に入れておく（漢字は HTML から自動抽出）
KANA = "".join(chr(c) for c in range(0x3041, 0x3097)) + "".join(chr(c) for c in range(0x30A1, 0x30FB)) + "ー"
SAFETY = KANA + "0123456789０１２３４５６７８９「」『』（）()、。・！？!?〜～ 　:：-‐—"


def fetch_sources():
    os.makedirs(SRC, exist_ok=True)
    for name, url in SOURCES.items():
        path = os.path.join(SRC, name)
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            continue
        print(f"  download {name} ...", flush=True)
        with urllib.request.urlopen(url, timeout=120) as r:
            data = r.read()
        with open(path, "wb") as f:
            f.write(data)


def read_strings(html):
    def const(name):
        m = re.search(r"const\s+" + name + r"\s*=\s*(['\"])(.*?)\1\s*;", html)
        if not m:
            sys.exit(f"ERROR: {name} が HTML に見つかりません")
        return m.group(2)

    return const("TITLE_MAIN"), const("TITLE_SUB"), const("EPISODE_TITLE")


def subset_font(path, text, wght=None):
    font = TTFont(path)
    opts = subset.Options()
    opts.flavor = None
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.name_legacy = True
    opts.name_languages = ["*"]
    opts.notdef_outline = True
    opts.glyph_names = False
    opts.hinting = False
    sub = subset.Subsetter(options=opts)
    sub.populate(text=text)
    sub.subset(font)
    if wght is not None and "fvar" in font:
        font = instancer.instantiateVariableFont(font, {"wght": wght}, updateFontNames=False)
    cmap = font.getBestCmap()
    missing = sorted({ch for ch in text if ch.strip() and ord(ch) not in cmap})
    if missing:
        sys.exit(f"ERROR: {os.path.basename(path)} に無い文字: {''.join(missing)}")
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue(), len(font.getGlyphOrder())


def main():
    fetch_sources()
    with open(HTML, "r", encoding="utf-8") as f:
        html = f.read()
    title_main, title_sub, episode = read_strings(html)
    brush_text = title_main
    mincho_text = "".join(sorted(set(title_sub + episode + SAFETY)))
    print(f"  筆文字 : {brush_text}")
    print(f"  明朝   : {title_sub} / {episode}  (+かな・数字・約物 {len(SAFETY)}字)")

    jobs = [
        ("GMBrush", 400, os.path.join(SRC, "YujiSyuku-Regular.ttf"), brush_text, None, "YujiSyuku-subset.woff2"),
        ("GMMincho", 200, os.path.join(SRC, "NotoSerifJP-VF.ttf"), mincho_text, 200, "NotoSerifJP-ExtraLight-subset.woff2"),
        ("GMMincho", 300, os.path.join(SRC, "NotoSerifJP-VF.ttf"), mincho_text, 300, "NotoSerifJP-Light-subset.woff2"),
    ]
    os.makedirs(OUTDIR, exist_ok=True)
    faces = []
    for family, weight, path, text, wght, outname in jobs:
        data, nglyphs = subset_font(path, text, wght)
        with open(os.path.join(OUTDIR, outname), "wb") as f:
            f.write(data)
        b64 = base64.b64encode(data).decode("ascii")
        faces.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:%d;font-display:block;"
            "src:url(data:font/woff2;base64,%s) format('woff2');}" % (family, weight, b64)
        )
        print(f"  {outname}: {nglyphs} glyphs, {len(data)/1024:.1f} KB")

    block = "/*@@FONTS_BEGIN@@*/\n" + "\n".join(faces) + "\n/*@@FONTS_END@@*/"
    new_html, n = re.subn(r"/\*@@FONTS_BEGIN@@\*/.*?/\*@@FONTS_END@@\*/", lambda m: block, html, flags=re.S)
    if n != 1:
        sys.exit("ERROR: HTML に /*@@FONTS_BEGIN@@*/ 〜 /*@@FONTS_END@@*/ マーカーがありません")
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"  embedded → {os.path.basename(HTML)} ({len(new_html.encode('utf-8'))/1024:.1f} KB)")


if __name__ == "__main__":
    main()
