#!/usr/bin/env python3
"""セリフ一覧（lines.json）から、焼き込み用の字幕・SRT・文字起こし txt をまとめて作る。

  python make_subs.py WORK/lines.json --clips 001.mov 002.mov 003.mov --name warudakumi --work WORK

できるもの（すべて WORK に置く）:
  subs.ass                    render.py で焼き込む字幕（ハウススタイル・解像度に合わせて自動調整）
  transcript_<name>.srt       発話どおりの時刻の字幕ファイル
  transcript_<name>.txt       文字起こし。最後の「補足」は自分で書き足す

lines.json の書き方:
{
  "title": "悪だくみ",
  "lines": [
    {"start": 0.85, "end": 3.29, "speaker": "female", "text": "はぁ、まだお姉ちゃん来ない"},
    {"start": 9.33, "end": 11.73, "speaker": "male", "text": "いい話があるんだけど、\\n興味ない？"},
    {"start": 27.58, "end": 29.44, "speaker": "male", "text": "こいつ、ちょろいな", "aside": true},
    {"start": 6.60, "end": 8.35, "speaker": "male", "text": "Are you okay?\\nAre you hurt?", "label": "男性・英語"}
  ]
}
  start/end : 発話の開始・終了（連結後の通し時刻・秒）。字幕の前後の余白はこのスクリプトが付ける
  speaker   : female（ピンク）/ male（金）/ other（白）
  text      : \\n で改行位置を指定できる。無ければ、はみ出すときだけ句読点で自動改行する
  aside     : true なら心の声。字幕を（ ）で囲む
  label     : txt に書く話者の表記を変えたいとき（例: "男性・英語"）
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

# ハウススタイル（720x1280 基準の値。解像度に合わせて比例させる）
BASE_W, BASE_H = 720, 1280
FONT_SIZE, OUTLINE, SHADOW, MARGIN_LR, MARGIN_V = 68, 6, 4, 28, 105
COLORS = {                      # ASS の色は &HAABBGGRR
    "female": ("Pink", "&H00AF5FFF"),     # #FF5FAF
    "male": ("Gold", "&H004AC2FF"),       # #FFC24A
    "other": ("White", "&H00FFFFFF"),
}
LABELS = {"female": "女性", "male": "男性", "other": "その他"}
OUTLINE_COLOR, BACK_COLOR = "&H00201A1A", "&H90000000"
FADE_MS = 150
LEAD, TAIL, MIN_SHOW, GAP = 0.10, 0.30, 0.90, 0.06   # 前の余白・後の余白・最短表示・字幕どうしの隙間


class Measurer:
    """libass と同じ考え方で文字幅を見積もる（フォントサイズ＝アセンダ＋ディセンダ）。"""

    def __init__(self, font_info):
        self.fi = font_info
        f = common.load_font(font_info, 1000)
        asc, desc = f.getmetrics()
        self.ratio = 1000.0 / (asc + desc)
        self.cache = {}

    def width(self, text: str, fs: int) -> float:
        size = max(1, round(fs * self.ratio))
        if size not in self.cache:
            self.cache[size] = common.load_font(self.fi, size)
        return self.cache[size].getlength(text)


def split_best(text: str, m: Measurer, fs: int):
    """いちばん左右の長さが揃う位置で2行に分ける。句読点の後ろを優先する。"""
    punct = set("、。，．！？!?…‥・　 ）」』")
    cands = [i + 1 for i, ch in enumerate(text[:-1]) if ch in punct]
    if not cands:
        cands = [i for i in range(1, len(text))
                 if not (text[i - 1].isascii() and text[i - 1].isalnum() and text[i].isascii() and text[i].isalnum())]
    if not cands:
        return [text]
    i = min(cands, key=lambda k: max(m.width(text[:k].rstrip(), fs), m.width(text[k:].lstrip(), fs)))
    return [text[:i].rstrip(), text[i:].lstrip()]


def join_lines(parts: list) -> str:
    out = parts[0]
    for p in parts[1:]:
        out += (" " if out[-1:].isascii() and p[:1].isascii() else "") + p
    return out


def ass_time(t: float) -> str:
    cs = int(round(max(0.0, t) * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def srt_time(t: float) -> str:
    ms = int(round(max(0.0, t) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def txt_time(t: float) -> str:
    cs = int(round(max(0.0, t) * 100))
    return f"{cs // 6000:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def dispw(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def ass_escape(s: str) -> str:
    return s.replace("\\", "＼").replace("{", "｛").replace("}", "｝")


def main() -> None:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lines_json")
    ap.add_argument("--clips", nargs="+", required=True, help="クリップ（番号順）。尺・解像度・txt の見出しに使う")
    ap.add_argument("--name", required=True, help="ファイル名に使う英数字の名前（例 warudakumi）")
    ap.add_argument("--work", required=True)
    ap.add_argument("--title", default=None, help="lines.json に title が無いとき用")
    ap.add_argument("--font-family", default=None, help="字幕のフォント名を指定したいとき")
    a = ap.parse_args()

    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    data = json.loads(Path(a.lines_json).read_text(encoding="utf-8"))
    lines = data["lines"] if isinstance(data, dict) else data
    title = (data.get("title") if isinstance(data, dict) else None) or a.title or a.name
    clips = [common.probe(c) for c in a.clips]
    total = sum(c["duration"] for c in clips)
    W, H = clips[0]["width"], clips[0]["height"]

    for i, ln in enumerate(lines, 1):
        if ln.get("speaker") not in COLORS:
            sys.exit(f"{i}行目: speaker は female / male / other のどれか（今: {ln.get('speaker')!r}）")
        if not (0 <= float(ln["start"]) < float(ln["end"])):
            sys.exit(f"{i}行目: start < end になっていない")
        if not str(ln.get("text", "")).strip():
            sys.exit(f"{i}行目: text が空")
    lines = sorted(lines, key=lambda ln: float(ln["start"]))

    font_info = common.find_jp_font()
    if not font_info:
        sys.exit("日本語の太字フォントが見つかりません。scripts/setup_check.py の案内に従ってください。")
    family = a.font_family or font_info["family"]
    s, sx = H / BASE_H, W / BASE_W
    fs, ol, sh = round(FONT_SIZE * s), max(1, round(OUTLINE * s)), max(1, round(SHADOW * s))
    ml = mr = round(MARGIN_LR * sx)
    mv = round(MARGIN_V * s)
    limit = (W - ml - mr - 2 * ol) * 0.97
    meas = Measurer(font_info)

    # ---- 表示時間: 前後に余白を付け、重ならないよう詰め、短すぎるものは延ばす
    n = len(lines)
    raw = [(float(ln["start"]), float(ln["end"])) for ln in lines]
    starts, ends = [], []
    for k, (st, en) in enumerate(raw):
        s0 = st - LEAD
        if k > 0 and raw[k - 1][1] <= st:
            s0 = max(s0, raw[k - 1][1] + GAP)
        starts.append(max(0.0, s0))
    for k, (st, en) in enumerate(raw):
        e0 = max(en + TAIL, starts[k] + MIN_SHOW)
        if k + 1 < n and en <= raw[k + 1][0]:
            e0 = min(e0, starts[k + 1] - GAP)
        ends.append(min(max(e0, en), total - 0.02))
    overlaps = [k for k in range(n - 1) if raw[k][1] > raw[k + 1][0]]

    # ---- 改行と幅のチェック
    notices, events = [], []
    for k, ln in enumerate(lines):
        parts = [p.strip() for p in str(ln["text"]).split("\n") if p.strip()]
        if len(parts) == 1 and meas.width(parts[0], fs) > limit:
            parts = split_best(parts[0], meas, fs)
            notices.append(f"{k + 1}行目を自動改行: 「{' / '.join(parts)}」（不自然なら lines.json に \\n で指定）")
        if ln.get("aside"):             # 1行だけのときは parts[0] と parts[-1] が同じ要素なので順番に足す
            parts[0] = "（" + parts[0]
            parts[-1] = parts[-1] + "）"
        fs_k = fs
        while max(meas.width(p, fs_k) for p in parts) > limit and fs_k > fs * 0.6:
            fs_k -= 1
        if fs_k != fs:
            notices.append(f"{k + 1}行目は長いので文字を {fs}→{fs_k} に縮小（改行位置を見直す手もある）")
        style = COLORS[ln["speaker"]][0]
        body = "\\N".join(ass_escape(p) for p in parts)
        tags = f"{{\\fad({FADE_MS},{FADE_MS})" + (f"\\fs{fs_k}" if fs_k != fs else "") + "}"
        events.append(f"Dialogue: 0,{ass_time(starts[k])},{ass_time(ends[k])},{style},,0,0,0,,{tags}{body}")
        ln["_display"] = join_lines(parts)

    styles = "\n".join(
        f"Style: {name},{family},{fs},{col},{col},{OUTLINE_COLOR},{BACK_COLOR},-1,0,0,0,100,100,0,0,1,"
        f"{ol},{sh},2,{ml},{mr},{mv},1" for name, col in COLORS.values())
    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{styles}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(events) + "\n"
    (work / "subs.ass").write_text(ass, encoding="utf-8")

    # ---- SRT（余白なし・発話どおりの時刻）
    srt = "\n".join(f"{k + 1}\n{srt_time(st)} --> {srt_time(en)}\n{ln['_display']}\n"
                    for k, ((st, en), ln) in enumerate(zip(raw, lines)))
    (work / f"transcript_{a.name}.srt").write_text(srt, encoding="utf-8")

    # ---- 文字起こし txt（補足は後で書き足す）
    def label(ln):
        return ln.get("label") or (LABELS[ln["speaker"]] + ("・心の声" if ln.get("aside") else ""))

    plain = [join_lines([p.strip() for p in str(ln["text"]).split("\n") if p.strip()]) for ln in lines]
    col = min(max(dispw(p) for p in plain) + 2, 48)
    rule = "-" * 59
    out = [f"文字起こし — {title}（" + (f"{len(clips)}本連結 " if len(clips) > 1 else "") + f"全{total:.2f}秒）",
           "=" * 59]
    if len(clips) > 1:
        out.append("元素材（番号順に連結）:")
        t0 = 0.0
        for i, c in enumerate(clips, 1):
            out.append(f"  {i:03d}  {c['name']}   {txt_time(t0)} – {txt_time(t0 + c['duration'])}")
            t0 += c["duration"]
    else:
        c = clips[0]
        out.append(f"素材: {c['name']}   {c['width']}x{c['height']} / {c['fps']:.3g}fps / {total:.2f}秒")
    out += ["", rule]
    for (st, en), p, ln in zip(raw, plain, lines):
        out += [f"[{txt_time(st)} – {txt_time(en)}]  {p}{' ' * max(1, col - dispw(p))}（{label(ln)}）", ""]
    out[-1:] = [rule, "", "全文:"] + plain + ["", rule, "補足", "",
                "・（ここに書く: 確認したこと／字幕にしなかった音（笑い声・歓声・効果音）と幻聴として",
                "  除外したもの／話者の決め手／固有名詞など要確認の点）", ""]
    (work / f"transcript_{a.name}.txt").write_text("\n".join(out), encoding="utf-8")

    # ---- 画面表示
    print(f"字幕: {W}x{H} / {family} {fs}pt / フチ{ol} 影{sh} / 下余白{mv}")
    for k, ln in enumerate(lines):
        print(f"  {k + 1:2d} {ass_time(starts[k])}–{ass_time(ends[k])} {COLORS[ln['speaker']][0]:<5} {ln['_display']}")
    for msg in notices:
        print("※ " + msg)
    if overlaps:
        print("※ 発話が重なっている行: " + ", ".join(f"{k + 1}と{k + 2}" for k in overlaps)
              + "（字幕は上下に並んで同時表示される）")
    print(f"保存: {work / 'subs.ass'}\n      {work / f'transcript_{a.name}.srt'}\n      {work / f'transcript_{a.name}.txt'}"
          "  ← 最後の「補足」を書き足すこと")


if __name__ == "__main__":
    main()
