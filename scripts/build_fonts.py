"""Noto Sans CJK JP (Bold / Black) から、テロップ用の woff2 サブセットを作る。

- 収録文字: CP932(JIS X 0208 + Windows拡張) 全文字 + ASCII/Latin-1 + 記号少々
  → 今後のエピソードで文言を変えても、通常の日本語なら文字化けしない範囲。
- 'palt'(プロポーショナル詰め)などの OpenType 機能は残す。
- 元フォント: Ubuntu の fonts-noto-cjk パッケージ (SIL OFL 1.1)。
  `sudo apt-get install fonts-noto-cjk` の後に `python3 scripts/build_fonts.py`。

出力: public/fonts/NotoSansCJKjp-{Bold,Black}.subset.woff2 (生成済みをリポジトリに同梱)
"""
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTCollection

SRC_DIR = Path("/usr/share/fonts/opentype/noto")
OUT_DIR = Path(__file__).resolve().parent.parent / "public" / "fonts"
WEIGHTS = {"Bold": "NotoSansCJK-Bold.ttc", "Black": "NotoSansCJK-Black.ttc"}


def charset() -> set[int]:
    cps: set[int] = set(range(0x20, 0x7F)) | set(range(0xA0, 0x100))
    # CP932 の 2 バイト文字をすべてデコードして収集
    leads = list(range(0x81, 0xA0)) + list(range(0xE0, 0xFD))
    trails = list(range(0x40, 0x7F)) + list(range(0x80, 0xFD))
    for lead in leads:
        for trail in trails:
            try:
                ch = bytes([lead, trail]).decode("cp932")
            except UnicodeDecodeError:
                continue
            cps.update(ord(c) for c in ch)
    cps.update(range(0xFF61, 0xFFA0))  # 半角カナ
    cps.update(range(0x3000, 0x3100))  # CJK記号・ひらがな・カタカナ
    cps.update(ord(c) for c in "…‥–—―‐‘’“”•・♪♫★☆♡♥✓✔→←↑↓⇒～〜！？＝＋－×÷％＃＆＠")
    return cps


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    unicodes = sorted(charset())
    for weight, filename in WEIGHTS.items():
        collection = TTCollection(str(SRC_DIR / filename))
        font = next(f for f in collection.fonts if f["name"].getDebugName(1).startswith("Noto Sans CJK JP"))
        opts = Options()
        opts.flavor = "woff2"
        opts.layout_features = ["*"]  # palt 等を保持
        opts.name_IDs = ["*"]
        opts.name_languages = ["*"]
        opts.notdef_outline = True
        opts.hinting = False
        sub = Subsetter(options=opts)
        sub.populate(unicodes=unicodes)
        sub.subset(font)
        out = OUT_DIR / f"NotoSansCJKjp-{weight}.subset.woff2"
        font.flavor = "woff2"
        font.save(str(out))
        print(f"{out.name}: {len(font.getBestCmap())} chars, {out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
