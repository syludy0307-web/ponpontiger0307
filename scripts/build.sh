#!/usr/bin/env bash
# 2本の .mov を連結し、冒頭5秒にタイトル「おなら以外」を、
# セリフにピンク太字の字幕を焼き込む。
#   使い方: ./build.sh <clip1.mov> <clip2.mov> [出力.mp4]
set -euo pipefail

CLIP1="${1:?clip1 が必要です}"
CLIP2="${2:?clip2 が必要です}"
OUT="${3:-onara-igai_final.mp4}"
HERE="$(cd "$(dirname "$0")" && pwd)"

# 必要なもの: ffmpeg(libass有効) / python3+Pillow / Noto Sans CJK
#   apt-get install -y ffmpeg fonts-noto-cjk && pip install Pillow

# 1) 連結（両クリップとも 720x1280 / 24fps / h264 / pcm_s16le なので再エンコード不要）
printf "file '%s'\n" "$(realpath "$CLIP1")" "$(realpath "$CLIP2")" > list.txt
ffmpeg -v error -f concat -safe 0 -i list.txt -c copy -y concat.mov

# 2) タイトル画像を生成（白文字＋濃いフチ＋ドロップシャドウ）
python3 "$HERE/make_title.py"

# 3) タイトル＋字幕をまとめて1パスで焼き込む（再エンコードは1回だけ）
#    タイトル: 0.00-0.55s スライドイン(バウンド) / 0.00-0.35s フェードイン
#              4.55-5.00s フェードアウト＋上へドリフト → 5.00s で消灯
#    字幕:     Noto Sans CJK JP Bold・ピンク(#FF5FAF)・濃いフチ＋影・各0.15sフェード
cp "$HERE/subs.ass" ./subs.ass
ffmpeg -v error -stats \
  -i concat.mov \
  -framerate 24 -loop 1 -t 5 -i title.png \
  -filter_complex_script "$HERE/final_filter.txt" \
  -map '[v]' -map 0:a \
  -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -profile:v high -level 4.0 \
  -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart -y "$OUT"

echo "できました: $OUT"

# 4) 文字起こしをやり直す場合
#    ffmpeg -v error -i concat.mov -vn -ac 1 -ar 16000 -y audio16k.wav
#    python3 "$HERE/transcribe.py" large-v3
