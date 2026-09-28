# ponpontiger0307

縦型ショート動画を連結し、タイトル・文字起こし・字幕を入れて仕上げた成果物と、
その手順を別のチャットの Claude でも再現できるようにしたスキルです。

## 成果物 (`output/`)

| タイトル | 動画 | 文字起こし |
| --- | --- | --- |
| おなら以外 | `onara-igai_final.mp4` | `transcript.txt` / `.srt` |
| 信長 | `nobunaga_subtitled.mp4` | `transcript_nobunaga.txt` / `.srt` |
| アウェイ | `away_final.mp4` | `transcript_away.txt` / `.srt` |
| ハザード | `hazard_final.mp4` | `transcript_hazard.txt` / `.srt` |
| 濡れ衣 | `nureginu_final.mp4` | `transcript_nureginu.txt` / `.srt` |
| 電話にでないと… | `denwa_final.mp4` | `transcript_denwa.txt` / `.srt` |
| 悪だくみ | `warudakumi_final.mp4` | `transcript_warudakumi.txt` / `.srt` |
| シバネコガール | `shibanekogirl_final.mp4` | `transcript_shibanekogirl.txt` / `.srt` |

文字起こしの txt には、時刻・話者・判断したこと（除外した幻聴、話者の決め手など）の補足が付いています。

## ハウススタイル

- **連結**: ファイル名の番号順（001→002→003）
- **タイトル**: 画面上部・冒頭5秒。白文字＋濃いフチ＋影（Noto Sans CJK JP Bold）。
  上からスライドインして少し行き過ぎて戻る → 静止 → 最後の0.5秒で上に抜けながらフェードアウト
- **字幕**: 画面下部・太字・濃いフチと影・0.15秒フェード。女性＝ピンク `#FF5FAF`、男性＝金 `#FFC24A`。
  心の声は（ ）で囲む
- **画質**: 解像度は素材のまま、H.264（CRF18）＋AAC 192kbps、エンコードは1回

## スキル (`.claude/skills/video-concat-subtitle/`)

上の仕上げを、別のチャット・デスクトップ版の Claude が同じようにできるようにまとめたものです。
このリポジトリを Claude Code で開くと自動で読み込まれます。`dist/video-concat-subtitle.skill`
（同じ中身を1つにまとめたファイル）をプロフィールに保存すれば、どのチャットでも使えます。

スキルだけを渡した事前知識なしの Claude に「悪だくみ」（3本連結）と「電話にでないと…」
（1本・768x1344）を一から作らせ、どちらも正解（並び順・全セリフ・話者の色・心の声・
時刻の補正・幻聴の除外・元ファイル無傷など）と一致することを確かめています。

| ファイル | 役割 |
| --- | --- |
| `SKILL.md` | 完成形・作業の流れ・文字起こしと話者判定の判断基準 |
| `references/lessons.md` | 実際に起きた失敗（取りこぼし・幻聴・ずれ・話者の取り違えなど）と見つけ方 |
| `references/desktop-setup.md` | Mac / Windows の準備とエラー対処 |
| `scripts/setup_check.py` | 環境チェック（足りないものの入れ方を OS ごとに表示） |
| `scripts/analyze.py` | 文字起こしの調査（5通りの聞き方を1回で並べる）と区間の聞き直し |
| `scripts/frames.py` | 指定時刻のコマを並べた画像（話者の確認用） |
| `scripts/make_subs.py` | セリフ一覧から字幕（ASS）・SRT・文字起こし txt を生成 |
| `scripts/make_title.py` | タイトル画像の生成 |
| `scripts/render.py` | 連結・タイトル・字幕を1回で書き出して検品 |
| `scripts/deliver.py` | デスクトップへの納品（上書きしない） |

Mac / Windows / Linux で動きます。必要なのは ffmpeg（libass 入り）、Python 3.9 以上、
faster-whisper、Pillow、日本語の太字フォントです（`setup_check.py` が確認と案内をします）。

## 各動画の作業ファイル (`scripts/`)

スキル化する前に、動画ごとに使ったタイトル画像・字幕定義（`subs_*.ass`）・ffmpeg のフィルタ定義です。
新しく作るときはスキルの方を使ってください。
