# 踊るフィリピン豆知識 #01「フィリピンのクリスマスはいつから？」

ダンス動画にクイズ形式のテロップを重ねる、TikTok 向け縦型ショートの編集プロジェクトです(Remotion + React)。
伝える内容は1つだけ:「フィリピンのクリスマスシーズンは **9月** から。“**ber**” が付く月(September〜December)がクリスマスシーズン」。

## 完成品の仕様

| 項目 | 値 |
| --- | --- |
| ファイル | `output/philippines_christmas_dance_15s.mp4`(`src/config.ts` の `output.file`) |
| 画面 | 1080×1920(9:16)/ 30fps |
| 映像 | H.264(High)/ yuv420p / CRF 18 / faststart |
| 音声 | 元動画の音声をそのまま AAC 192kbps(BGM・効果音・ナレーションの追加なし) |
| 尺 | 目標 15.00秒 = 450フレーム。**今回の素材は 14.09秒しかないため 14.07秒(422フレーム)** |

尺は素材の長さから自動で決まります。素材が15秒以上なら `trimStartSeconds` から 450 フレーム(15.00秒)、
短い場合はループや静止画で水増しせず、素材の終わりで止めます(書き出し時に `[尺不足]` と表示)。

## 必要なもの

- Node.js 18 以上(動作確認は 22)
- FFmpeg の別途インストールは不要(Remotion に同梱のものを使います)
- 初回の書き出し時に、Remotion が描画用の Chrome Headless Shell(約90MB)を自動でダウンロードします

## 使い方

```bash
npm install
# ダンス動画を public/input/dance.mp4 に置く(元ファイルは上書きされません)

npm run studio   # ブラウザでプレビュー・微調整(Remotion Studio)
npm run stills   # 確認用プレビュー画像4枚 → output/previews/
npm run render   # 完成動画 → output/philippines_christmas_dance_15s.mp4
```

> **書き出しは必ず `npm run render` を使ってください。**
> `npx remotion render` を単体で使うと、Remotion 内部の AAC 変換の仕様で音声が約43ms遅れます(下の「制作メモ」参照)。

プレビュー画像(`npm run stills`)は次の4時点です。

| ファイル | 時点 | 確認すること |
| --- | --- | --- |
| `preview_01_quiz_1.0s.png` | 1.0秒 | 質問の読みやすさ |
| `preview_02_answer_4.4s.png` | 4.4秒 | 答えとパロルのアイコン(集中線は 4.00〜4.35秒で消えた後) |
| `preview_03_explain_9.0s.png` | 9.0秒 | September の綴りと配色 |
| `preview_04_recap_13.0s.png` | 13.0秒 | 復習テロップの配置 |

任意のフレームも書き出せます: `node scripts/stills.mjs 124` → `output/previews/extra/frame_124.png`(124 = 4.13秒、集中線が出ている瞬間)

## 設定の変え方(`src/config.ts`)

再編集に必要な値はすべて `src/config.ts` にまとめてあります。次のエピソードもここを書き換えるだけで作れます。

| 変えたいもの | 項目 |
| --- | --- |
| 入力動画のパス | `video.src`(`public/` からの相対パス) |
| 使用区間の開始位置 | `video.trimStartSeconds`(秒) |
| 書き出し先のファイル名 | `output.file` |
| テロップ文言・強調色を付ける部分 | `texts`(部分ごとに `highlight` / `bounce` / `underline` を指定) |
| 答えの横のアイコン | `answerIcon`(`'parol'` 星形ランタン / `'toilet'` トイレ案内 / `'none'`) |
| シーンの切り替えフレーム | `scenes`(30fps。4秒 = 120) |
| 文字サイズ | `fontSize` |
| テロップ位置・シリーズ名の位置 | `layout`(`captionTop`, `centerX`, `seriesLabel`, `iconSize` など) |
| 強調色・縁取り色 | `colors`(強調色は `highlight`) |
| 動きの長さ | `motion`(キーワードの弾み、答えのポップ、集中線、下線) |

1行が `layout.maxLineWidth`(720px)を超える文言にすると、はみ出さないよう自動で縮小します。
フォントは常用の日本語(CP932 範囲 7,631 字)を収録しているので、次回以降の文言でも文字化けしません。

## タイムライン(30fps)

| 時間 | フレーム | テロップ | 演出 |
| --- | --- | --- | --- |
| 0.00〜4.00秒 | 0〜119 | フィリピンの**クリスマス**は / **いつ**から？ | 1フレーム目から表示。「いつ」だけ最初の0.25秒で弾む。小さな「？」2つが揺れて静止 |
| 4.00〜7.50秒 | 120〜224 | 正解は… / **9月！** | 「9月！」を 85%→108%→100%(0.2秒)。背後に集中線 0.35秒。横にパロル(星形ランタン) |
| 7.50〜11.50秒 | 225〜344 | Septem**ber** / **ber**が付く月はクリスマス | 「ber」だけ黄色。下に黄色い下線を 0.25秒で左→右 |
| 11.50秒〜最後 | 345〜421 | **9月**から**クリスマス** / 知ってた？ | 登場時だけ軽くポップ、その後は最後まで静止(今回は素材の都合で 2.57秒) |

太字は黄色(強調色)。ダンス映像は全編で1本を連続再生しています(シーンごとの再スタート・速度変更・反転・フリーズなし)。
左上にシリーズ名「踊るフィリピン豆知識 #01」を小さく固定表示しています。

## ファイル構成

```
src/
  config.ts              … 編集用の設定(ここだけ触れば OK)
  Root.tsx               … コンポジション登録。素材の長さから尺を自動計算
  DanceTrivia.tsx        … 本体(最下層にダンス動画 → 上にテロップ類)
  scenes/                … 4シーン(Quiz / Answer / Explain / Recap)
  components/            … 縁取り文字、集中線、パロル・トイレのアイコン、「？」、シリーズ名
  animation.ts, fonts.ts
scripts/
  render.mjs             … 完成動画の書き出し(映像 → 元音声の合成 → faststart 確認)
  stills.mjs             … プレビュー画像の書き出し
  build_fonts.py         … 同梱フォント(サブセット)の作り方
public/
  fonts/                 … Noto Sans CJK JP Black / Bold(サブセット, SIL OFL 1.1)
  input/                 … 素材置き場(動画は .gitignore 済み)
output/
  caption.txt            … 投稿文
  *.mp4, previews/       … 書き出し結果(.gitignore 済み)
```

## 制作メモ

- **ネタの出典**: SBS Food「A very Filipino Christmas: Early starts, pigs and plenty of flan」
  (“ber” months = September〜December に入るとクリスマスが始まる、と明記)
  https://www.sbs.com.au/food/article/a-very-filipino-christmas-early-starts-pigs-and-plenty-of-flan/k9c0mr98a
- **ネタの差し替え**: 最初は「CRって何？(Comfort Room = トイレ)」で制作しましたが、素材がトイレで踊る映像のため、
  人物をいじっているように見えかねないと判断してこのネタに変更しました。CR 版の文言はコミット `a897def` に残っていて、
  `answerIcon: 'toilet'` でトイレのピクトグラムも使えます(別の場所で撮った動画なら流用可)。
- **テロップの位置**: 素材の全フレームで顔と手の位置を検出し(MediaPipe)、完成画面上で
  顔は y≈504〜1137、手は y≈769 より下にしか来ないことを確認。テロップは頭上の帯(y≈186〜501)に置き、
  書き出し後に全422フレームで「顔・手・TikTok の透かしとテロップが重ならない」ことを確認しました。
  冒頭0〜0.4秒だけ人物が前かがみになり、質問の2行目が髪の上端に重なります(顔には重なりません)。
- **配置ガイド**: テロップは上端180px・下端360px・右端180pxの内側、左端80px以上に収まっています
  (本作品の目安であり、プラットフォーム公式のセーフゾーンではありません)。
- **拍合わせ**: 4秒付近(3.8〜4.2秒)に明確な音のアクセントが無かったため、答えは指定どおり 4.00秒に出しています。
- **音声**: Remotion は内部で AAC を ADTS 形式で作るため、先頭のプライミング情報が失われ、
  元動画より 2048 サンプル(約43ms)遅れます。`npm run render` は映像を音声なしで書き出した後、
  元動画の音声を同じ区間で AAC 化して合わせるので、ズレは 0 です(相互相関で確認)。
- **フォント**: Noto Sans CJK JP(Noto Sans JP 相当)の Black / Bold を同梱。ライセンスは `public/fonts/OFL.txt`。
- **Remotion のライセンス**: 個人・従業員3人以下の会社・非営利団体は無料(商用可)。
  それ以上の規模の会社は有料ライセンスが必要です(`node_modules/remotion/LICENSE.md`)。
