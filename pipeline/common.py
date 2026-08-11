# -*- coding: utf-8 -*-
"""Shared constants and helpers for the haunted-hospital video pipeline."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "source")
BUILD = os.path.join(ROOT, "build")
STILLS = os.path.join(BUILD, "stills")
CLIPS = os.path.join(BUILD, "clips")
OUT = os.path.join(ROOT, "output")

SRT_PATH = os.path.join(SRC, "narration.srt")
AUDIO_PATH = os.path.join(SRC, "narration.mp3")

W, H = 1920, 1080          # output frame
AW, AH = 2688, 1512        # art overscan (1.4x) for Ken Burns headroom
FPS = 30
DUR_TOTAL = 676.57         # audio duration (s)

F_SANS = "Noto Sans CJK JP"
F_SANS_BLACK = "Noto Sans CJK JP Black"
F_SERIF = "Noto Serif CJK JP"
F_SERIF_BLACK = "Noto Serif CJK JP Black"
F_MONO = "Noto Sans Mono CJK JP"

FONT_SANS_TTC = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_BLACK_TTC = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_SERIF_TTC = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
FONT_REG_TTC = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def ts_to_s(ts):
    m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)", ts.strip())
    h, mi, s, ms = (int(g) for g in m.groups())
    return h * 3600 + mi * 60 + s + ms / 1000.0


def parse_srt(path=SRT_PATH):
    """Return list of {idx, start, end, text}."""
    raw = open(path, encoding="utf-8-sig").read()
    entries = []
    for block in re.split(r"\n\s*\n", raw.strip()):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 3:
            continue
        idx = int(lines[0])
        a, b = lines[1].split("-->")
        text = " ".join(lines[2:]).strip()
        entries.append({"idx": idx, "start": ts_to_s(a), "end": ts_to_s(b), "text": text})
    return entries


def ensure_dirs():
    for d in (BUILD, STILLS, CLIPS, OUT):
        os.makedirs(d, exist_ok=True)


if __name__ == "__main__":
    subs = parse_srt()
    print(json.dumps({"n": len(subs), "first": subs[0], "last": subs[-1]}, ensure_ascii=False, indent=1))
