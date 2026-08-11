# 廃病院 心霊スポット TOP5 — 動画生成パイプライン

ナレーション音声(MP3)+ 字幕(SRT)から、16:9 / 1080p / 30fps の
モーショングラフィックス動画を全自動生成するパイプラインです。

実写素材は使わず、全カットをプロシージャル生成した「動く再現イラスト」
(劇画調シルエット+霧+フィルムグレイン)で構成し、
ファウンドフッテージ風のナイトビジョン演出・キネティックタイポグラフィ・
情報カードをナレーションにフレーム単位で同期させています。

## 構成

```
source/            narration.mp3 / narration.srt (入力)
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
