# -*- coding: utf-8 -*-
"""Kinetic typography + narration subtitles -> build/main.ass

Layers: 0 panel bg / 1 rings-bars / 2 overlay text / 3 chroma dupes /
        4 HUD / 5 narration subs.
Colors are ASS &HBBGGRR&.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, parse_srt, ensure_dirs

RED = "&H3226D9&"       # d92632
DRED = "&H1C15A8&"      # a8151c
CYAN = "&HD4E07F&"      # 7fe0d4
WHITE = "&HF0F0F2&"
PALE = "&HDAE4E8&"
INK = "&H141210&"
YEL = "&H58C8E8&"       # e8c858

F_SANS = "Noto Sans CJK JP"
F_BLACK = "Noto Sans CJK JP Black"
F_SERIF = "Noto Serif CJK JP Black"
F_MONO = "Noto Sans Mono CJK JP"

EVENTS = []


def tf(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def ev(layer, t0, t1, style, text, name=""):
    EVENTS.append((layer, t0, t1, style, name, text))


# ---------------------------------------------------------------- helpers
def slam(t0, t1, text, x, y, size=96, color=WHITE, serif=True, chroma=True,
         shake=True, spacing=4, layer=2):
    """Impact pop: overshoot scale-in + rotational settle + chromatic dupes."""
    st = "Serif" if serif else "Black"
    rot = "\\frz2.4\\t(0,90,\\frz-1.2)\\t(90,190,\\frz0)" if shake else ""
    base = (f"{{\\an5\\pos({x},{y})\\fs{size}\\1c{color}\\fsp{spacing}"
            f"\\fscx240\\fscy240\\t(0,140,0.6,\\fscx100\\fscy100){rot}"
            f"\\fad(40,110)\\bord{max(2, size // 30)}\\blur1.2}}{text}")
    ev(layer, t0, t1, st, base)
    if chroma:
        for dx, dy, c in ((-4, -2, RED), (4, 2, CYAN)):
            ghost = (f"{{\\an5\\pos({x + dx},{y + dy})\\fs{size}\\1c{c}\\alpha&HA8&"
                     f"\\fsp{spacing}\\fscx240\\fscy240\\t(0,140,0.6,\\fscx100\\fscy100)"
                     f"\\fad(40,110)\\bord0\\blur2}}{text}")
            ev(3, t0, min(t1, t0 + 0.55), st, ghost)


def chip(t0, t1, text, x, y, size=44, color=WHITE, accent=RED, an=5, w_pad=26,
         serif=False):
    """Boxed keyword chip with wipe-in bg bar + text."""
    n = len(text)
    w = int(size * (n * 1.02) / 2) * 2 + w_pad * 2
    h = size + 30
    x0, y0 = x - w // 2, y - h // 2
    bar = (f"{{\\an7\\pos({x0},{y0})\\1c{INK}\\alpha&H28&\\bord0\\shad0\\p1"
           f"\\clip({x0},{y0},{x0},{y0 + h})"
           f"\\t(0,160,\\clip({x0},{y0},{x0 + w},{y0 + h}))\\fad(0,90)}}"
           f"m 0 0 l {w} 0 l {w} {h} l 0 {h}{{\\p0}}")
    ev(0, t0, t1, "Black", bar)
    acc = (f"{{\\an7\\pos({x0},{y0})\\1c{accent}\\bord0\\shad0\\p1\\fad(60,90)}}"
           f"m 0 0 l 10 0 l 10 {h} l 0 {h}{{\\p0}}")
    ev(1, t0, t1, "Black", acc)
    st = "Serif" if serif else "Black"
    ev(2, t0, t1, st,
       f"{{\\an5\\pos({x + 5},{y})\\fs{size}\\1c{color}\\bord2.4\\blur0.8\\fsp2"
       f"\\fad(90,90)}}{text}")


def quote(t0, t1, text, x, y, size=64, color=PALE, fade=400, spacing=10):
    """Slow serif quote, letterspaced, gentle rise."""
    ev(2, t0, t1, "Serif",
       f"{{\\an5\\move({x},{y + 14},{x},{y},0,{int(fade * 1.4)})\\fs{size}\\1c{color}"
       f"\\fsp{spacing}\\bord2.6\\blur1.4\\fad({fade},{min(300, fade)})}}{text}")


def smalltag(t0, t1, text, x, y, size=34, color=CYAN, an=7):
    ev(2, t0, t1, "Mono",
       f"{{\\an{an}\\pos({x},{y})\\fs{size}\\1c{color}\\bord2\\blur0.6\\fsp3"
       f"\\fad(120,120)}}{text}")


def ring(t0, x, y, r0=26, r1=110, dur=0.9, color=RED, width=5, layer=1):
    """Expanding fading circle (scaled \\p drawing)."""
    d = r0 * 2
    sc0, sc1 = 100, int(100 * r1 / r0)
    ev(layer, t0, t0 + dur, "Black",
       f"{{\\an5\\pos({x},{y})\\1a&HFF&\\3c{color}\\bord{width}\\blur1"
       f"\\fscx{sc0}\\fscy{sc0}\\t(0,{int(dur * 1000)},\\fscx{sc1}\\fscy{sc1})"
       f"\\fad(0,{int(dur * 700)})\\p1}}m 0 {r0} b 0 {int(r0 * 0.45)} {int(r0 * 0.45)} 0 {r0} 0 "
       f"b {int(r0 * 1.55)} 0 {d} {int(r0 * 0.45)} {d} {r0} "
       f"b {d} {int(r0 * 1.55)} {int(r0 * 1.55)} {d} {r0} {d} "
       f"b {int(r0 * 0.45)} {d} 0 {int(r0 * 1.55)} 0 {r0}{{\\p0}}")


def hrule(t0, t1, x, y, w, color=RED, h=6, dur=260):
    x0 = x - w // 2
    ev(1, t0, t1, "Black",
       f"{{\\an7\\pos({x0},{y})\\1c{color}\\bord0\\shad0\\p1"
       f"\\clip({x0},{y - 4},{x0},{y + h + 4})"
       f"\\t(0,{dur},\\clip({x0},{y - 4},{x0 + w},{y + h + 4}))\\fad(0,120)}}"
       f"m 0 0 l {w} 0 l {w} {h} l 0 {h}{{\\p0}}")


# ---------------------------------------------------------------- narration subs
EMPH = ["幽霊", "心霊現象", "心霊スポット", "霊安室", "少年の霊", "女性の霊", "足音",
        "人影", "うめき声", "ナースコール", "血まみれ", "白装束", "儀式", "目の部屋",
        "巨大な目", "ハイヒールの音", "隔離", "地下", "立入", "閉院", "負債", "廃病院",
        "白い顔", "話し声", "寒気", "吐き気", "明かり", "声"]


def stylize_sub(text):
    text = text.replace(" ", "  ")
    for w in EMPH:
        if w in text:
            text = text.replace(w, f"{{\\1c{RED}\\b1}}{w}{{\\1c{WHITE}\\b0}}", 1)
    return text


def narration():
    subs = parse_srt()
    for s in subs:
        txt = stylize_sub(s["text"])
        ev(5, s["start"], s["end"], "Sub", f"{{\\fad(110,90)}}{txt}")


# ---------------------------------------------------------------- HUD (found footage)
def rec_hud(t0, t1, base_tc=(2, 47, 13), label="NIGHT MODE"):
    # corner brackets
    for (bx, by, sx, sy) in ((70, 60, 1, 1), (1850, 60, -1, 1),
                             (70, 1020, 1, -1), (1850, 1020, -1, -1)):
        ev(4, t0, t1, "Black",
           f"{{\\an7\\pos({bx},{by})\\1c&HE8F2EA&\\alpha&H50&\\bord0\\shad0\\p1}}"
           f"m 0 0 l {56 * sx} 0 l {56 * sx} {10 * sy} l {12 * sx} {10 * sy} "
           f"l {12 * sx} {56 * sy} l 0 {56 * sy}{{\\p0}}")
    # blinking REC
    t = t0
    while t < t1:
        ev(4, t, min(t + 0.55, t1), "Mono",
           f"{{\\an7\\pos(118,84)\\fs40\\1c{RED}\\bord0\\blur0.6}}●"
           f"{{\\1c&HE8F2EA&\\fsp6}} REC")
        t += 1.0
    ev(4, t0, t1, "Mono",
       f"{{\\an9\\pos(1802,84)\\fs34\\1c&HC8E8D0&\\alpha&H30&\\bord0\\fsp2}}{label}")
    # counting timecode
    h0, m0, s0 = base_tc
    total0 = h0 * 3600 + m0 * 60 + s0
    t = t0
    while t < t1:
        cur = total0 + int(t - t0)
        tc = f"{cur // 3600:02d}:{cur % 3600 // 60:02d}:{cur % 60:02d}"
        ev(4, t, min(t + 1.0, t1), "Mono",
           f"{{\\an9\\pos(1802,132)\\fs40\\1c&HE8F2EA&\\bord0\\blur0.4\\fsp3}}{tc}")
        t += 1.0
    ev(4, t0, t1, "Mono",
       f"{{\\an1\\pos(118,1016)\\fs30\\1c&HC8E8D0&\\alpha&H40&\\bord0\\fsp2}}"
       "AF●  ISO 51200  ▮▮▮▯")


# ---------------------------------------------------------------- structural pieces
RANKS = [
    (5, "黒瀬病院", "広島県東広島市", 31.64, 33.92, 137.04),
    (4, "旧相武病院", "東京都八王子市", 137.04, 139.84, 236.40),
    (3, "旧野木病院", "栃木県野木町", 236.40, 239.08, 357.88),
    (2, "小美玉小川脳病院", "茨城県小美玉市", 357.88, 360.32, 443.84),
    (1, "姫川病院", "新潟県糸魚川市", 445.84, 448.40, 631.76),
]


def rank_cards():
    for rank, name, loc, t0, t1, tend in RANKS:
        big_red = rank == 1
        col = RED if big_red else WHITE
        # mega number, right side
        ev(2, t0, t1, "Black",
           f"{{\\an5\\pos(1450,470)\\fs560\\1c{col}\\bord10\\3c{INK}\\blur2\\fsp0"
           f"\\fscx260\\fscy260\\t(0,160,0.55,\\fscx100\\fscy100)"
           f"\\frz3\\t(0,100,\\frz-1.5)\\t(100,220,\\frz0)\\fad(30,140)}}{rank}")
        for dx, c in ((-7, RED), (7, CYAN)):
            ev(3, t0, t0 + 0.5, "Black",
               f"{{\\an5\\pos({1450 + dx},468)\\fs560\\1c{c}\\alpha&H96&\\bord0\\blur3"
               f"\\fscx260\\fscy260\\t(0,160,0.55,\\fscx100\\fscy100)\\fad(20,80)}}{rank}")
        ev(2, t0 + 0.10, t1, "Black",
           f"{{\\an5\\pos(1450,205)\\fs64\\1c{PALE}\\fsp14\\bord3\\blur0.8\\fad(90,140)}}"
           f"第 {rank} 位")
        # name lockup, left
        nsize = 130 if len(name) <= 5 else 96
        ev(2, t0 + 0.28, t1, "Serif",
           f"{{\\an4\\move(180,545,220,545,0,220)\\fs{nsize}\\1c{WHITE}\\fsp4"
           f"\\bord5\\blur1.4\\fad(110,140)}}{name}")
        for dx, c in ((-4, RED), (4, CYAN)):
            ev(3, t0 + 0.28, t0 + 0.8, "Serif",
               f"{{\\an4\\move({180 + dx},543,{220 + dx},543,0,220)\\fs{nsize}\\1c{c}"
               f"\\alpha&HA0&\\bord0\\blur2.4\\fad(90,90)}}{name}")
        hrule(t0 + 0.42, t1, 610, 640, 860, RED if big_red else "&H8890A0&", 7)
        ev(2, t0 + 0.5, t1, "Mono",
           f"{{\\an4\\pos(224,700)\\fs46\\1c{CYAN}\\fsp8\\bord2.6\\fad(130,140)}}"
           f"{loc}")
        if big_red:
            ev(0, t0, t1, "Black",
               f"{{\\an7\\pos(0,0)\\1c{DRED}\\alpha&HC8&\\bord0\\shad0\\p1"
               f"\\fad(60,180)}}m 0 500 l 1920 460 l 1920 620 l 0 660{{\\p0}}")


def section_headers():
    for rank, name, loc, t0, t1, tend in RANKS:
        hd = f"▍第{rank}位  {name} ── {loc}"
        ev(4, t1 + 0.8, tend - 0.3, "Mono",
           f"{{\\an7\\pos(56,44)\\fs33\\1c&HE6ECF0&\\alpha&H48&\\bord2\\3c{INK}"
           f"\\fsp2\\fad(240,240)}}{hd}")
        # progress diamonds top-right
        cells = []
        for i, r in enumerate([5, 4, 3, 2, 1]):
            on = r >= rank
            cells.append(f"{{\\1c{RED if r == rank else '&H667080&'}"
                         f"\\alpha&H{'30' if on else '90'}&}}◆")
        ev(4, t1 + 0.8, tend - 0.3, "Mono",
           f"{{\\an9\\pos(1864,48)\\fs30\\bord2\\3c{INK}\\fsp6\\fad(240,240)}}"
           + "".join(cells))


def info_card(t0, t1, rows, x=140, y=210):
    """Case-file panel: rows = [(label, value, t_offset)]."""
    w, h = 640, 76 + 86 * len(rows)
    ev(0, t0, t1, "Black",
       f"{{\\an7\\pos({x},{y})\\1c&H100E0C&\\alpha&H48&\\bord0\\shad0\\p1"
       f"\\clip({x},{y},{x + w},{y})\\t(0,220,\\clip({x},{y},{x + w},{y + h}))"
       f"\\fad(0,160)}}m 0 0 l {w} 0 l {w} {h} l 0 {h}{{\\p0}}")
    ev(1, t0, t1, "Black",
       f"{{\\an7\\pos({x},{y})\\1c{RED}\\bord0\\shad0\\p1\\fad(80,160)}}"
       f"m 0 0 l 12 0 l 12 {h} l 0 {h}{{\\p0}}")
    ev(2, t0 + 0.12, t1, "Mono",
       f"{{\\an7\\pos({x + 40},{y + 22})\\fs30\\1c{RED}\\bord0\\fsp6\\fad(90,140)}}"
       "▣ CASE FILE")
    for i, (lab, val, dt) in enumerate(rows):
        yy = y + 76 + i * 86
        ts = t0 + dt
        ev(2, ts, t1, "Mono",
           f"{{\\an7\\pos({x + 40},{yy})\\fs30\\1c{CYAN}\\bord0\\fsp3\\fad(110,140)}}"
           f"{lab}")
        ev(2, ts + 0.10, t1, "Black",
           f"{{\\an7\\pos({x + 40},{yy + 30})\\fs42\\1c{WHITE}\\bord2.6\\blur0.6"
           f"\\fad(110,140)}}{val}")


def stat_slam(t0, t1, num, label, x, y, nsize=170, color=RED):
    ev(2, t0, t1, "Mono",
       f"{{\\an4\\pos({x},{y})\\fs{nsize}\\1c{color}\\bord6\\3c{INK}\\blur1"
       f"\\fscx240\\fscy240\\t(0,150,0.55,\\fscx100\\fscy100)"
       f"\\frz-2\\t(0,120,\\frz0)\\fad(30,160)}}{num}")
    ev(2, t0 + 0.14, t1, "Black",
       f"{{\\an4\\pos({x + 12},{y + nsize * 0.62})\\fs46\\1c{PALE}\\fsp10\\bord2.6"
       f"\\fad(110,160)}}{label}")
    hrule(t0 + 0.05, t1, x + 260, int(y + nsize * 0.98), 520, "&H5A6478&", 4)


# ---------------------------------------------------------------- cue script
def cues():
    # ---- INTRO
    smalltag(0.35, 3.6, "日本に現在も残る――", 78, 96, 40)
    slam(0.95, 8.80, "廃病院", 960, 330, 250, WHITE, serif=True, spacing=14)
    ev(2, 3.95, 8.80, "Serif",
       f"{{\\an5\\pos(960,505)\\fs52\\1c{PALE}\\fsp16\\bord2.6\\fad(300,120)}}"
       "幽霊が出ると噂される")
    ev(0, 5.92, 8.80, "Black",
       f"{{\\an7\\pos(530,584)\\1c{DRED}\\alpha&H70&\\bord0\\shad0\\p1"
       f"\\clip(960,520,960,704)\\t(0,150,\\clip(100,520,1820,704))\\fad(0,120)}}"
       "m 0 0 l 860 0 l 860 112 l 0 112{\\p0}")
    slam(6.02, 8.80, "心霊スポット TOP5", 960, 640, 92, WHITE, serif=False,
         chroma=True, spacing=6)
    chip(9.3, 13.7, "かつての姿", 250, 160, 44, WHITE, CYAN)
    chip(14.3, 17.2, "現在", 220, 160, 48, WHITE, RED)
    quote(16.5, 21.5, "聞こえるはずのない \"声\"", 960, 300, 62)
    slam(19.4, 21.55, "足音", 1350, 430, 110, RED)
    # map scene
    ev(2, 22.1, 31.3, "Mono",
       f"{{\\an2\\pos(960,1002)\\fs38\\1c{CYAN}\\bord2.6\\fsp4\\fad(200,150)}}"
       "解体済みは除外 ── 現存する建物のみを厳選")
    ev(2, 25.3, 31.3, "Serif",
       f"{{\\an5\\pos(1595,205)\\fs86\\1c{RED}\\bord5\\3c&HE8E8F0&\\xbord6\\ybord6"
       f"\\frz-11\\fscx320\\fscy320\\t(0,130,0.5,\\fscx100\\fscy100)\\fad(20,160)}}全件現存")
    smalltag(28.95, 31.4, "COUNTDOWN ▶", 1660, 990, 34, RED, an=7)

    # ---- #5 KUROSE
    info_card(34.4, 43.6, [
        ("通称", "黒瀬病院", 0.0),
        ("正式名称", "正仁クリニック", 6.2),
        ("所在地", "広島県東広島市", 1.2),
        ("現況", "住宅街の中に現存", 2.4),
    ])
    chip(44.5, 50.0, "山奥ではなく――", 1470, 220, 46)
    slam(48.35, 55.0, "住宅街のド真ん中", 1170, 400, 96, WHITE)
    quote(58.9, 66.3, "時間だけが、止まった建物", 960, 260, 66)
    rec_hud(66.75, 77.9, (2, 47, 13))
    chip(68.3, 72.0, "足音だけが聞こえる", 1360, 240, 44, WHITE, RED)
    chip(72.3, 76.4, "窓の向こうに人影", 460, 300, 46, WHITE, RED)
    slam(73.4, 77.6, "少年の霊", 480, 470, 100, RED)
    chip(78.5, 83.9, "こちらを覗く\"何か\"", 1380, 260, 46)
    slam(84.9, 90.0, "屋上に、誰か", 1280, 300, 92, PALE)
    quote(89.0, 92.7, "外から見ているだけなのに", 960, 250, 56)
    # dusk sound contrast panels
    for tick in range(0, 63):
        tt = 93.8 + tick * 0.33
        if tt > 114.3:
            break
        import random as _r
        _r.seed(tick)
        bars = "".join(
            f"m {i * 26} {40 - h} l {i * 26 + 14} {40 - h} l {i * 26 + 14} 40 l {i * 26} 40 "
            for i, h in enumerate(_r.choices(range(6, 40), k=5)))
        ev(1, tt, min(tt + 0.35, 114.4), "Black",
           f"{{\\an7\\pos(300,300)\\1c{YEL}\\alpha&H30&\\bord0\\shad0\\p1}}{bars}{{\\p0}}")
    ev(1, 93.8, 114.4, "Black",
       f"{{\\an7\\pos(1500,332)\\1c&H8890A0&\\bord0\\shad0\\p1\\fad(200,200)}}"
       "m 0 0 l 130 0 l 130 6 l 0 6{\\p0}")
    smalltag(93.8, 114.4, "住宅街 ── 生活音", 300, 250, 32, YEL)
    smalltag(93.8, 114.4, "廃病院 ── 無音", 1500, 282, 32, "&HAEB6C4&")
    chip(116.4, 121.3, "荒れたままの外壁", 1420, 240, 44)
    chip(121.6, 126.3, "放置された年月", 480, 240, 44)
    quote(127.0, 136.5, "住宅街に、廃墟だけが取り残されている", 960, 270, 58)

    # ---- #4 SOBU
    info_card(140.3, 148.8, [
        ("名称", "旧相武病院", 0.0),
        ("所在地", "東京都八王子市", 1.0),
        ("特記", "都内に現存する大型廃病院", 2.2),
        ("現況", "厳重管理下", 3.4),
    ])
    chip(150.0, 154.6, "女性の幽霊の噂", 1420, 240, 46, WHITE, RED)
    slam(154.95, 160.3, "長い髪の女", 1250, 380, 104, PALE)
    chip(160.8, 165.2, "首を絞め付けられる感覚", 1250, 560, 44, WHITE, RED)
    smalltag(165.7, 168.9, "さらに不気味な噂――", 90, 120, 40, "&HAEB6C4&")
    slam(169.2, 177.4, "目の部屋", 1330, 300, 150, RED)
    chip(172.2, 177.4, "壁に描かれた巨大な目", 1330, 470, 44)
    ev(2, 177.9, 186.8, "Serif",
       f"{{\\an5\\pos(960,240)\\fs58\\1c{PALE}\\fsp12\\bord3\\blur1.2\\fad(500,300)}}"
       f"その目を見た者には {{\\1c{RED}}}良くないこと{{\\1c{PALE}}} が起こる")
    quote(183.6, 189.1, "部屋だけが、こちらを見ている", 960, 400, 54)
    chip(190.0, 195.0, "現在も厳重に管理", 1460, 240, 44)
    chip(196.9, 202.5, "外から見ても感じる\"重さ\"", 1420, 240, 42)
    chip(205.6, 210.6, "誰もいないはずの窓", 470, 240, 46)
    slam(207.3, 212.4, "明かり", 1310, 430, 120, YEL)
    quote(209.1, 216.2, "そこにいるのは、誰?", 960, 270, 64)
    chip(217.0, 222.4, "女の霊", 700, 240, 46, WHITE, RED)
    chip(217.6, 222.4, "目の部屋", 1220, 240, 46, WHITE, RED)
    quote(225.6, 232.0, "無人の空間は、迷路になる", 960, 260, 60)
    smalltag(232.3, 236.1, "東京都内・屈指の不気味さ", 1560, 980, 34, RED, an=7)

    # ---- #3 NOGI
    info_card(239.6, 251.8, [
        ("名称", "旧野木病院", 0.0),
        ("旧称", "野木厚生クリニック", 1.0),
        ("所在地", "栃木県野木町", 2.2),
        ("種別", "精神科系(とされる)", 3.4),
    ])
    chip(244.4, 249.0, "栃木三大廃病院", 1440, 240, 48)
    slam(249.35, 251.9, "現存する最後の一つ", 1200, 420, 76, RED)
    # timeline chips
    tl = [("1985", "開業", 252.5), ("精神科の病院", "", 256.9),
          ("閉院", "", 263.7), ("老人ホーム計画", "", 266.6),
          ("改装中断", "", 269.9), ("現在も放置", "", 272.2)]
    for i, (big, sub_, ts) in enumerate(tl):
        x = 300 + i * 275
        ev(1, ts, 277.4, "Black",
           f"{{\\an7\\pos({x - 108},226)\\1c{RED}\\bord0\\shad0\\p1\\fad(80,140)}}"
           "m 0 0 l 8 0 l 8 60 l 0 60{\\p0}")
        ev(2, ts, 277.4, "Black",
           f"{{\\an4\\pos({x - 84},240)\\fs40\\1c{WHITE}\\bord2.6\\fad(90,140)}}"
           f"{big}{('  ' + sub_) if sub_ else ''}")
        if i:
            ev(1, ts, 277.4, "Black",
               f"{{\\an7\\pos({x - 150},252)\\1c&H667080&\\bord0\\shad0\\p1\\fad(80,140)}}"
               "m 0 0 l 30 0 l 30 5 l 0 5{\\p0}")
    slam(278.1, 283.9, "女の幽霊", 1290, 350, 100, PALE)
    slam(284.5, 291.0, "白装束の集団", 1210, 300, 110, PALE)
    chip(286.5, 293.5, "深夜の\"儀式\"", 1210, 470, 46, WHITE, RED, serif=True)
    quote(296.1, 299.3, "生きた人間か、別の何かか", 960, 250, 58)
    rec_hud(299.7, 313.4, (3, 12, 44))
    chip(302.1, 306.6, "誰もいない場所から声", 1350, 240, 42, WHITE, RED)
    slam(305.0, 309.6, "白い顔", 500, 420, 110, PALE)
    chip(314.0, 318.3, "昼でも光が届かない", 1420, 240, 44)
    chip(318.6, 322.6, "増え続ける落書き", 460, 240, 44)
    quote(323.0, 328.5, "それでも、建物は残り続ける", 960, 260, 58)
    smalltag(329.2, 331.4, "白い人影は――", 700, 380, 46, PALE)
    slam(331.7, 335.0, "一人とは限らない", 960, 480, 100, RED)
    chip(338.0, 343.4, "再利用計画 → 中断", 1440, 220, 44)
    quote(344.4, 350.4, "完成しないまま、止まった建物", 960, 250, 56)
    quote(351.5, 357.5, "病院の痕跡と、工事の痕跡が混ざる", 960, 250, 52)

    # ---- #2 OGAWA
    info_card(360.8, 370.2, [
        ("通称", "小美玉小川脳病院", 0.0),
        ("正式名称", "聖仁会小川病院(とされる)", 1.0),
        ("所在地", "茨城県小美玉市", 2.2),
        ("種別", "精神科系", 3.4),
    ])
    chip(371.0, 375.3, "森の奥へ", 1480, 240, 48)
    quote(375.6, 379.6, "近づくだけで、空気が変わる", 960, 250, 56)
    chip(380.0, 382.1, "窓に残る頑丈な格子", 1400, 430, 44, WHITE, RED)
    slam(384.6, 390.2, "隔離病棟", 1330, 300, 130, RED)
    chip(387.3, 390.2, "閉鎖的な病室", 1330, 470, 44)
    chip(391.2, 396.4, "奥から、話し声", 1380, 240, 46, WHITE, RED)
    slam(402.1, 404.6, "女らしい姿", 1270, 380, 96, PALE)
    chip(405.2, 409.0, "突然の寒気・吐き気", 1380, 240, 44, WHITE, RED)
    slam(411.5, 416.4, "地下の噂", 1300, 400, 110, RED)
    chip(417.0, 422.3, "格子の付いた窓", 1420, 240, 44)
    chip(422.9, 427.8, "光の届かない廊下", 960, 240, 44)
    chip(428.4, 432.9, "森の中に、そのまま", 960, 240, 44)
    chip(433.7, 438.9, "誰もいない病室から声", 1380, 240, 44, WHITE, RED)
    quote(439.3, 443.5, "そこに、患者の姿はない", 960, 260, 60)
    smalltag(441.6, 443.6, "そして――", 1700, 960, 40, RED, an=7)

    # ---- #1 HIMEKAWA
    ring(444.1, 960, 540, 30, 320, 1.2, DRED, 7)
    ring(444.9, 960, 540, 30, 380, 1.2, DRED, 7)
    info_card(448.9, 459.2, [
        ("名称", "姫川病院", 0.0),
        ("所在地", "新潟県糸魚川市", 1.0),
        ("規模", "巨大総合病院級", 2.2),
        ("現況", "全景がそのまま現存", 3.4),
    ])
    stat_slam(459.9, 471.1, "1987", "開院", 240, 300)
    stat_slam(466.7, 471.1, "20億円超", "負債", 240, 560, 150)
    stat_slam(469.25, 471.1, "2007", "閉院", 240, 820, 150)
    chip(471.8, 477.5, "巨大病棟が、そのまま", 1400, 240, 44)
    chip(478.2, 482.0, "2025年 テレビ取材", 1500, 940, 42, WHITE, RED)
    for txt, ts, te in (("割れた窓ガラス", 485.2, 486.9),
                        ("荒れた廊下", 487.1, 488.7),
                        ("残された病院設備", 488.95, 491.2)):
        slam(ts, te, txt, 960, 820, 74, WHITE, chroma=False, shake=False)
    quote(492.0, 497.9, "時間から、取り残された", 960, 260, 64)
    ev(2, 498.5, 503.1, "Serif",
       f"{{\\an5\\pos(960,150)\\fs64\\1c{RED}\\fsp10\\bord3.2\\fad(200,160)}}"
       "数多くの心霊現象")
    for hx, hy, ts in ((0.235, 0.74, 499.0), (0.62, 0.575, 499.6),
                       (0.44, 0.41, 500.2), (0.72, 0.245, 500.8)):
        ring(ts, int(1920 * hx), int(1080 * hy), 22, 120, 1.0)
        ring(ts + 0.5, int(1920 * hx), int(1080 * hy), 22, 90, 0.9)
    slam(503.6, 511.0, "霊安室", 1310, 280, 160, RED)
    chip(507.3, 511.0, "女性の幽霊が現れる", 1310, 450, 44)
    chip(511.7, 515.6, "遺体が安置された場所", 1400, 240, 44)
    chip(516.2, 519.0, "現在は、誰も使っていない", 1400, 240, 42)
    smalltag(519.6, 521.8, "しかし、その霊安室で――", 620, 300, 44, PALE)
    slam(522.2, 526.0, "女らしい姿", 960, 440, 104, PALE)
    slam(526.5, 530.0, "2階 手術室", 1290, 280, 120, WHITE)
    chip(529.5, 534.5, "男の低いうめき声", 1290, 450, 46, WHITE, RED)
    slam(535.1, 538.2, "血まみれの女性", 960, 330, 110, RED)
    ev(2, 538.7, 541.6, "Serif",
       f"{{\\an5\\pos(960,540)\\fs150\\1c&HE8E8F2&\\fsp30\\bord5\\3c{DRED}\\blur2"
       f"\\fscx104\\t(0,2600,\\fscx100\\fscy96)\\fad(60,200)}}助けて――")
    chip(542.3, 546.2, "深夜のハイヒールの音", 1360, 240, 44, WHITE, RED)
    for i in range(4):
        ring(542.7 + i * 0.85, 620 + i * 200, 830 - i * 60, 16, 90, 0.8,
             "&HAEB6C4&", 4)
    chip(546.9, 550.6, "鳴るはずのないナースコール", 1330, 240, 42, WHITE, RED)
    ring(547.3, 960, 555, 30, 190, 1.0)
    ring(548.4, 960, 555, 30, 190, 1.0)
    ring(549.5, 960, 555, 30, 190, 1.0)
    chip(551.3, 554.8, "病室から聞こえる声", 1380, 240, 44, WHITE, RED)
    slam(554.15, 556.7, "歩く人影", 1290, 420, 100, PALE)
    quote(557.4, 562.3, "場所ごとに、違う怪異", 960, 150, 60)
    for hx, hy in ((0.235, 0.74), (0.62, 0.575), (0.44, 0.41), (0.72, 0.245)):
        ring(557.8, int(1920 * hx), int(1080 * hy), 22, 100, 1.0)
        ring(559.2, int(1920 * hx), int(1080 * hy), 22, 100, 1.0)
        ring(560.6, int(1920 * hx), int(1080 * hy), 22, 100, 1.0)
    quote(563.1, 567.5, "怖いのは、今も残っていること", 960, 260, 62)
    # year ticker
    for i in range(20):
        y0, y1 = 568.0 + i * 0.26, 568.0 + (i + 1) * 0.26
        ev(2, y0, min(y1, 573.0) if i < 19 else 575.7, "Mono",
           f"{{\\an4\\pos(240,430)\\fs210\\1c{WHITE}\\bord7\\3c{INK}\\blur0.8}}"
           f"{2007 + i}")
    smalltag(568.0, 575.7, "閉院から――", 246, 300, 40, "&HAEB6C4&")
    ev(2, 573.4, 575.8, "Black",
       f"{{\\an4\\pos(250,560)\\fs54\\1c{RED}\\fsp6\\bord3\\fad(120,150)}}"
       "19年間、無人のまま")
    smalltag(576.4, 580.0, "それでも、夜になると――", 640, 280, 44, PALE)
    slam(581.05, 584.3, "大きな音", 960, 430, 130, RED)
    chip(585.1, 590.1, "※廃墟への無断立入は犯罪です", 1360, 980, 38, WHITE, YEL)
    chip(590.9, 594.0, "何列も並ぶ病棟の窓", 1400, 240, 44)
    slam(594.35, 597.5, "その奥は、真っ暗", 1230, 420, 88, PALE)
    for txt, ts, te, red in (("かつての病室", 597.9, 600.2, False),
                             ("かつての廊下", 600.5, 603.3, False),
                             ("かつての手術室", 603.7, 607.1, False),
                             ("そして――霊安室", 607.5, 611.0, True)):
        slam(ts, te, txt, 960, 250, 76, RED if red else PALE, chroma=red,
             shake=False)
    quote(611.5, 616.3, "そのすべてが、同じ建物の中に", 960, 180, 58)
    for hx, hy in ((0.235, 0.74), (0.62, 0.575), (0.44, 0.41), (0.72, 0.245)):
        ring(611.9, int(1920 * hx), int(1080 * hy), 24, 130, 1.4)
        ring(613.6, int(1920 * hx), int(1080 * hy), 24, 130, 1.4)
    ev(2, 617.0, 621.3, "Black",
       f"{{\\an5\\pos(960,220)\\fs54\\1c{PALE}\\fsp6\\bord3\\fad(300,200)}}"
       "ナースコールが鳴るのは、患者が看護師を呼ぶため")
    quote(622.8, 626.2, "しかし、もう患者はいない", 960, 340, 64, PALE)
    ev(2, 626.9, 631.3, "Serif",
       f"{{\\an5\\pos(960,300)\\fs110\\1c{RED}\\fsp16\\bord5\\blur1.6"
       f"\\t(0,4200,\\fscx103\\fscy103)\\fad(500,400)}}それでも、今も鳴る")
    ring(628.6, 960, 560, 34, 260, 1.6, RED, 6)

    # ---- OUTRO recap
    ev(2, 631.95, 641.4, "Black",
       f"{{\\an5\\pos(960,105)\\fs56\\1c{WHITE}\\fsp10\\bord3\\fad(200,200)}}"
       "現存する廃病院 ── 心霊スポット TOP5")
    recap = [(5, "黒瀬病院", "広島県東広島市"), (4, "旧相武病院", "東京都八王子市"),
             (3, "旧野木病院", "栃木県野木町"), (2, "小美玉小川脳病院", "茨城県小美玉市"),
             (1, "姫川病院", "新潟県糸魚川市")]
    for i, (r, nm, lc) in enumerate(recap):
        ts = 632.5 + i * 0.85
        y = 205 + i * 162
        ev(2, ts, 641.4, "Black",
           f"{{\\an4\\move(340,{y},400,{y},0,200)\\fs44\\1c{RED}\\bord2.6"
           f"\\fad(130,200)}}{r}")
        ev(2, ts + 0.08, 641.4, "Serif",
           f"{{\\an4\\move(420,{y},480,{y},0,200)\\fs58\\1c{WHITE}\\bord3"
           f"\\fad(130,200)}}{nm}")
        ev(2, ts + 0.16, 641.4, "Mono",
           f"{{\\an4\\pos(1150,{y + 6})\\fs36\\1c{CYAN}\\fsp4\\bord2.4"
           f"\\fad(160,200)}}{lc}")
    quote(654.2, 658.0, "人がいなくなり、電気が消えた後", 960, 250, 54)
    ev(2, 674.6, 676.4, "Serif",
       f"{{\\an5\\pos(960,540)\\fs120\\1c{RED}\\fsp20\\bord6\\blur2\\fad(400,300)}}終")


HEADER = """[Script Info]
Title: 廃病院 心霊スポット TOP5
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{sans},58,&H00F5F5F7,&H000000FF,&H00080808,&HA0000000,-1,0,0,0,100,100,1.5,0,1,2.7,1.6,2,90,90,52,1
Style: Serif,{serif},80,&H00F0F0F2,&H000000FF,&H000A0A0C,&H96000000,0,0,0,0,100,100,0,0,1,3,2,5,60,60,60,1
Style: Black,{black},72,&H00F0F0F2,&H000000FF,&H000A0A0C,&H96000000,0,0,0,0,100,100,0,0,1,3,2,5,60,60,60,1
Style: Mono,{mono},40,&H00E8ECF0,&H000000FF,&H00080808,&H96000000,-1,0,0,0,100,100,1,0,1,2.2,1.2,5,60,60,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(sans=F_SANS, serif=F_SERIF, black=F_BLACK, mono=F_MONO)


def main():
    ensure_dirs()
    narration()
    rank_cards()
    section_headers()
    cues()
    EVENTS.sort(key=lambda e: (e[1], e[0]))
    lines = [HEADER]
    for layer, t0, t1, style, name, text in EVENTS:
        lines.append(f"Dialogue: {layer},{tf(t0)},{tf(t1)},{style},{name},0,0,0,,{text}\n")
    out = os.path.join(BUILD, "main.ass")
    with open(out, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"{out}: {len(EVENTS)} events")


if __name__ == "__main__":
    main()
