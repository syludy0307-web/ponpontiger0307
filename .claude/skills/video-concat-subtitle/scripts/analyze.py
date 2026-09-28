#!/usr/bin/env python3
"""セリフの文字起こし調査ツール（Whisper large-v3）。

  # 1) 全体を調べる（クリップは番号順に並べて渡す）
  python analyze.py scan 001.mov 002.mov 003.mov --work WORK

  # 2) 気になる区間だけ聞き直す（時刻は連結後の通し時刻・秒）。区間はいくつでも並べられる
  #    （モデルの読み込みに毎回20〜40秒かかるので、聞きたい区間はまとめて1回で渡す）
  python analyze.py window WORK/audio_concat.wav 21.3 26.6  34.4 35.6 --lang ja
  python analyze.py window WORK/audio_concat.wav 6.6 9.2 --lang auto
  python analyze.py window WORK/audio_concat.wav 7.3 9.8 --models large-v3,large-v2,medium
  python analyze.py window WORK/audio_concat.wav 22.4 24.8 --hotwords 物の怪

scan がやること:
  A. 連結音声・VADあり（基準にする）
  B. 連結音声・VADなし（A が合体させたり落としたりした発話を拾う）
  C. クリップごと・VADあり（クリップの境目をまたいだ取り違えを防ぐ）
  D. 音はあるのに文字になっていない区間を、言語自動判別で聞き直す（英語セリフの取りこぼし対策）
  E. 1つの発話の中で語と語の間が大きく空いている所を、前後に分けて聞き直す（ずれ・合体の疑い）
結果は画面に出し、WORK/analysis.json にも保存する。

判断（幻聴か・誰の声か・固有名詞か）はツールではなく読む側がする。
このツールの役目は、判断に必要な材料を漏れなく並べること。
"""
from __future__ import annotations

import argparse
import difflib
import json
import math
import os
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

SR = 16000
GAP_WARN = 0.8          # 1つの発話の中で語の間がこれ以上空いたら「ずれ・合体の疑い」
LONG_WORD = 0.9         # 1語がこれ以上の長さなら「無音を抱き込んだずれの疑い」

# 無音・BGM・効果音の区間で Whisper が出しがちなフレーズ（実際に何度も出た）
# EXACT は本物のセリフのこともあるので「弱」、CONTAINS はそれだけで「強」
EXACT_HALLU = {"おわり", "you", "bye", "byebye", "thankyou", "thanks", "ありがとうございました", "감사합니다"}
CONTAINS_HALLU = ["ご視聴ありがとうございました", "チャンネル登録", "最後まで視聴", "ご覧いただき", "thanksforwatching",
                  "thankyouforwatching", "다음영상에서", "takkforwatching",
                  "seeyouinthenextvideo", "字幕は", "字幕作成", "字幕由",
                  # 各国語の「字幕: 〇〇」というクレジット（Whisper の定番の幻聴）
                  "soustitrage", "soustitres", "teksting", "amaraorg", "untertitel", "subtitlesby"]


# ------------------------------------------------------------------ 音声の入出力

def read_wav(path) -> np.ndarray:
    with wave.open(str(path)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).copy()


def write_wav(path, x: np.ndarray) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(x.astype(np.int16).tobytes())


def extract_clip_audio(clip: dict, out: Path) -> np.ndarray:
    """16kHz モノラルに変換し、クリップの尺ぴったりに無音で埋める／切る。

    render.py の連結（concat フィルタ）はクリップごとに長い方のストリームに合わせて
    音声を無音で埋めるので、ここでも同じ時間軸にそろえておく。
    """
    x = np.zeros(0, dtype=np.int16)
    if clip["has_audio"]:
        r = common.run([common.ffmpeg(), "-v", "error", "-i", clip["path"], "-vn",
                        "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", "-y", out])
        if r.returncode != 0:
            sys.exit(f"音声の取り出しに失敗: {clip['name']}\n{r.stderr}")
        x = read_wav(out)
    n = int(round(clip["duration"] * SR))
    x = np.concatenate([x, np.zeros(max(0, n - len(x)), dtype=np.int16)])[:n]
    write_wav(out, x)
    return x


def energy(x: np.ndarray, win: float = 0.5) -> list:
    step = int(SR * win)
    out = []
    for i in range(0, len(x), step):
        seg = x[i:i + step].astype(np.float64)
        if len(seg) < step // 4:
            break
        rms = math.sqrt(float(np.mean(seg * seg)))
        out.append((round(i / SR, 2), 20 * math.log10(rms / 32768) if rms > 0 else -99.0))
    return out


# ------------------------------------------------------------------ Whisper

def load_model(name: str, device: str):
    from faster_whisper import WhisperModel
    ct = "int8" if device == "cpu" else "float16"
    print(f"[モデル読み込み] {name} ({device}/{ct})  ※初回はダウンロードで数分かかる", flush=True)
    return WhisperModel(name, device=device, compute_type=ct, cpu_threads=min(8, os.cpu_count() or 4))


def decode(model, x, lang, vad, beam=5, min_sil=400, offset=0.0, prompt=None, hotwords=None):
    audio = x.astype(np.float32) / 32768.0
    kw = dict(language=lang, beam_size=beam, word_timestamps=True,
              condition_on_previous_text=False, vad_filter=vad)
    if vad:
        kw["vad_parameters"] = dict(min_silence_duration_ms=min_sil)
    if prompt:
        kw["initial_prompt"] = prompt
    if hotwords:
        kw["hotwords"] = hotwords
    try:
        segs, info = model.transcribe(audio, **kw)
        segs = list(segs)
    except TypeError:                       # 古い faster-whisper は hotwords 非対応
        kw.pop("hotwords", None)
        segs, info = model.transcribe(audio, **kw)
        segs = list(segs)
    out = []
    for s in segs:
        words = [{"w": w.word.strip(), "s": round(w.start + offset, 2), "e": round(w.end + offset, 2),
                  "p": round(w.probability, 3)} for w in (s.words or [])]
        out.append({"start": round(s.start + offset, 2), "end": round(s.end + offset, 2),
                    "text": s.text.strip(), "words": words})
    return out, info


def decode_window(model, x, a, b, lang, **kw):
    i0, i1 = max(0, int(a * SR)), min(len(x), int(b * SR))
    return decode(model, x[i0:i1], lang, vad=False, beam=10, offset=i0 / SR, **kw)


# ------------------------------------------------------------------ 判定の材料

def _key(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum())


def mark_hallucination(seg: dict, total: float, lang_prob=None) -> dict:
    reasons, certain = [], False
    k = _key(seg["text"])
    if not k:
        reasons.append("文字が無い（記号・絵文字・♪だけ）")
        certain = True
    elif any(p in k for p in CONTAINS_HALLU):
        reasons.append("定番の幻聴フレーズ")
        certain = True
    elif k in EXACT_HALLU:
        reasons.append("幻聴によく出る短い語")
    ws = seg["words"]
    if ws and ws[0]["p"] < 0.35:
        reasons.append(f"先頭語の信頼度が低い {ws[0]['p']:.2f}")
    if seg["end"] > total + 0.3:
        reasons.append("動画の長さを超えた時刻")
        certain = True
    if lang_prob is not None and lang_prob < 0.6:
        reasons.append(f"言語判定が不確か {lang_prob:.2f}")
    strong = certain or len(reasons) >= 2
    seg["halluc"] = {"reasons": reasons, "level": "強" if strong else ("弱" if reasons else "")}
    return seg


def onset(x: np.ndarray, a: float, b: float, thr: float):
    """a〜b 秒の中で、音が thr dB を超えて 0.1 秒以上続き始める時刻（50ms 刻み）。

    区間を切り出して聞き直すと、先頭の語の時刻が区間の開始に張り付くことがある。
    そのときはこの「音の立ち上がり」を開始時刻の目安にする。
    """
    step = int(SR * 0.05)
    loud_run = 0
    for i in range(max(0, int(a * SR)), min(len(x), int(b * SR)), step):
        seg = x[i:i + step].astype(np.float64)
        rms = math.sqrt(float(np.mean(seg * seg))) if len(seg) else 0.0
        if rms > 0 and 20 * math.log10(rms / 32768) > thr:
            loud_run += 1
            if loud_run >= 2:
                return round(i / SR - 0.05, 2)
        else:
            loud_run = 0
    return None


def long_words(seg: dict) -> list:
    """1語なのに長すぎる語。前の無音を抱き込んでいて、実際の開始はもっと後ろ（例: 「詳」が1.2秒）。"""
    return [w for w in seg["words"] if w["e"] - w["s"] >= LONG_WORD]


def word_onset(x, w: dict, thr: float):
    o = onset(x, w["s"], w["e"] + 0.1, thr)
    return o if o is not None and o > w["s"] + 0.15 else None


def start_hint(x, segs, win_start, thr):
    """先頭の語が区間の開始に張り付いている／長すぎるとき、音の立ち上がりを返す。"""
    if not segs or not segs[0]["words"]:
        return None
    ws = segs[0]["words"]
    pinned = abs(ws[0]["s"] - win_start) <= 0.06
    if not pinned and ws[0]["e"] - ws[0]["s"] < LONG_WORD:
        return None
    end = ws[0]["e"] + 0.1
    if pinned and len(ws) > 1:
        end = max(end, ws[1]["s"])
    o = onset(x, ws[0]["s"], end, thr)
    return o if o is not None and o > ws[0]["s"] + 0.15 else None


def internal_gaps(seg: dict) -> list:
    ws = seg["words"]
    return [(ws[k - 1]["e"], ws[k]["s"], k) for k in range(1, len(ws))
            if ws[k]["s"] - ws[k - 1]["e"] >= GAP_WARN]


def _merge(spans: list) -> list:
    out = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def loud_regions(prof: list):
    dbs = np.array([d for _, d in prof]) if prof else np.array([-99.0])
    floor = float(np.percentile(dbs, 20))
    thr = min(-28.0, floor + 12.0)          # 騒がしい素材でも静かな素材でも効くしきい値
    regs = []
    for t, d in prof:
        if d > thr:
            if regs and t - regs[-1][1] <= 0.5:
                regs[-1][1] = t + 0.5
            else:
                regs.append([t, t + 0.5])
    return regs, thr, floor


def uncovered_windows(loud: list, covered: list, total: float) -> list:
    pieces = []
    for a, b in loud:
        cur = a
        for c0, c1 in covered:
            if c1 <= cur or c0 >= b:
                continue
            if c0 > cur:
                pieces.append([cur, c0])
            cur = max(cur, c1)
        if cur < b:
            pieces.append([cur, b])
    wins = []
    for a, b in pieces:
        a, b = max(0.0, a - 0.3), min(total, b + 0.3)
        if b - a < 0.6:
            continue
        n = max(1, math.ceil((b - a) / 2.6))
        step = (b - a) / n
        wins += [(round(a + i * step, 2), round(a + (i + 1) * step, 2)) for i in range(n)]
    return wins


def same_utterance(s1: dict, s2: dict) -> bool:
    overlap = min(s1["end"], s2["end"]) - max(s1["start"], s2["start"])
    if overlap < -0.5:
        return False
    k1, k2 = _key(s1["text"]), _key(s2["text"])
    if k1 and k2 and (k1 in k2 or k2 in k1):   # C は複数の行を1つにまとめることがある
        return True
    return difflib.SequenceMatcher(None, k1, k2).ratio() >= 0.5


def fmt_words(seg: dict) -> str:
    return " ".join(f"{w['w']}@{w['s']:.2f}-{w['e']:.2f}({w['p']:.2f})" for w in seg["words"])


def ts(t: float) -> str:
    return f"{t:6.2f}"


# ------------------------------------------------------------------ scan

def cmd_scan(a) -> None:
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    clips = [common.probe(c) for c in a.clips]

    print("===== 素材（この順で連結される） =====")
    bounds, t = [], 0.0
    for i, c in enumerate(clips, 1):
        bounds.append((t, t + c["duration"]))
        print(f"{i:03d} {c['name']:<28} {c['width']}x{c['height']}  {c['fps']:.3g}fps  "
              f"{c['vcodec']}/{c['profile']}/{c['pix_fmt']}  "
              f"{(c['acodec'] or '音声なし')} {c['sample_rate'] or ''}  {c['duration']:.3f}s"
              + (f"  回転{c['rotation']}°" if c["rotation"] else ""))
        t += c["duration"]
    total = t
    sizes = {(c["width"], c["height"]) for c in clips}
    print(f"合計 {total:.2f} 秒" + (f" / 境目: {', '.join(f'{b:.2f}' for _, b in bounds[:-1])} 秒" if len(clips) > 1 else ""))
    if len(sizes) > 1:
        print("※ 解像度が混ざっている → render.py が1本目に合わせて縮小＋余白で揃える")

    xs = [extract_clip_audio(c, work / f"audio_{i:03d}.wav") for i, c in enumerate(clips, 1)]
    x = np.concatenate(xs)
    concat_path = work / "audio_concat.wav"
    write_wav(concat_path, x)

    prof = energy(x)
    loud, thr, floor = loud_regions(prof)
    print(f"\n===== 音量（0.5秒ごと） しきい値 {thr:.1f}dB / 床 {floor:.1f}dB =====")
    edges = [b for _, b in bounds[:-1]]
    for t0, db in prof:
        mark = "  <-- 境目" if any(t0 <= e < t0 + 0.5 for e in edges) else ""
        print(f"{t0:6.1f}s {db:6.1f} {'#' * max(0, int((db + 60) / 2))}{mark}")

    model = load_model(a.model, a.device)

    print("\n[A] 連結・VADあり …", flush=True)
    A, _ = decode(model, x, "ja", vad=True)
    print("[B] 連結・VADなし …", flush=True)
    B, _ = decode(model, x, "ja", vad=False, beam=10)
    print("[C] クリップ個別 …", flush=True)
    C = []
    for (s0, _e), xi in zip(bounds, xs):
        C += decode(model, xi, "ja", vad=True, min_sil=300, offset=s0)[0]
    for seg in A + B + C:
        mark_hallucination(seg, total)

    # Whisper の語の時刻は早めに出がちで、実際の声は語の終わりの後も少し続く。
    # 後ろを広めに見ておかないと、セリフの語尾が「文字の無い区間」として拾われて幻聴が出る
    covered = _merge([[w["s"] - 0.3, w["e"] + 0.6] for seg in A + B + C
                      if seg["halluc"]["level"] != "強" for w in seg["words"]])
    wins = uncovered_windows(loud, covered, total)
    print(f"[D] 音があるのに文字が無い区間 {len(wins)} 個を言語自動判別で聞き直し …", flush=True)
    D = []
    for w0, w1 in wins:
        segs, info = decode_window(model, x, w0, w1, None)
        for s in segs:
            mark_hallucination(s, total, info.language_probability)
        item = {"start": w0, "end": w1, "lang": info.language,
                "lang_prob": round(info.language_probability, 2), "segments": segs}
        if info.language != "ja":           # 短い日本語が他言語と誤判定されることもあるので両方見る
            item["as_ja"] = mark_hallucination_list(decode_window(model, x, w0, w1, "ja")[0], total)
        D.append(item)

    print("[E] 語間の空白を聞き直し …", flush=True)
    E = []
    for idx, seg in enumerate(A, 1):
        for g0, g1, _k in internal_gaps(seg):
            before = (max(0.0, seg["start"] - 0.3), min(total, g0 + 0.3))
            after = (max(0.0, g1 - 0.8), min(total, seg["end"] + 0.3))
            after_segs = decode_window(model, x, *after, "ja")[0]
            E.append({"a_index": idx, "gap": [g0, g1], "text": seg["text"],
                      "before": {"range": before, "segments": decode_window(model, x, *before, "ja")[0]},
                      "after": {"range": after, "segments": after_segs,
                                "onset": start_hint(x, after_segs, after[0], thr)}})

    # ---------------------------------------------------------------- レポート
    def show(title, segs, words=False):
        print(f"\n===== {title} =====")
        if not segs:
            print("  （なし）")
        for s in segs:
            h = s["halluc"]
            flag = f"   ⚠幻聴の疑い({h['level']}): {', '.join(h['reasons'])}" if h["level"] else ""
            print(f"[{ts(s['start'])} -> {ts(s['end'])}] {s['text']}{flag}")
            if words:
                print(f"      {fmt_words(s)}")
                for g0, g1, _k in internal_gaps(s):
                    print(f"      ⚠ 語の間が {g1 - g0:.1f} 秒空いている（{g0:.2f}→{g1:.2f}）→ E を参照")
                for w in long_words(s):
                    o = word_onset(x, w, thr)
                    if o:
                        pause = o - w["s"]
                        print(f"      ⚠「{w['w']}」が {w['e'] - w['s']:.1f} 秒と長い → 前に約 {pause:.1f} 秒の間。"
                              f"音の立ち上がり ≈ {o:.2f} 秒"
                              + ("（1秒以上なので、ここで行を分けてこの時刻を開始にする）" if pause >= 1.0
                                 else "（1秒未満なので分けなくてよい）"))
                    else:
                        print(f"      ・「{w['w']}」が {w['e'] - w['s']:.1f} 秒と長いが、頭から声が続いている"
                              "（ゆっくり言っているだけ。間は無いので1行のままでよい）")

    show("A: 連結・VADあり（基準）", A, words=True)
    show("B: 連結・VADなし", B)
    show("C: クリップ個別", C)

    print("\n===== D: 音があるのに文字になっていなかった区間（言語自動判別） =====")
    if not D:
        print("  （なし）")
    for d in D:
        body = " / ".join(f"「{s['text']}」{'⚠' + s['halluc']['level'] if s['halluc']['level'] else ''}"
                          f" {fmt_words(s)}" for s in d["segments"]) or "（文字なし）"
        prev = [s for s in A + B + C if s["halluc"]["level"] != "強" and 0 <= d["start"] - s["end"] <= 1.2]
        tail = (f"  ← 直前の「…{max(prev, key=lambda s: s['end'])['text'][-6:]}」の語尾かも"
                if prev else "")
        print(f"{d['start']:6.2f}-{d['end']:6.2f}  lang={d['lang']}({d['lang_prob']:.2f})  {body}{tail}")
        if "as_ja" in d:
            ja = " / ".join(f"「{s['text']}」{'⚠' + s['halluc']['level'] if s['halluc']['level'] else ''}"
                            f" {fmt_words(s)}" for s in d["as_ja"]) or "（文字なし）"
            print(f"{'':15}  日本語で聞くと: {ja}")

    print("\n===== E: 語間の空白を前後に分けて聞き直した結果 =====")
    if not E:
        print("  （なし）")
    for e in E:
        print(f"A#{e['a_index']}「{e['text']}」 {e['gap'][0]:.2f}→{e['gap'][1]:.2f} が空いている")
        for side in ("before", "after"):
            r = e[side]["range"]
            segs = e[side]["segments"]
            body = " / ".join(f"「{s['text']}」 {fmt_words(s)}" for s in segs) or "（文字なし）"
            print(f"   {'前' if side == 'before' else '後'} {r[0]:.2f}-{r[1]:.2f}: {body}")
        if e["after"].get("onset") is not None:
            print(f"   ※ 後半の先頭の語が区間の開始に張り付いている。音の立ち上がり ≈ {e['after']['onset']:.2f} 秒"
                  " → これを開始時刻にする")

    # ---------------------------------------------------------------- まとめ
    print("\n===== まとめ（ここを見て lines.json を作る） =====")
    base = [s for s in A if s["halluc"]["level"] != "強"]
    print("セリフ候補（A 基準・幻聴の疑いが強いものは除外済み。裏付け＝同じ内容が出た聞き方）:")
    for i, s in enumerate(base, 1):
        seen = "A" + ("B" if any(same_utterance(s, o) for o in B) else "") + \
               ("C" if any(same_utterance(s, o) for o in C) else "")
        notes = []
        if internal_gaps(s):
            fix = next((e["after"]["onset"] for e in E if e["text"] == s["text"] and e["after"].get("onset")), None)
            notes.append("語間に空白→Eを確認" + (f"（開始の目安 {fix:.2f} 秒）" if fix else ""))
        for w in long_words(s):
            o = word_onset(x, w, thr)
            if o and o - w["s"] >= 1.0:
                notes.append(f"「{w['w']}」の前に約{o - w['s']:.1f}秒の間 → ここで行を分け、後ろは {o:.2f} 秒開始")
        # ※ ふつうの行の開始時刻は Whisper のままでよい（0.3秒ほど早めに出がちだが、字幕が少し早く出るぶんには
        #    問題にならなかった）。音量から推定し直すと、ため息など小さな声で始まる行で遅れる方向に外れる。
        if s["halluc"]["level"]:
            notes.append("幻聴の疑い(弱)")
        print(f"  {i:2d} [{ts(s['start'])} – {ts(s['end'])}] {s['text']}   裏付け:{seen}"
              + (f"   ※{' / '.join(notes)}" if notes else ""))

    extra = [s for s in B + C if s["halluc"]["level"] != "強" and not any(same_utterance(s, o) for o in A)]
    if extra:
        print("A に無いが B/C で出た発話（取りこぼしの可能性。window で確認する）:")
        for s in extra:
            print(f"     [{ts(s['start'])} – {ts(s['end'])}] {s['text']}")
    real_d = [(d, s) for d in D for s in d["segments"]
              if not s["halluc"]["level"] and s["words"]
              and sum(w["p"] for w in s["words"]) / len(s["words"]) >= 0.7]
    if real_d:
        print("文字が出ていなかった区間で、実際の発話らしいもの（日本語以外も含む）:")
        for d, s in real_d:
            avg = sum(w["p"] for w in s["words"]) / len(s["words"])
            print(f"     [{ts(s['start'])} – {ts(s['end'])}] lang={d['lang']} 「{s['text']}」 平均p={avg:.2f}")
    dropped = [s for s in A + B + C if s["halluc"]["level"] == "強"]
    dropped += [s for d in D for s in d["segments"] if s["halluc"]["level"] == "強"]
    if dropped:
        print(f"幻聴として除外したもの {len(dropped)} 件（例）:")
        for s in dropped[:6]:
            print(f"     [{ts(s['start'])} – {ts(s['end'])}] 「{s['text']}」 {', '.join(s['halluc']['reasons'])}")

    report = {"clips": clips, "bounds": bounds, "total": total, "audio_concat": str(concat_path),
              "energy": prof, "threshold_db": thr, "floor_db": floor, "loud_regions": loud,
              "A_vad": A, "B_novad": B, "C_per_clip": C, "D_uncovered": D, "E_gaps": E}
    (work / "analysis.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n保存: {work / 'analysis.json'}")
    print(f"聞き直し用の連結音声: {concat_path}")


def mark_hallucination_list(segs, total):
    for s in segs:
        mark_hallucination(s, total)
    return segs


# ------------------------------------------------------------------ window

def cmd_window(a) -> None:
    if len(a.ranges) % 2:
        sys.exit("区間は「開始 終了」の組で渡してください（例: 21.3 26.6 34.4 35.6）")
    pairs = [(a.ranges[i], a.ranges[i + 1]) for i in range(0, len(a.ranges), 2)]
    x = read_wav(a.wav)
    total = len(x) / SR
    lang = None if a.lang == "auto" else a.lang
    _loud, thr, _floor = loud_regions(energy(x))
    for name in [m.strip() for m in a.models.split(",") if m.strip()]:
        model = load_model(name, a.device)
        for st, en in pairs:
            segs, info = decode_window(model, x, st, en, lang, prompt=a.prompt, hotwords=a.hotwords)
            print(f"\n--- {name}  {st:.2f}-{en:.2f}  lang={info.language}({info.language_probability:.2f})"
                  + (f"  prompt={a.prompt!r}" if a.prompt else "") + (f"  hotwords={a.hotwords!r}" if a.hotwords else ""))
            if not segs:
                print("  （文字なし）")
            for s in segs:
                mark_hallucination(s, total, None if lang else info.language_probability)
                h = s["halluc"]
                print(f"  [{ts(s['start'])} -> {ts(s['end'])}] {s['text']}"
                      + (f"   ⚠幻聴の疑い({h['level']}): {', '.join(h['reasons'])}" if h["level"] else ""))
                print(f"      {fmt_words(s)}")
            o = start_hint(x, segs, st, thr)
            if o is not None:
                print(f"  ※ 先頭の語が区間の開始に張り付いている／長すぎる（区間の切り方の影響）。音の立ち上がり ≈ {o:.2f} 秒。\n"
                      "    scan で「語間の空白」「長すぎる語（間1秒以上）」と出た行ならこれを開始に使う。"
                      "それ以外の行は scan の A の時刻のままでよい")
            first = segs[0]["words"][0] if segs and segs[0]["words"] else None
            for s in segs:
                for w in long_words(s):
                    if w is first and o is not None:
                        continue                # すぐ上で報告済み
                    wo = word_onset(x, w, thr)
                    if wo:
                        print(f"  ※「{w['w']}」が {w['e'] - w['s']:.1f} 秒と長い → 前に約 {wo - w['s']:.1f} 秒の間。"
                              f"音の立ち上がり ≈ {wo:.2f} 秒")
        del model


def main() -> None:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="全体を調べる")
    s.add_argument("clips", nargs="+", help="クリップ（番号順）")
    s.add_argument("--work", required=True, help="作業フォルダ")
    s.add_argument("--model", default="large-v3")
    s.add_argument("--device", default="cpu", help="cpu / cuda")
    w = sub.add_parser("window", help="区間を聞き直す")
    w.add_argument("wav", help="scan が作った audio_concat.wav")
    w.add_argument("ranges", nargs="+", type=float, help="開始 終了 [開始 終了 ...]（秒）。まとめて渡すと速い")
    w.add_argument("--lang", default="ja", help="ja / en / auto など")
    w.add_argument("--models", default="large-v3",
                   help="カンマ区切り。例 large-v3,large-v2,medium（large-v2 と medium は初回ダウンロードあり）")
    w.add_argument("--prompt", default=None, help="文脈として与える文（initial_prompt）")
    w.add_argument("--hotwords", default=None, help="出やすくしたい語")
    w.add_argument("--device", default="cpu")
    a = ap.parse_args()
    cmd_scan(a) if a.cmd == "scan" else cmd_window(a)


if __name__ == "__main__":
    main()
