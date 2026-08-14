# 廃病院 心霊スポット TOP5 — 動画生成パイプライン

ナレーション音声(MP3)+ 字幕(SRT)から、16:9 / 1080p / 30fps の
モーショングラフィックス動画を全自動生成するパイプラインです。

実写素材は使わず、全カットをプロシージャル生成した「動く再現イラスト」
(劇画調シルエット+霧+フィルムグレイン)で構成し、
ファウンドフッテージ風のナイトビジョン演出・キネティックタイポグラフィ・
情報カードをナレーションにフレーム単位で同期させています。

## 構成

```
source/            narration.mp3 / narration.srt / op.mp4 / ed.mp4 (入力)
pipeline/
  common.py        定数・SRTパーサ
  scenes.py        77カットのタイムライン(カメラ・FX・オーバーレイ)
  art_base.py      描画プリミティブ(ノイズ/建物/廊下/人影/グレード)
  art_scenes.py    約50種のシーンビルダー(2688x1512 静止画)
  gen_art.py       静止画一括生成 + コンタクトシート
  subs.py          ASS生成(字幕 + ランク演出 + 情報カード + HUD 等 800+イベント)
  render.py        ffmpeg合成(zoompan/霧/グレイン/スティンガー→連結→焼き込み)
output/
  haibyouin_top5_720p.mp4   720p配布版(リポジトリ同梱)
  haibyouin_top5_16x9.mp4   1080p配布版(約230MB — GitHubの容量制限のため
                            リポジトリには含めず。下記手順で再生成可能)
```

## ビルド手順

```bash
apt-get install -y ffmpeg fonts-noto-cjk fonts-noto-cjk-extra
pip install pillow numpy

cd pipeline
python3 gen_art.py        # シーン静止画 + オーバーレイ生成
python3 subs.py           # build/main.ass 生成
python3 render.py all     # fog/stinger → 77クリップ → 連結 → 最終mux
python3 render.py dist    # 配布版エンコード(1080p軽量化 + 720p 2パス)
python3 render.py attach  # source/op.mp4・ed.mp4 を本編の前後に連結
```

個別リビルド: `python3 gen_art.py <art名>` / `python3 render.py scenes <sceneID>`
→ `python3 render.py concat && python3 render.py final`

## 演出メモ

- カメラ: Ken Burns(ズーム+ドリフト+微ウォブル)/ 手持ち風(高周波ウォブル)
- セクション転換: ホワイトノイズ・スティンガー + ランクカード(数字スラム+色収差)
- 情報系: CASE FILEパネル、統計スラム(1987/負債20億/2007)、年号カウンター、
  日本地図、館内マップ(ホットスポットPing)、リキャップボード
- ホラー演出: 幽霊レイヤーのフェード出現、REC/タイムコードHUD、
  フリッカー、ジョルト(第1位「大きな音」)、赤の強調ワード字幕

---

## プロジェクト2: 日本航空123便 ── 事故と、残された疑問

18分07秒 / 16:9 / 1080p / 30fps。実在の航空事故を扱うため、演出は
調査ドキュメンタリー調(設計図・データ図解・地図・年表)に統一し、
墜落の瞬間や犠牲者を描写しない方針で構成しています。

### 追加ファイル

```
pipeline/
  jal123_art.py     73種の技術図解シーン(747断面、圧力隔壁、接合板比較、
                    飛行経路図、FDR波形、資料カード等)
  jal123_scenes.py  111カットのタイムライン
  jal123_subs.py    819イベントのASS。SRTの音声認識誤変換を補正
                    (--audit で全変更点を出力)
  jal123_audio.py   BGM7曲のセクション割当+ダッキング、SE10点の配置
source/jal123/      narration.mp3 / narration.srt
source/bgm/         BGM 7曲   source/se/  SE 5点
output/jal123_preview_540p.mp4   プレビュー版(リポジトリ同梱)
```

### ビルド

```bash
cd pipeline
PROJ=jal123 python3 gen_art.py
PROJ=jal123 python3 jal123_subs.py
PROJ=jal123 python3 jal123_audio.py
PROJ=jal123 python3 render.py all
PROJ=jal123 python3 render.py dist
PROJ=jal123 python3 render.py attach
```

### 字幕の補正について

入力SRTは音声認識由来の誤変換を多数含むため、焼き込み前に補正しています。
特に「圧力核兵器」は事故原因の用語「圧力隔壁」の誤変換で、そのまま表示すると
誤情報になります。補正は `jal123_subs.py` の FIXES(文脈と航空事実から確定
できるもの)と NEUTRALISED(音声から復元できず、断定を避けて中立表現に
留めたもの)に分けて管理しています。

```bash
PROJ=jal123 python3 jal123_subs.py --audit   # 全変更点の一覧
```

### 音楽の扱い

犠牲者に触れる場面(520人の件 / 「まだ生きていた人がいた」の件)は
意図的に無音とし、他のセクションではナレーションにサイドチェイン
ダッキングした控えめな音量で敷いています。
