# -*- coding: utf-8 -*-
"""Music and sound-effect bed for the JAL123 documentary.

Design rules for this subject matter:
  * narration always wins — the BGM bed is side-chain ducked under it;
  * the casualty passage and the "people were still alive" passage carry
    no music at all;
  * SE are used as punctuation at structural boundaries and at the two
    physical events, never as shock hits.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import AUDIO_PATH, BGM_DIR, BUILD, SE_DIR, ensure_dirs

MIX = os.path.join(BUILD, "audio_mix.m4a")

# (start, end, track, gain_dB) — gaps are intentional silence.
BEDS = [
    (0.0, 30.0, "concrete_corridor.mp3", -15),
    (30.0, 152.0, "concrete_corridor.mp3", -12),
    # 152.0-166.5 犠牲者の場面: 無音
    (166.5, 279.4, "clock_in_the_hall.mp3", -14),
    (279.4, 350.0, "cold_tiles_beneath.mp3", -13),
    (350.4, 446.0, "where_floorboards_groan.mp3", -14),
    # 446.0-458.5 「まだ生きていた人がいた」: 無音
    (458.5, 511.0, "where_floorboards_groan.mp3", -15),
    (511.4, 742.0, "cold_tiles_beneath.mp3", -15),
    (742.0, 827.0, "concrete_corridor.mp3", -15),
    (827.4, 890.0, "last_room_is_locked.mp3", -14),
    (890.4, 1018.0, "beneath_the_floorboards.mp3", -14),
    (1018.6, 1072.0, "last_unplayed_key.mp3", -11),
]

# (time, file, gain_dB)
HITS = [
    (30.62, "se2.mp3", -9),     # 構造破壊の瞬間
    (166.60, "se1.mp3", -14),   # 章: 原因
    (288.85, "se4.mp3", -11),   # 隔壁の破壊
    (350.60, "se1.mp3", -14),   # 章: 陰謀論
    (511.60, "se1.mp3", -14),   # 章: 検証
    (239.65, "se3.mp3", -12),   # データ: 70%
    (827.60, "se1.mp3", -14),   # 章: 結論
    (890.60, "se5.mp3", -13),   # 章: 残された謎
    (943.10, "se4.mp3", -14),   # 2026年 削除
    (1060.60, "se5.mp3", -14),  # 結び
]

FADE = 2.5      # bed fade in/out (s)


def build(out=MIX, verbose=True):
    ensure_dirs()
    inputs = ["-i", AUDIO_PATH]
    parts = []
    labels = []
    for i, (t0, t1, track, gain) in enumerate(BEDS):
        dur = t1 - t0
        inputs += ["-stream_loop", "-1", "-i", os.path.join(BGM_DIR, track)]
        idx = i + 1
        fo = max(0.0, dur - FADE)
        parts.append(
            f"[{idx}:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,"
            f"volume={gain}dB,"
            f"afade=t=in:st=0:d={FADE},afade=t=out:st={fo:.3f}:d={FADE},"
            f"adelay={int(t0 * 1000)}|{int(t0 * 1000)}[b{idx}]")
        labels.append(f"[b{idx}]")
    off = len(BEDS) + 1
    for j, (t, se, gain) in enumerate(HITS):
        inputs += ["-i", os.path.join(SE_DIR, se)]
        idx = off + j
        parts.append(
            f"[{idx}:a]volume={gain}dB,adelay={int(t * 1000)}|{int(t * 1000)}[s{idx}]")
        labels.append(f"[s{idx}]")
    # music+SE bed, ducked by the narration, then summed with it
    parts.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:"
                 "dropout_transition=0,alimiter=limit=0.5[bed]")
    parts.append("[0:a]aformat=channel_layouts=stereo,volume=1.0,asplit=2[nar][sc]")
    parts.append("[bed][sc]sidechaincompress=threshold=0.03:ratio=6:attack=25:"
                 "release=700:makeup=1[duck]")
    parts.append("[nar][duck]amix=inputs=2:normalize=0:dropout_transition=0,"
                 "alimiter=limit=0.94,aresample=44100[out]")
    cmd = (["ffmpeg", "-y", "-v", "error"] + inputs +
           ["-filter_complex", ";".join(parts), "-map", "[out]",
            "-c:a", "aac", "-b:a", "192k", out])
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode:
        sys.stderr.write(r.stderr.decode()[-2500:])
        raise SystemExit(1)
    if verbose:
        print("audio mix:", out)
    return out


if __name__ == "__main__":
    build()
