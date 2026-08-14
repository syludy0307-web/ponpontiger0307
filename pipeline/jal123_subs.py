# -*- coding: utf-8 -*-
"""Subtitles + kinetic data typography for the JAL123 documentary.

Two jobs:
  1. Repair the auto-transcribed SRT.  The raw file contains homophone errors
     that would be seriously misleading burned into a factual documentary
     (e.g. 圧力核兵器 for 圧力隔壁).  FIXES holds only corrections forced by
     context and aviation fact; NEUTRALISED holds garbled spans that cannot be
     resolved from the audio, rewritten to phrasing that asserts nothing the
     narration may not have said.
  2. Lay out the data typography: figures, timelines, comparison panels.

Style: investigative/technical.  No chromatic-aberration slams, no glitch.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, parse_srt, ensure_dirs

# ASS colours are &HBBGGRR&
WHITE = "&HF2F2F4&"
PALE = "&HE0DCD2&"
CYAN = "&HECD696&"      # 96d6ec
AMB = "&H4AB0E8&"       # e8b04a
RED = "&H4842D8&"       # d84248
STEEL = "&H9E8A78&"
INK = "&H120E0A&"

F_SANS = "Noto Sans CJK JP"
F_BLACK = "Noto Sans CJK JP Black"
F_SERIF = "Noto Serif CJK JP Black"
F_MONO = "Noto Sans Mono CJK JP"

EVENTS = []

# ---------------------------------------------------------------- SRT repair
# Unambiguous: homophone/OCR errors whose correct form is fixed by aviation
# fact or by the script's own vocabulary elsewhere in the same narration.
FIXES = [
    ("圧力核兵器", "圧力隔壁"),
    ("圧力\n隔壁", "圧力隔壁"),
    ("基調たち", "機長たち"),
    ("高浜正樹機長たち", "高浜機長たち"),   # 実際の機長名と食い違うため名を落とす
    ("操縦艦", "操縦桿"),
    ("プラップ", "フラップ"),
    ("自己調査委員会", "事故調査委員会"),
    ("自己調査報告書", "事故調査報告書"),
    ("自己報告書", "事故報告書"),
    ("自己記", "事故機"),
    ("単独旗", "単独機"),
    ("雄高の尾根", "御巣鷹の尾根"),
    ("帰ろう亀裂", "疲労亀裂"),
    ("異常外国", "異常外力"),
    ("終助", "救助"),
    ("接対と安否", "撃墜と隠蔽"),
    ("精椎の証拠", "撃墜の証拠"),
    ("接対", "撃墜"),
    ("四高等の油圧配管", "四系統の油圧配管"),
    ("液体の傾き", "機体の傾き"),
    ("猛烈な効\n果", "猛烈な降下"),
    ("猛烈な効果", "猛烈な降下"),
    ("一度はコードを約", "一度は高度を約"),
    ("安全韓国", "安全勧告"),
    ("物晶", "物証"),
    ("うがわしく", "疑わしく"),
    ("うがいたく", "疑いたく"),
    ("こじられた", "報じられた"),
    ("情報が削減した", "情報が錯綜した"),
    ("情報の困難", "情報の混乱"),
    ("十章で確認", "物証で確認"),
    ("死者が二千二十四年に掲載", "自社が2024年に掲載"),
    ("足を下ろし", "脚を下ろし"),
    ("人も目で追って", "人の目で追って"),
    ("記録媒体には\n刻みがあり", "記録媒体には傷みがあり"),
    ("刻みがあり", "傷みがあり"),
    ("曹操だけを根拠", "焼損だけを根拠"),
    ("激しく焼け出したい", "激しい焼損"),
    ("ミサ イル", "ミサイル"),
    ("ミサイ ル説", "ミサイル説"),
    ("事故までに期待は", "事故までに機体は"),
    ("少しでも期待を安定", "少しでも機体を安定"),
    ("期待には、まず", "機体には、まず"),
    ("巨大な七百四十七", "巨大なボーイング747"),
    ("f四戦闘機", "F-4戦闘機"),
    ("国家運輸安全\n委員会", "国家運輸安全委員会"),
    ("種子の\n元、米軍関係者", "という趣旨の、元米軍関係者"),
    ("種子の元、米軍関係者", "という趣旨の、元米軍関係者"),
    ("五百二十人 という", "520人という"),
]

# Garbled spans that cannot be recovered from the audio with confidence.
# Rewritten to neutral phrasing that cannot assert something false.
NEUTRALISED = [
    ("性追跡が", "撃墜説が"),                       # 文脈上ほぼ確実だが語形は不明
    ("事故機のオブに見えたとされる", "事故機の近くに見えたとされる"),
    ("精椎兵器の残骸", "兵器の残骸"),               # 「特殊兵器」等かは判別不能
    ("うがいたくなるのも", "疑いたくなるのも"),
]

NUMBERS = [
    ("千九百八十五年", "1985年"), ("千九百八十七年", "1987年"),
    ("千九百七十八年", "1978年"), ("千九百九十年代", "1990年代"),
    ("二千二十六年", "2026年"), ("二千二十五年", "2025年"),
    ("二千二十四年", "2024年"), ("二千七年", "2007年"),
    ("八月十二日", "8月12日"), ("2026年八月", "2026年8月"),
    ("十八時十二分", "18時12分"), ("十八時五十六分", "18時56分"),
    ("十九時二十一分", "19時21分"),
    ("五百二十四人", "524人"), ("五百二十人", "520人"),
    ("約二万四千フィート", "約24,000ft"), ("約二万二千フィート", "約22,000ft"),
    ("約一万八千八百回", "約18,800回"), ("約一万フィート", "約10,000ft"),
    ("約一万八千フィート", "約18,000ft"),
    ("三百\n四十ノット", "340ノット"), ("約三百", "約340"), ("四十ノットだったとされる", "ノットだったとされる"),
    ("二十億円", "20億円"), ("七十パーセント", "70%"),
    ("約十二分後", "約12分後"), ("約三十分", "約30分"), ("二十分ほど", "20分ほど"),
    ("四十一年後", "41年後"), ("四十年", "40年"), ("七年以上", "7年以上"),
    ("七年前", "7年前"), ("四系統", "4系統"), ("四人", "4人"),
]


def repair(text):
    for a, b in FIXES + NEUTRALISED + NUMBERS:
        text = text.replace(a, b)
    return re.sub(r"\s{2,}", " ", text).strip()


EMPH = ["圧力隔壁", "垂直尾翼", "疲労亀裂", "油圧", "接合板", "リベット",
        "不適切な修理", "撃墜", "ミサイル", "陰謀論", "物証", "異常外力",
        "フライトレコーダー", "520人", "524人", "生存者", "御巣鷹の尾根",
        "制御不能", "70%", "18,800回", "救助", "事故調査報告書", "隠蔽"]


def tf(t):
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def ev(layer, t0, t1, style, text):
    EVENTS.append((layer, t0, t1, style, text))


def narration():
    for s in parse_srt():
        txt = repair(s["text"])
        for w in EMPH:
            if w in txt:
                txt = txt.replace(w, f"{{\\1c{AMB}\\b1}}{w}{{\\1c{WHITE}\\b0}}", 1)
                break
        ev(5, s["start"], s["end"], "Sub", f"{{\\fad(100,80)}}{txt}")


# ---------------------------------------------------------------- primitives
def rule(t0, t1, x, y, w, col=AMB, h=5, dur=280, layer=1):
    ev(layer, t0, t1, "Black",
       f"{{\\an7\\pos({x},{y})\\1c{col}\\bord0\\shad0\\p1"
       f"\\clip({x},{y - 4},{x},{y + h + 4})"
       f"\\t(0,{dur},\\clip({x},{y - 4},{x + w},{y + h + 4}))\\fad(0,120)}}"
       f"m 0 0 l {w} 0 l {w} {h} l 0 {h}{{\\p0}}")


def panel(t0, t1, x, y, w, h, fill=INK, alpha="&H50&", accent=AMB, dur=240):
    ev(0, t0, t1, "Black",
       f"{{\\an7\\pos({x},{y})\\1c{fill}\\alpha{alpha}\\bord0\\shad0\\p1"
       f"\\clip({x},{y},{x + w},{y})\\t(0,{dur},\\clip({x},{y},{x + w},{y + h}))"
       f"\\fad(0,150)}}m 0 0 l {w} 0 l {w} {h} l 0 {h}{{\\p0}}")
    if accent:
        ev(1, t0, t1, "Black",
           f"{{\\an7\\pos({x},{y})\\1c{accent}\\bord0\\shad0\\p1\\fad(80,150)}}"
           f"m 0 0 l 9 0 l 9 {h} l 0 {h}{{\\p0}}")


def datum(t0, t1, value, label, x, y, vsize=150, col=AMB, unit="", an=4):
    """Big number with a small label under it, wiped in."""
    ev(2, t0, t1, "Mono",
       f"{{\\an{an}\\pos({x},{y})\\fs{vsize}\\1c{col}\\bord5\\3c{INK}\\blur0.6"
       f"\\fscx118\\fscy118\\t(0,180,0.5,\\fscx100\\fscy100)\\fad(60,150)}}{value}"
       + (f"{{\\fs{int(vsize * 0.44)}\\1c{PALE}}} {unit}" if unit else ""))
    if label:
        ev(2, t0 + 0.12, t1, "Black",
           f"{{\\an{an}\\pos({x + (4 if an == 4 else 0)},{y + vsize * 0.56})\\fs42"
           f"\\1c{PALE}\\fsp8\\bord2.4\\fad(120,150)}}{label}")
    rule(t0 + 0.05, t1, x - (0 if an == 4 else 200), int(y + vsize * 0.86),
         400 if an == 4 else 400, STEEL, 4)


def tag(t0, t1, text, x, y, size=40, col=CYAN, an=7):
    ev(2, t0, t1, "Mono",
       f"{{\\an{an}\\pos({x},{y})\\fs{size}\\1c{col}\\bord2.4\\3c{INK}\\fsp3"
       f"\\fad(140,140)}}{text}")


def label_box(t0, t1, text, x, y, size=46, col=WHITE, accent=AMB, pad=28):
    w = int(size * len(text) * 1.04) + pad * 2
    h = size + 34
    panel(t0, t1, x - w // 2, y - h // 2, w, h, accent=accent)
    ev(2, t0 + 0.06, t1, "Black",
       f"{{\\an5\\pos({x + 5},{y})\\fs{size}\\1c{col}\\bord2.6\\3c{INK}\\fsp2"
       f"\\fad(120,140)}}{text}")


def headline(t0, t1, text, x, y, size=96, col=WHITE, serif=True, fsp=6):
    st = "Serif" if serif else "Black"
    ev(2, t0, t1, st,
       f"{{\\an5\\move({x},{y + 12},{x},{y},0,260)\\fs{size}\\1c{col}\\fsp{fsp}"
       f"\\bord4\\3c{INK}\\blur0.8\\fad(160,180)}}{text}")


def note(t0, t1, text, x, y, size=44, col=PALE):
    ev(2, t0, t1, "Serif",
       f"{{\\an5\\pos({x},{y})\\fs{size}\\1c{col}\\fsp10\\bord3\\3c{INK}"
       f"\\fad(300,220)}}{text}")


def listrow(t0, t1, text, x, y, i, size=46, col=WHITE, accent=AMB):
    ev(1, t0, t1, "Black",
       f"{{\\an7\\pos({x - 34},{y - 26})\\1c{accent}\\bord0\\shad0\\p1\\fad(90,140)}}"
       f"m 0 0 l 8 0 l 8 52 l 0 52{{\\p0}}")
    ev(2, t0 + 0.05, t1, "Black",
       f"{{\\an4\\move({x + 16},{y},{x},{y},0,220)\\fs{size}\\1c{col}\\bord2.6"
       f"\\3c{INK}\\fad(120,140)}}{text}")


def clock(t0, t1, text, x=1782, y=76):
    ev(4, t0, t1, "Mono",
       f"{{\\an9\\pos({x},{y})\\fs44\\1c{AMB}\\bord2.6\\3c{INK}\\fsp4"
       f"\\fad(200,200)}}{text}")


def chapter(t0, t1, text):
    ev(4, t0, t1, "Mono",
       f"{{\\an7\\pos(64,52)\\fs32\\1c{CYAN}\\alpha&H30&\\bord2\\3c{INK}\\fsp2"
       f"\\fad(260,260)}}▍{text}")


def counter(t0, t1, x, y, v0, v1, steps, size=170, col=AMB, fmt="{:,}"):
    """Rolling numeric counter."""
    dt = (t1 - t0) / steps
    for i in range(steps):
        v = int(v0 + (v1 - v0) * ((i + 1) / steps))
        a, b = t0 + i * dt, t0 + (i + 1) * dt
        ev(2, a, b if i < steps - 1 else t1, "Mono",
           f"{{\\an4\\pos({x},{y})\\fs{size}\\1c{col}\\bord5\\3c{INK}\\blur0.5}}"
           f"{fmt.format(v)}")


# ---------------------------------------------------------------- cue script
def cues():
    # ===== 1. 発生 =====
    ev(2, 0.35, 4.30, "Mono",
       f"{{\\an5\\pos(960,470)\\fs150\\1c{WHITE}\\fsp18\\bord5\\3c{INK}"
       f"\\fscx112\\t(0,3600,\\fscx100)\\fad(500,240)}}1985.08.12")
    rule(1.60, 4.30, 620, 560, 680, RED, 6)
    note(1.95, 4.30, "日本航空123便", 960, 640, 56)
    chapter(4.6, 48.3, "1985.08.12  JAL123  HND → ITM")
    clock(4.6, 15.1, "18:12")
    label_box(6.6, 9.2, "羽田空港 18時12分 離陸", 1330, 220, 44)
    label_box(9.5, 13.6, "目的地: 大阪(伊丹)", 1360, 220, 44, accent=CYAN)
    datum(15.4, 19.0, "524", "乗客乗員", 200, 300, 190)
    note(19.4, 23.9, "その中には、歌手の坂本九さんもいた", 960, 900, 50)
    clock(24.1, 30.5, "18:24")
    datum(24.3, 30.5, "24,000", "巡航高度", 190, 280, 140, unit="ft")
    label_box(26.6, 30.5, "離陸から約12分後", 1400, 240, 46, accent=CYAN)
    headline(30.9, 34.4, "突然の異常音", 960, 300, 110, RED)
    label_box(34.8, 37.3, "客室の酸素マスクが落下", 1290, 230, 46, accent=RED)
    headline(37.8, 42.1, "垂直尾翼 大部分を喪失", 960, 250, 88, RED, serif=False)
    for i, (t, txt) in enumerate([(42.6, "油圧 #1"), (43.4, "油圧 #2"),
                                  (44.2, "油圧 #3"), (45.0, "油圧 #4")]):
        listrow(t, 48.3, txt, 250, 300 + i * 96, i, 48, WHITE, RED)
    headline(45.8, 48.3, "4系統すべて喪失", 1330, 470, 76, RED, serif=False)

    # ===== 2. 32分間 =====
    chapter(48.6, 152.0, "CONTROL LOST  ── 32 MINUTES")
    label_box(48.9, 53.9, "緊急事態を宣言", 1330, 220, 48, accent=RED)
    headline(55.0, 60.0, "操縦桿が効かない", 960, 250, 92, RED)
    label_box(60.6, 65.0, "ダッチロール", 1420, 210, 50, accent=AMB)
    tag(61.0, 65.0, "左右に振れる蛇行運動", 1420, 280, 36, CYAN, an=8)
    label_box(65.6, 70.2, "フゴイド運動", 1420, 210, 50, accent=AMB)
    tag(66.0, 70.2, "長周期の高度上下", 1420, 280, 36, CYAN, an=8)
    headline(71.0, 75.4, "舵は、ほとんど使えない", 960, 880, 68, PALE)
    label_box(76.4, 83.5, "左右エンジンの推力差で操縦", 1180, 200, 46, accent=AMB)
    listrow(78.5, 88.8, "脚を下ろす", 250, 720, 0, 48)
    listrow(80.6, 88.8, "フラップを使う", 250, 810, 1, 48)
    listrow(82.0, 88.8, "推力を調整する", 250, 900, 2, 48)
    headline(84.5, 88.8, "機体を安定させようとした", 1230, 320, 62, WHITE, serif=False)
    datum(89.6, 97.0, "32", "分間、空中に留めた", 620, 430, 260, unit="min", an=5)
    clock(97.2, 138.0, "18:40")
    datum(98.4, 107.0, "22,000", "を約20分保持", 190, 300, 130, unit="ft")
    label_box(107.6, 117.0, "山が迫る ── 出力を上げ 10,000ftへ", 1060, 210, 44,
              accent=CYAN)
    label_box(117.6, 122.0, "フラップ操作 → 傾きが増大", 1230, 210, 44, accent=RED)
    datum(122.4, 132.0, "18,000", "毎分の降下率", 1180, 420, 130, RED, unit="ft/min")
    datum(132.4, 138.3, "340", "衝突時の速度", 1180, 700, 120, RED, unit="kt")
    clock(138.6, 152.0, "18:56")
    headline(139.4, 145.0, "18時56分ごろ", 960, 250, 86, WHITE)
    headline(145.6, 152.0, "群馬県 御巣鷹の尾根", 960, 250, 92, RED)

    # ===== 3. 犠牲 =====
    chapter(152.4, 166.1, "CASUALTIES")
    datum(152.6, 158.4, "520", "人が亡くなった", 180, 300, 200, RED)
    datum(158.8, 163.0, "4", "人が生存", 180, 300, 200, CYAN)
    headline(163.4, 166.1, "単独機の事故として 世界最悪級", 960, 880, 62, PALE,
             serif=False)

    # ===== 4. 原因 =====
    chapter(166.5, 279.4, "CAUSE  ── OFFICIAL INVESTIGATION")
    headline(166.6, 170.7, "では、なぜ墜落したのか", 960, 430, 104, AMB)
    label_box(171.4, 179.7, "1987年 事故調査報告書", 1360, 200, 46)
    headline(174.2, 179.7, "原因は7年前に遡る", 960, 900, 66, WHITE, serif=False)
    label_box(180.4, 188.2, "1978年 大阪国際空港", 1330, 200, 46, accent=RED)
    headline(183.0, 188.2, "しりもち事故", 1330, 330, 80, RED, serif=False)
    tag(185.2, 188.2, "機体後部の圧力隔壁が損傷", 1330, 420, 38, CYAN, an=8)
    label_box(189.0, 194.4, "後部圧力隔壁とは", 1340, 200, 48, accent=CYAN)
    note(195.2, 202.2, "与圧された客室と、機体後部を隔てる巨大な壁", 960, 880, 48)
    label_box(203.0, 211.8, "毎フライト 加圧と減圧を受ける", 1200, 200, 44, accent=AMB)
    label_box(212.4, 217.1, "修理を担当 ── 機体メーカー", 1240, 200, 44, accent=CYAN)
    headline(214.4, 217.1, "ボーイング", 1240, 320, 76, WHITE, serif=False)
    label_box(217.8, 224.0, "本来 ── 接合板は1枚", 1300, 190, 48, accent=CYAN)
    tag(220.0, 224.0, "リベット2列で荷重を分担", 1300, 270, 38, CYAN, an=8)
    label_box(225.0, 232.7, "実際 ── 接合板を2枚に分割", 1240, 190, 48, accent=RED)
    tag(228.0, 232.7, "実質1列だけで荷重を受ける状態に", 1240, 270, 38, RED, an=8)
    headline(233.4, 238.7, "この差が、7年後に効いてくる", 960, 900, 60, PALE,
             serif=False)
    datum(239.6, 246.9, "70", "本来の強度に対して", 200, 320, 210, RED, unit="%")

    # ===== 5. 7年 =====
    counter(247.6, 253.8, 300, 380, 0, 18800, 26, 180, AMB)
    ev(2, 247.6, 253.9, "Black",
       f"{{\\an4\\pos(304,486)\\fs42\\1c{PALE}\\fsp8\\bord2.4\\fad(120,150)}}"
       "回の離着陸")
    label_box(254.6, 261.5, "飛ぶたび加圧、降りれば減圧", 1220, 200, 44, accent=AMB)
    headline(262.2, 269.1, "小さな疲労亀裂が、少しずつ育つ", 960, 250, 72, RED,
             serif=False)
    label_box(270.0, 279.3, "接合板とシール材に隠れて見えない", 1160, 200, 42,
              accent=CYAN)
    headline(274.4, 279.3, "目視点検では発見が難しい", 960, 900, 62, PALE, serif=False)

    # ===== 6. 破壊 =====
    chapter(279.6, 350.0, "THE FAILURE  ── 1985.08.12")
    headline(280.0, 288.2, "そして 1985年8月12日", 960, 260, 84, WHITE)
    headline(288.8, 297.2, "圧力隔壁が破壊された", 960, 250, 96, RED, serif=False)
    label_box(298.2, 307.2, "高圧の空気が機体後部へ一気に流出", 1140, 200, 42,
              accent=RED)
    listrow(300.4, 313.0, "垂直尾翼の大部分", 250, 700, 0, 46, WHITE, RED)
    listrow(302.4, 313.0, "補助動力装置(APU)", 250, 790, 1, 46, WHITE, RED)
    listrow(307.8, 313.0, "4系統の油圧配管", 250, 880, 2, 46, WHITE, RED)
    label_box(313.6, 322.0, "現在も公式に認定されている流れ", 1180, 200, 44)
    label_box(322.6, 330.6, "回収された圧力隔壁", 1330, 200, 46, accent=CYAN)
    headline(325.4, 330.6, "破断面に残る疲労亀裂", 1330, 330, 66, AMB, serif=False)
    label_box(331.4, 340.0, "米国 国家運輸安全委員会(NTSB)", 1180, 200, 42,
              accent=CYAN)
    headline(334.6, 340.0, "同種事故を防ぐ安全勧告", 1180, 320, 58, WHITE, serif=False)
    headline(341.0, 350.0, "不適切な修理は、強い物証で裏付けられている", 960, 890, 58,
             PALE, serif=False)

    # ===== 7. 陰謀論 =====
    chapter(350.4, 511.0, "THE OTHER STORY  ── 陰謀論")
    headline(350.6, 358.2, "40年経っても消えない、別の物語", 960, 420, 88, RED)
    for t0_, t1_, txt in ((358.6, 366.0, "自衛隊のミサイルが命中したのでは?"),
                          (366.4, 371.3, "訓練用の標的機が衝突したのでは?"),
                          (371.7, 377.9, "F-4戦闘機が追尾していたのでは?"),
                          (378.3, 385.2, "救助の遅れは証拠隠しでは?")):
        ev(2, t0_, t1_, "Black",
           f"{{\\an5\\pos(1020,540)\\fs62\\1c{WHITE}\\bord3\\3c{INK}\\fsp2"
           f"\\fad(160,160)}}{txt}")
    label_box(385.8, 394.8, "事故直後、情報は大きく混乱した", 1180, 200, 44,
              accent=CYAN)
    label_box(395.4, 404.6, "墜落地点 ── 長野県側か、群馬県側か", 1120, 200, 42,
              accent=CYAN)
    clock(405.0, 424.0, "19:21")
    label_box(405.4, 415.6, "自衛隊機が山中の火災を確認", 1240, 200, 44, accent=AMB)
    label_box(416.2, 424.2, "暗闇の山岳地帯 ── 着陸できず", 1200, 200, 44, accent=RED)
    headline(425.0, 434.3, "本格的な救助は、翌朝になった", 960, 250, 78, RED,
             serif=False)
    headline(435.0, 447.0, "墜落直後、まだ生きていた人が複数いた", 960, 250, 68,
             WHITE, serif=False)
    note(448.0, 458.0, "この事実は重い", 960, 300, 76)
    note(451.0, 458.0, "もっと早く到達できていれば ──", 960, 880, 52)
    label_box(458.6, 470.0, "1990年代 ── 元米軍関係者の証言", 1180, 200, 44,
              accent=CYAN)
    headline(462.6, 470.0, "「救助の準備をしたが、不要と伝えられた」", 1180, 330, 50,
             PALE, serif=False)
    headline(470.6, 480.0, "何かを隠したのでは ── と疑いたくなる", 960, 250, 68,
             RED, serif=False)

    # ===== 8. 断片 =====
    label_box(480.6, 490.0, "オレンジ色の物体", 1320, 200, 48, accent=AMB)
    tag(483.0, 490.0, "写真・目撃情報のみ", 1320, 280, 38, CYAN, an=8)
    label_box(490.6, 496.2, "報告書の付録にある「異常外力」", 1180, 200, 44,
              accent=AMB)
    label_box(496.8, 502.3, "現場の激しい焼損", 1330, 200, 46, accent=RED)
    label_box(502.9, 511.0, "救助開始までの空白", 1330, 200, 46, accent=RED)
    headline(506.0, 511.0, "断片は、そろっている", 960, 900, 62, PALE, serif=False)

    # ===== 9. 検証 =====
    chapter(511.4, 827.0, "EXAMINING THE EVIDENCE")
    headline(511.6, 522.0, "疑わしく見える事実と、証明する証拠は別だ", 960, 420, 74,
             AMB)
    headline(522.6, 530.1, "まず、ミサイル説", 960, 250, 92, WHITE, serif=False)
    label_box(530.8, 542.1, "最大の問題 ── 機体後部から疲労亀裂", 1140, 200, 42,
              accent=CYAN)
    headline(534.6, 542.1, "亀裂は1978年の修理部分から進展していた", 1140, 330, 48,
             AMB, serif=False)
    headline(543.0, 550.8, "これは推測ではない", 960, 250, 84, WHITE, serif=False)
    label_box(546.0, 550.8, "破断面の調査で確認された", 1230, 330, 44, accent=CYAN)
    label_box(551.4, 560.0, "2026年 ── フライトレコーダー再解析の報道", 1080, 200, 42,
              accent=AMB)
    label_box(562.0, 570.9, "記録媒体には傷みがあった", 1240, 200, 44, accent=RED)
    label_box(571.6, 585.0, "一部の重要データが正常に読めない", 1160, 200, 42,
              accent=RED)
    label_box(585.6, 598.4, "記録を拡大し、ビットを人の目で追う", 1140, 200, 42,
              accent=CYAN)
    headline(590.0, 598.4, "地道な復元作業", 1140, 330, 68, WHITE, serif=False)
    headline(599.0, 609.7, "そのデータが示したもの", 960, 250, 84, AMB, serif=False)
    listrow(610.4, 625.4, "① まず 前方へ押される加速度", 250, 720, 0, 48, WHITE, AMB)
    listrow(616.0, 625.4, "② 続いて 下向きの加速度", 250, 812, 1, 48, WHITE, AMB)
    label_box(626.0, 636.9, "隔壁が壊れ、空気が後方へ噴出", 1200, 200, 44, accent=CYAN)
    headline(630.0, 636.9, "その反作用で機体は前方へ", 1200, 330, 58, AMB, serif=False)
    headline(637.4, 644.5, "公式の流れと整合する", 960, 250, 86, AMB, serif=False)
    headline(645.2, 654.0, "もし外部からの命中が原因なら", 960, 250, 68, WHITE,
             serif=False)
    headline(654.6, 659.2, "同じ動きを説明する別の物理的根拠が要る", 960, 890, 56,
             PALE, serif=False)
    headline(659.8, 669.1, "現在まで、それを上回る実証は示されていない", 960, 250, 62,
             RED, serif=False)
    label_box(669.8, 682.5, "写真だけでは、標的機ともミサイルとも特定できない", 1060,
              200, 40, accent=CYAN)
    label_box(683.2, 692.7, "「異常外力」── 付録にある言葉自体は事実", 1100, 200, 42,
              accent=AMB)
    headline(687.0, 692.7, "ただし、何が生んだ力かまでは特定できない", 1100, 330, 48,
             PALE, serif=False)
    label_box(693.4, 702.7, "2025年 国会 ── 防衛大臣が明確に否定", 1120, 200, 42,
              accent=CYAN)
    headline(703.4, 714.3, "政府が否定したから真実、という話ではない", 960, 250, 62,
             PALE, serif=False)
    headline(714.9, 722.0, "重要なのは、物的証拠の向きだ", 960, 250, 78, AMB,
             serif=False)
    for i, (t, txt) in enumerate([(715.4, "圧力隔壁の疲労破壊"), (717.0, "誤った修理"),
                                  (719.0, "垂直尾翼の破壊"), (721.0, "4系統の油圧喪失"),
                                  (724.4, "FDRの挙動")]):
        listrow(t, 742.0, txt, 230, 380 + i * 92, i, 44, WHITE, CYAN)
    headline(729.6, 742.0, "すべてが同じ方向を向いている", 1500, 540, 56, AMB,
             serif=False)

    # ===== 11. 救助 =====
    headline(742.6, 754.3, "では、救助の遅れは?", 960, 250, 92, WHITE, serif=False)
    for i, (t, txt) in enumerate([(744.4, "位置情報の混乱"), (747.0, "夜間の山岳救助の困難"),
                                  (750.4, "組織間の連絡"), (752.8, "米軍支援をめぐる証言")]):
        listrow(t, 767.2, txt, 300, 320 + i * 162, i, 50, WHITE, AMB)
    headline(757.0, 767.2, "疑問が残る部分は、確かにある", 960, 900, 62, AMB,
             serif=False)
    headline(768.0, 781.0, "「遅れた」と「意図的に遅らせた」の間には", 960, 200, 60,
             PALE, serif=False)
    headline(776.0, 781.0, "大きな距離がある", 960, 890, 78, RED, serif=False)
    label_box(782.0, 805.8, "命令記録・兵器の残骸 ── 決定的な証拠は未確認", 1010, 200,
              40, accent=RED)
    label_box(806.6, 827.0, "大量の航空燃料を積んだ機体が高速で衝突", 1080, 200, 40,
              accent=AMB)
    headline(814.0, 827.0, "焼損だけを根拠に、特殊な兵器へは結びつけられない", 960, 890,
             54, PALE, serif=False)

    # ===== 12. 結論 =====
    chapter(827.4, 890.0, "CONCLUSION")
    headline(827.6, 838.5, "現時点で最も合理的な結論", 960, 430, 100, AMB)
    headline(839.2, 848.0, "撃墜されたのではない", 960, 250, 88, WHITE, serif=False)
    for i, (t, txt) in enumerate([(841.0, "1978年 不適切な修理"),
                                  (844.0, "圧力隔壁の疲労破壊"),
                                  (848.6, "垂直尾翼と油圧系統の喪失"),
                                  (852.0, "制御不能 → 墜落")]):
        listrow(t, 858.6, txt, 240, 620 + i * 88, i, 44, WHITE, RED)
    headline(853.4, 858.6, "この可能性が圧倒的に高い", 1420, 300, 58, AMB, serif=False)
    headline(859.4, 872.0, "陰謀論が生まれた土壌", 960, 200, 76, WHITE, serif=False)
    for i, (t, txt) in enumerate([(860.0, "情報の混乱"), (862.6, "救助の遅れ"),
                                  (865.0, "説明不足"), (867.0, "520人という犠牲")]):
        listrow(t, 882.9, txt, 250, 500 + i * 92, i, 46, WHITE, STEEL)
    headline(874.0, 882.9, "不信感が、一つの巨大な物語につながった", 1360, 560, 50,
             PALE, serif=False)

    # ===== 13. 残された謎 =====
    chapter(890.4, 1018.0, "THE UNANSWERED QUESTION")
    headline(890.6, 899.3, "まだ一つだけ、妙な穴が残る", 960, 430, 96, RED)
    headline(900.0, 908.6, "なぜ作業員は接合板を2枚にしたのか", 960, 250, 74, AMB,
             serif=False)
    label_box(909.2, 919.7, "事故調査当時 ── 作業者からの聞き取りは不十分", 1060, 200,
              40, accent=RED)
    label_box(920.4, 930.7, "2024年 ボーイングの安全教育用資料", 1140, 200, 42,
              accent=CYAN)
    headline(924.6, 930.7, "「構造上、そのまま設置が難しかったため切り分けた」", 1140,
             330, 44, PALE, serif=False)
    clock(931.4, 956.6, "2026.08")
    headline(931.6, 943.0, "2026年8月 ── その説明を削除", 960, 250, 78, RED,
             serif=False)
    label_box(944.0, 956.6, "日本航空に混乱を招いたとして謝罪", 1180, 200, 44,
              accent=RED)
    label_box(957.2, 966.6, "過去には「指示の読み違い」という説明も", 1100, 200, 42,
              accent=CYAN)
    label_box(967.2, 981.2, "FAA安全資料には、現在も同趣旨の記述が残る", 1060, 200, 40,
              accent=AMB)
    label_box(981.8, 995.0, "一方でボーイングは、同じ説明を削除", 1140, 200, 42,
              accent=RED)
    headline(988.0, 995.0, "ここが奇妙だ", 1140, 330, 78, RED, serif=False)
    headline(995.6, 1006.2, "修理ミス自体は、物証で確認されている", 960, 200, 62,
             WHITE, serif=False)
    headline(1000.6, 1006.2, "しかし「なぜその作業を選んだか」は──", 960, 890, 56,
             AMB, serif=False)
    datum(1007.0, 1018.3, "41", "年後の今も、説明の出所が揺れている", 200, 300, 200,
          RED, unit="年")

    # ===== 14. 結び =====
    chapter(1018.6, 1072.0, "JAL123  ── THE LAST PAGE")
    headline(1019.0, 1032.0, "制御不能に至る物理は、かなり解明されている", 960, 250,
             62, WHITE, serif=False)
    headline(1032.6, 1046.0, "だが、最初の引き金となった人間側の理由は", 960, 200, 62,
             AMB, serif=False)
    headline(1039.0, 1046.0, "40年経った今も、確定していない", 960, 890, 66, RED,
             serif=False)
    headline(1046.6, 1054.0, "撃墜説を裏付ける決定的な証拠はない", 960, 250, 66,
             PALE, serif=False)
    headline(1054.6, 1060.0, "それでも、もし記録が残っているとしたら", 960, 250, 62,
             WHITE, serif=False)
    ev(2, 1060.6, 1069.4, "Serif",
       f"{{\\an5\\pos(960,470)\\fs104\\1c{WHITE}\\fsp14\\bord5\\3c{INK}\\blur1"
       f"\\t(0,8000,\\fscx103\\fscy103)\\fad(600,400)}}"
       "私たちがまだ知らない\\N最後の一ページ")
    ev(2, 1069.8, 1072.0, "Serif",
       f"{{\\an5\\pos(960,540)\\fs64\\1c{STEEL}\\fsp16\\bord3\\3c{INK}"
       f"\\fad(400,600)}}日本航空123便")


HEADER = """[Script Info]
Title: JAL123 ── 事故と、残された疑問
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{sans},56,&H00F4F4F6,&H000000FF,&H000A0A0C,&HA0000000,-1,0,0,0,100,100,1.2,0,1,2.6,1.5,2,100,100,54,1
Style: Serif,{serif},80,&H00F2F2F4,&H000000FF,&H000A0A0C,&H96000000,0,0,0,0,100,100,0,0,1,3,2,5,60,60,60,1
Style: Black,{black},72,&H00F2F2F4,&H000000FF,&H000A0A0C,&H96000000,0,0,0,0,100,100,0,0,1,3,2,5,60,60,60,1
Style: Mono,{mono},40,&H00ECD696,&H000000FF,&H000A0A0C,&H96000000,-1,0,0,0,100,100,1,0,1,2.2,1.2,5,60,60,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(sans=F_SANS, serif=F_SERIF, black=F_BLACK, mono=F_MONO)


def main():
    ensure_dirs()
    narration()
    cues()
    EVENTS.sort(key=lambda e: (e[1], e[0]))
    with open(os.path.join(BUILD, "main.ass"), "w", encoding="utf-8") as f:
        f.write(HEADER)
        for layer, t0, t1, style, text in EVENTS:
            f.write(f"Dialogue: {layer},{tf(t0)},{tf(t1)},{style},,0,0,0,,{text}\n")
    print(f"{os.path.join(BUILD, 'main.ass')}: {len(EVENTS)} events")


def audit():
    """Print every narration line the repair pass changed."""
    for s in parse_srt():
        a = s["text"]
        b = repair(a)
        if a != b:
            print(f"{s['start']:8.2f}  {a}\n          → {b}")


if __name__ == "__main__":
    if "--audit" in sys.argv:
        audit()
    else:
        main()
