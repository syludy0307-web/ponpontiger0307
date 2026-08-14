# -*- coding: utf-8 -*-
"""Generate scene stills + overlay layers.  Usage:
    python3 gen_art.py            # everything missing
    python3 gen_art.py name ...   # named builders only (force)
    python3 gen_art.py --sheet    # contact sheet of all stills
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import STILLS, ensure_dirs, PROJ

SCENES = importlib.import_module(
    "scenes" if PROJ == "haibyouin" else f"{PROJ}_scenes").SCENES
A = importlib.import_module(
    "art_scenes" if PROJ == "haibyouin" else f"{PROJ}_art")


def build(name, force=False):
    path = os.path.join(STILLS, f"{name}.png")
    if os.path.exists(path) and not force:
        return path, False
    if name in A.BUILDERS:
        img = A.BUILDERS[name]()
    elif name in A.OVERLAYS:
        img = A.OVERLAYS[name]()
    else:
        raise KeyError(f"no builder for {name}")
    img.save(path)
    return path, True


def contact_sheet(names, out, cols=5, cell=384):
    from PIL import Image, ImageDraw
    import art_base as B
    rows = (len(names) + cols - 1) // cols
    ch = int(cell * 9 / 16) + 30
    sheet = Image.new("RGB", (cols * cell, rows * ch), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    f = B.font(22, "bold")
    for i, n in enumerate(names):
        p = os.path.join(STILLS, f"{n}.png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB").resize((cell, int(cell * 9 / 16)))
        x, y = (i % cols) * cell, (i // cols) * ch
        sheet.paste(im, (x, y))
        d.text((x + 8, y + int(cell * 9 / 16) + 4), n, font=f, fill=(220, 220, 225))
    sheet.save(out)
    return out


if __name__ == "__main__":
    ensure_dirs()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    arts = list(dict.fromkeys(s["art"] for s in SCENES))
    ovs = sorted({o["img"] for s in SCENES for o in s.get("overlays", [])})
    if args:
        targets = args
        for n in targets:
            p, made = build(n, force=True)
            print(("built " if made else "cached ") + n)
    else:
        for n in arts + ovs:
            p, made = build(n)
            print(("built " if made else "cached ") + n, flush=True)
    if "--sheet" in sys.argv:
        out = contact_sheet(arts, os.path.join(STILLS, "_sheet.png"))
        print("sheet:", out)
