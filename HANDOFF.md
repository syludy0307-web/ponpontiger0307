# 引継ぎ書：フィリピン法律TikTokショート制作パイプライン

新スレッドはまずこのファイルを読むこと。ここまでの全context・制作システム・ユーザーの好みを記載。

## 0. 一言でいうと

ユーザー（日本語話者）がフィリピンの法律解説TikTokシリーズを制作中。毎回「台本＋ナレーションmp3＋ASR生成の粗いSRT」を渡してくるので、**誤字修正→タイムライン設計→Canvasレンダラーでフル演出→効果音ミックス→MP4納品→リポジトリにpush** までを一気通貫でやる。**9本完成済み**。

## 1. リポジトリ状態

- リポジトリ: `syludy0307-web/ponpontiger0307`
- ブランチ: **`claude/handoff-md-review-t8kkrs`**（現行の全作業・push先。#1〜8を作った `claude/philippines-adultery-tiktok-cmfhcw` をFFマージして引き継いだ）
- 1動画=1ディレクトリ。完成9本：

| # | ディレクトリ | テーマ | 尺 | 特徴 |
|---|---|---|---|---|
| 1 | philippines-adultery | 姦通罪(333条)/妾罪(334条) | 59.5s | シリーズの原型。チップ蓄積・天秤 |
| 2 | philippines-247 | 刑法247条デスティエロ | 56.0s | 追放マップ・閉じるドア・砂時計 |
| 3 | philippines-ra9262 | RA9262暴力防止法 | 58.0s | **写真合成開始**・7項目連打→束→Wスタンプ |
| 4 | philippines-divorce | 離婚制度なし | 49.5s | 階段図解・投票バー・札束/書類の山 |
| 5 | philippines-bastos | RA11313バワル・バストス法 | 52.5s | 場所タイル2×3・DM通知99+・PAL機オチ |
| 6 | philippines-ra9995 | RA9995盗撮・映像禁止法 | 52.0s | **合成SFX導入**(thump/shatter)・赤無音エンド |
| 7 | philippines-land | 名義貸し土地(Frenzel v. Catito) | 60.0s | **ストーリー型4ハードカット**・shutter合成・NULL AND VOID |
| 8 | philippines-estafa | エスタファ(315条) | 54.5s | **抑制演出版**（金色制限・単発ドン・白プログレスバー） |
| 9 | philippines-ra10175 | RA10175 4条a項1号 不正アクセス | 49.0s | **引っ張り型**（前半白のみ→RGBグリッチで赤解禁）・写真7点・BGM段変更 |

- 各ディレクトリ構成（共通）:
  - `timeline.js` … 単一ソース（sections / subs / sfxキュー / sfxGain）。rendererとmixerが共有
  - `render.html` … 1080×1920 Canvas。`window.renderFrame(t)` が時刻tの完成フレームを描く純関数（決定論的、Date.now/Math.random禁止）
  - `capture.cjs` … Playwrightでフレーム→ffmpegへJPEGパイプ（`--stills 1.0,2.0`でプレビューPNG）
  - `mix.cjs` … 音声ミックス＋最終MP4×2（final=高品質 / tiktok=配信用30MiB以下）
  - `subtitles_fixed.srt` … 誤字修正済みSRT（毎回ユーザーに納品）
  - `assets/` … narration.mp3, sfx_*.mp3/wav, bgm.mp3, (img/ 写真+photos.js+credits.json)
  - `.gitignore` … `preview/` `out/video_silent.mp4` `out/*_final.mp4`（**新規プロジェクトで必ず作る**。#8で忘れてpreviewをコミット→amendで修正した）
- コミット運びは1動画2コミットが基本（パイプライン一式→完成MP4）。**tiktok版のみコミット**（finalは重いのでignore、#1〜3の旧finalは履歴に残ってるが気にしない）

## 2. 環境セットアップ（新コンテナで最初にやる）

```bash
apt-get update && apt-get install -y ffmpeg fonts-noto-cjk fonts-noto-cjk-extra
# Playwright は global 導入済み想定（/opt/node22/lib/node_modules, chromium は PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers）
# 実行は必ず: NODE_PATH=/opt/node22/lib/node_modules node capture.cjs （CJSなのでNODE_PATHが効く）
```

- フォント: `Noto Sans CJK JP`(weight 900=Black), `Noto Serif CJK JP`(900), `Noto Color Emoji`（canvasで絵文字OK、🇵🇭等の旗も出る）
- ネットワークはプロキシ経由。**Wikimedia Commons API/画像は取得可能**（他のストックサイトは不可前提）
- bashのcwdはコマンド間でリセットされることがある。**cdは毎コマンド絶対パスで**

## 3. 制作フロー（次の動画=10本目のレシピ）

1. `mkdir philippines-XXX/assets` → アップロードされたmp3/srtをコピー、**既存プロジェクトからsfx6種+bgm.mp3+capture.cjsをコピー**（#9 philippines-ra10175/assets が全部揃ってる）
2. `ffprobe` でナレーション長を測る → `DUR = ナレーション末尾 + 約1.4s`（60秒以内厳守）
3. SRT誤字修正（§6参照）→ `subtitles_fixed.srt` 作成。キュー結合・アラビア数字化（2024年/131/4年2ヶ月）
4. `timeline.js` 作成：sections（音声で区切る）/ subs（色分けセグメント）/ sfxキュー / sfxGain
5. `render.html` 作成：既存プロジェクトのヘルパー（§4）を流用しシーンだけ書く
6. 写真が合う題材なら `fetch_photos.cjs`（#3,4のをコピーしてWANTS変更）→ resize→base64→photos.js（§5）
7. `--stills` で10枚前後プレビュー → **Readで目視** → レイアウト衝突を直す（毎回2〜3箇所ある）
8. 本番レンダリング（バックグラウンド、1800フレーム≈2分）→ `mix.cjs` 実行
9. 検品：duration / ebur128（-14〜15 LUFS目標）/ 演出特殊箇所のvolumedetect / mp4からフレーム抽出してRead
10. `SendUserFile`（**tiktok版+fixed SRT**、30MiB制限注意）→ README書く → `.gitignore`確認 → commit → push

## 4. ビジュアルシステム（render.htmlの共通言語）

- 色: 赤 `#FF4A3D`(fill #FF3B2F) / 金 `goldGrad()`グラデ / 白 / 縁 `#10131F` / PH色 blue#0E4BC3 red#D6203A yellow#FCD116
- 字幕: 下段 y1568/1620(2行/1行), 64px, 黒縁13px, セグメント色分け `{t:'テキスト',c:'w|r|g|b'}`, 1文字ずつpop+キーワード常時バウンス, 下部黒グラデ
- **全セクションに下段字幕を必ず入れる**（#7で冒頭18秒字幕なし→ユーザー指摘。センター演出と字幕は併用する）
- セーフゾーン: 重要要素 x<950 / 字幕は y1750まで / バッジ y150 / プログレスバー y0-10（金。#8のみ白）
- 主要ヘルパー（どのrender.htmlにもある）: `segText`(文字送りテキスト) / `megaText`(slam/boyon/scalePop) / `pillBlock` / `stampBlock`(赤ハンコ) / `chip・bigChip` / `drawX`(赤✖叩きつけ) / `boyonSc`(ボヨン) / `popIn/elasticIn/outSc` / IMPACTSテーブル(shake+flash+burst+speedlines+confetti) / `drawWipes`(セクション境界の斜めワイプ) / `drawBadge`(上部ピル) / `vignetteGrain`
- 図解資産（過去作からコピー可）: 天秤 / 檻ドロップ(drawBars) / 手錠 / 木槌(slam時刻はT0/T1定数) / 婚姻届・登記簿・判決文 / 階段 / 投票バー / 砂時計 / ドア / 地図+立入禁止円 / スマホDM通知 / 場所タイル / チェックボックス行 / 時系列バー / カード(フリップ・スライド・束)
- 写真: `photoBG`(フルブリード+暗トーン+Ken Burns) / `photoPanel`(角丸パネル+ラベル+クレジット)。※`megaText`をtranslate済みcontext内で使う時は `x:0` を渡す（過去のバグ）

## 5. 写真ワークフロー（権利安全）

- Wikimedia Commons APIで検索→ライセンスが `CC*/Public domain/CC0` のみ採用→`credits.json`に記録
- リサイズ≤1600px → **base64でphotos.jsに埋め込み**（file://のcanvas汚染回避。imgタグ直読みはtoDataURLが死ぬ）
- クレジット焼き込み：パネル右下 or フルブリードは右上小 + エンドカードにまとめ行。PDはクレジット任意
- 実績素材: マカティ夜景(CC0) / 最高裁ファサード(CC BY-SA4.0 Patrickroque01, fy:.16でSUPREME COURT文字が入る) / 国旗(CC BY-SA4.0) / 刑務所鉄条網(CC BY2.0) / 下院本会議場(PD) / マニラ大聖堂(CC BY4.0) / PAL機(CC BY-SA3.0)
- #9で追加: フィリピン共和国紋章 BATAS AT BAYAN(PD/NHCP・条文シーンに強い) / データセンター青ラック(CC BY-SA3.0 BalticServers・サイバー感) / 配線クローゼット(PD) / 牢の鉄格子(CC BY2.0 Matt Brown) / 手錠(CC0) / マニラ夜景(CC BY-SA3.0 Spearminttt) / iPhone実機(CC BY-SA2.0)
- **#9のfetch_photos.cjsが最新版**（keyごとに候補クエリを多段フォールバック / DL後にマジックバイト検証 / `ONLY=phone,keypad` で一部だけ取り直し / base64化まで一括）。Commons APIは連続だと429を返すので候補が多いほど安全
- 検索ワードは当たり外れが大きい。`smartphone in hand` → ポインセチアの赤外線写真、`PIN pad` → ドイツの黒電話、が実際に来た。**必ずモンタージュを作って目視**（ffmpegで個別`-i`＋hstack/vstack。`-pattern_type glob`＋`tile`はサイズ違いで壊れる）
- 人物が特定できる写真はデリケート題材では使わない。台本が図解指定(#8)なら写真なしでOK

## 6. 音声システム

- ナレーション: `loudnorm=I=-15:TP=-1.5:LRA=11`（全体仕上がり-14〜15 LUFS）
- BGM: シリーズ共通 `bgm.mp3`（元-10.9 LUFS）→ **-17.1dB**のベッド。fade in 0.4 / out 2.2（台本指定で無音窓 `volume='if(between(t,A,B),0,1)':eval=frame` や早めfadeも）
- SFX 6種（全て頭出し0秒、adelayでキュー配置。gain実測ベース）:
  - `sfx_decision.mp3` 鉄琴ピコッ=テロップ出現 gain .40
  - `sfx_ashika.mp3` アシカ2=強調キメ gain .62
  - `sfx_boyon.mp3` ボヨン=ツッコミ gain .33（シリアス回は0でも可）
  - `sfx_thump.wav` 低音のドン（合成52Hz）gain 1.5
  - `sfx_shatter.wav` ガラス割れ（合成）gain .35
  - `sfx_shutter.wav` シャッター/カチッ（合成）gain .40
- mix.cjsはtimeline.jsのtypes配列を回す汎用実装。**参照する入力ファイルは全部assetsに置く**（キュー0件でも）
- 配信用: `crf21 maxrate3500-3600k` で30MiB以下に（SendUserFileの上限。超えたら再エンコード）

## 7. SRT修正の頻出パターン（毎回必ず全文チェック）

貫通罪→姦通罪 / 商材・妾罪 / ネタだけ→寝ただけ / 聞こんな→既婚の / ra九千九百九十五→RA9995 / バーチカン四国→バチカン市国 / 履行→離婚 / 簡易→下院 / 乗員→上院 / 人気切れで敗案→任期切れで廃案 / 口紅→口笛 / バールバスト四→バワル・バストス法 / 初版→初犯 / 重厚→受講 / 契機→刑期 / 外人→外国人 / 向こう→無効 / 名義菓子→名義貸し / 七円→7年 / 聖烈→成立 / 学位→学費 / 返済→転載 / 貸される→科される / 性交流→性行為 / 手元を結び見た→手元を盗み見た / ケイは六年一日→刑は6年1日 / 四条a一号→4条a項1号 など。**法律用語・数字は特に注意**

判断ルール（#9で確立）: **ASRが自然な日本語を出していて台本と意味が同じならASR準拠**（音声と字幕を一致させる方が優先。例「許可じゃない」台本 vs「許可ではない」ASR → ASR採用）。**壊れている／法律用語・数字を誤変換している場合は台本・正表記に修正**。意味が変わる箇所は台本準拠（例「スマホを見た」ASR → 「スマホを開けた」台本。後半の「開いた時点で終わり」に接続するため）

## 8. ユーザーの好み・作法（重要）

- 日本語でテンション高めのやり取り（絵文字OK）。フィードバックは「完璧！」or 具体的修正1-2点。修正は即やる
- 台本に**演出指定がある場合は厳守**（#7の4カット/無音→ドン、#8の金色禁止・強調禁止・赤フラッシュ1回など）。制作メモの⚠は絶対
- 台本にない言葉は画面に出さない（意訳テロップは最小限）。伏せ字（〇して/〇傷）は台本の表記に従う
- タイトル案・概要欄文言はユーザーの台本にあることが多い→納品時に添えてあげる
- 顔出し指定は無視してOK（素材が音声のみなので全編モーショングラフィックス）
- 毎回納品物: **tiktok版mp4 + subtitles_fixed.srt** をSendUserFile、リポジトリにpush、返信に構成サマリ
- stop-hookが「untracked files」と言ってくる→各動画完成時にちゃんとcommit+pushすれば黙る

## 9. 既知のハマりどころ

- `capture.cjs`はCJS。`NODE_PATH=/opt/node22/lib/node_modules` 必須
- bashのcwdリセット→絶対パスでcd
- レンダリングは`run_in_background`で回して通知を待つ（sleep禁止）
- プレビューは自分の目で必ずRead（毎回レイアウト衝突が2〜3ある：字幕帯y1440以下と図解の重なり、右端x950超え、translate済みmegaTextのx:0忘れ）
- 新プロジェクトに`.gitignore`を最初に置く
- assetsのsfxは6種全部コピー（mix.cjsが全入力を開く）
