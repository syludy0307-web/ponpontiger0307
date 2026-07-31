# フィリピンの浮気罪ショート動画（約60秒 / 1080x1920 / 30fps）

TikTok向け縦型ショート。Canvas + Playwright(Chromium) でフレームを決定論的に描画し、
ffmpeg で H.264 エンコード → ナレーション + 効果音をミックスして MP4 を出力する。

## 構成

| ファイル | 役割 |
|---|---|
| `timeline.js` | 字幕・テロップ・SFXキューの単一ソース（renderer と mixer で共有） |
| `render.html` | 1080x1920 Canvas レンダラー。`renderFrame(t)` が時刻 t の完成フレームを描く |
| `capture.cjs` | Playwright でフレームを回して ffmpeg にパイプ（`--stills t1,t2` でプレビュー静止画） |
| `mix.cjs` | ナレーション loudnorm(-15 LUFS) + SFX 22発を合成し、無音動画と結合して最終MP4 |
| `assets/` | ナレーション・効果音・元SRT |
| `subtitles_fixed.srt` | 誤字修正 + キュー結合済みSRT（貫通罪→姦通罪、商材→妾罪 など） |

## ビルド手順

```bash
NODE_PATH=/opt/node22/lib/node_modules node capture.cjs   # → out/video_silent.mp4
node mix.cjs                                              # → out/philippines_adultery_final.mp4
```

## 効果音の使い分け（timeline.js の sfx）

- `decision`（decision28 鉄琴・生演奏）… テロップがピコッと出る通常ポップ ×13
- `ashika`（カリフォルニアアシカ2）… 強調キメ（逮捕 / 1回でアウト / 最長6年 / 離婚制度なし）×5
- `boyon`（ボヨン）… ツッコミ（ほぼ捕まらない / 寝ただけセーフ / 刑務所ナシ / マシだろう）×4

## 演出メモ

- セクション: フック(国旗) → 刑法333条(法廷/木槌) → 刑法334条(天秤) → 落とし穴(ハザード) → 結論(檻)
- 字幕は1文字ずつポップ、キーワードは赤/金で常時バウンス
- キメテロップはスラム/ボヨン/スタンプの3種イン + 画面シェイク + 集中線 + 紙吹雪
- 台本上の「顔出し」パート(フック/落とし穴/結論)はセンター大文字のキネティックタイポ構成
