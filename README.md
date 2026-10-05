# 踊るフィリピン豆知識 #03「フィリピンのクリスマス、お年玉は誰から？」

ダンス動画にクイズ形式のテロップを重ねる、TikTok 向け縦型ショートの編集プロジェクトです(Remotion + React)。
#03 で伝える内容は1つだけ:「フィリピンの子どもはクリスマスに、**名付け親**(ninong・ninang)から **aguinaldo**(お金や贈り物)をもらう」。

## 完成品の仕様

| 項目 | 値 |
| --- | --- |
| ファイル | `output/philippines_godparent_money_dance_15s.mp4`(`src/config.ts` の `output.file`) |
| 画面 | 1080×1920(9:16)/ 30fps |
| 映像 | H.264(High)/ yuv420p / CRF 18 / faststart |
| 音声 | 元動画の音声をそのまま AAC 192kbps(BGM・効果音・ナレーションの追加なし) |
| 尺 | 15.00秒 = 450フレーム(エンドカードなし。素材が15.1秒で5秒を足す余地がないため) |

尺は素材の長さから自動で決まります。素材が足りる場合は `trimStartSeconds` から「450 フレーム(+ エンドカード)」、
短い場合はループや静止画で水増しせず、素材の終わりで止めます(書き出し時に `[尺不足]` と表示)。

## 必要なもの

- Node.js 18 以上(動作確認は 22)
- FFmpeg の別途インストールは不要(Remotion に同梱のものを使います)
- 初回の書き出し時に、Remotion が描画用の Chrome Headless Shell(約90MB)を自動でダウンロードします

## 使い方

```bash
npm install
# ダンス動画を public/input/ に置き、src/config.ts の video.src をそのファイル名にする
# (#03 は public/input/ep03.mp4。元ファイルは上書きされません)

npm run studio   # ブラウザでプレビュー・微調整(Remotion Studio)
npm run stills   # 確認用プレビュー画像 → output/previews/
npm run render   # 完成動画 → output/philippines_godparent_money_dance_15s.mp4
```

> **書き出しは必ず `npm run render` を使ってください。**
> `npx remotion render` を単体で使うと、Remotion 内部の AAC 変換の仕様で音声が約43ms遅れます(下の「制作メモ」参照)。

プレビュー画像(`npm run stills`)は次の時点です。

| ファイル | 時点 | 確認すること |
| --- | --- | --- |
| `preview_01_quiz_1.0s.png` | 1.0秒 | 質問の読みやすさ |
| `preview_02_answer_4.4s.png` | 4.4秒 | 答えと集中線の見え方(#03 は答えが 4.13秒に出るので、集中線が消えていく途中) |
| `preview_03_explain_9.0s.png` | 9.0秒 | 解説の綴りと配色 |
| `preview_04_recap_13.0s.png` | 13.0秒 | 復習テロップの配置 |
| `preview_05_endcard_17.5s.png` | 17.5秒 | エンドカード(エンドカードがある回だけ) |

任意のフレームも書き出せます: `node scripts/stills.mjs 127` → `output/previews/extra/frame_127.png`(127 = 4.23秒、#03 で集中線が一番広がる瞬間)

## 設定の変え方(`src/config.ts`)

再編集に必要な値はすべて `src/config.ts` にまとめてあります。次のエピソードもここを書き換えるだけで作れます。

| 変えたいもの | 項目 |
| --- | --- |
| 入力動画のパス | `video.src`(`public/` からの相対パス) |
| 使用区間の開始位置 | `video.trimStartSeconds`(秒) |
| 書き出し先のファイル名 | `output.file` |
| テロップ文言・強調色を付ける部分 | `texts`(部分ごとに `highlight` / `bounce` / `underline` を指定) |
| 答えの横のアイコン | `answerIcon`(`'calendar'` / `'parol'` 星形ランタン / `'toilet'` トイレ案内 / `'none'`) |
| エンドカード | `endCard`(`enabled` で付け外し、`seconds` 長さ、`label` / `club` / `name` 文言、`top` 位置) |
| シーンの切り替えフレーム | `scenes`(30fps。4秒 = 120) |
| 文字サイズ | `fontSize` |
| テロップ位置・シリーズ名の位置 | `layout`(`captionTop`, `centerX`, `seriesLabel`, `iconSize` など) |
| 「正解は…」の置き方 | `layout.answerLabel`(`'stacked'` 答えの上の行 / `'vertical'` 答えの左に小さく縦書き) |
| クイズ横の「？」の数 | `layout.questionMarks`(`'both'` 左右に2つ / `'left'` 左に1つ) |
| 色 | `colors`(強調色は `highlight`、エンドカードの金色は `goldLight` / `gold` / `goldDeep`) |
| 動きの長さ | `motion`(キーワードの弾み、答えのポップ、集中線、下線) |

1行が `layout.maxLineWidth`(720px)を超える文言にすると、はみ出さないよう自動で縮小します。
フォントは常用の日本語(CP932 範囲 7,631 字)を収録しているので、次回以降の文言でも文字化けしません。

## タイムライン(#03、30fps)

| 時間 | フレーム | テロップ | 演出 |
| --- | --- | --- | --- |
| 0.00〜4.13秒 | 0〜123 | フィリピンの**クリスマス** / お年玉は**誰**から？ | 1フレーム目から表示。「誰」だけ最初の0.25秒で弾む。左に小さな「？」が揺れて静止 |
| 4.13〜7.50秒 | 124〜224 | 正解は…(縦書き) **名付け親！** | 4.13秒の強い拍に合わせて登場。「名付け親！」を 85%→108%→100%(0.2秒)、背後に集中線 0.35秒 |
| 7.50〜11.50秒 | 225〜344 | **aguinaldo** / ＝名付け親からのお金や贈り物 | 「aguinaldo」だけ黄色。下に黄色い下線を 0.25秒で左→右 |
| 11.50〜15.00秒 | 345〜449 | **名付け親**の**お年玉** / 知ってた？ | 登場時だけ軽くポップ、その後は最後まで静止 |

太字は黄色(強調色)。ダンス映像は全編で1本を連続再生しています(シーンごとの再スタート・速度変更・反転・フリーズなし)。
シリーズ名「踊るフィリピン豆知識 #03」は左下に小さく固定表示しています。

## ファイル構成

```
src/
  config.ts              … 編集用の設定(ここだけ触れば OK)
  Root.tsx               … コンポジション登録。素材の長さから尺を自動計算
  DanceTrivia.tsx        … 本体(最下層にダンス動画 → 上にテロップ類 → 最後にエンドカード)
  scenes/                … 4シーン(Quiz / Answer / Explain / Recap)
  components/            … 縁取り文字、集中線、アイコン(カレンダー・パロル・トイレ)、「？」、シリーズ名、エンドカード
  animation.ts, fonts.ts
scripts/
  render.mjs             … 完成動画の書き出し(映像 → 元音声の合成 → faststart 確認)
  stills.mjs             … プレビュー画像の書き出し
  build_fonts.py         … 同梱フォント(日本語サブセット)の作り方
public/
  fonts/                 … Noto Sans CJK JP Black / Bold(サブセット)、Playfair Display Bold(いずれも SIL OFL 1.1)
  input/                 … 素材置き場(動画は .gitignore 済み)
output/
  caption.txt            … 投稿文
  *.mp4, previews/       … 書き出し結果(.gitignore 済み)
```

## エピソードの履歴

各回の文言・レイアウトは git のコミットに残っています。昔の回を作り直すときは、そのコミットの `src/config.ts` を使ってください。

| 回 | テーマ | 素材 | 尺 | コミット |
| --- | --- | --- | --- | --- |
| #01 | フィリピンのクリスマスはいつから？ → 9月！ | `public/input/dance.mp4` | 14.07秒 | `d673afb` |
| #02 | フィリピンのクリスマスはいつ終わる？ → 1月！(+ エンドカード) | `public/input/ep02.mp4` | 20.00秒 | `2f70a64` |
| #03 | フィリピンのクリスマス、お年玉は誰から？ → 名付け親！ | `public/input/ep03.mp4` | 15.00秒 | このコミット |
| (未使用) | CR って何？ → トイレ！ | 別の場所で撮った動画なら流用可 | — | `a897def` |

## 制作メモ

- **ネタの出典(#03)**: The Philippine Star「Namamasko po: Christmas scenarios we can all relate to」
  (aguinaldo を渡すことは名付け親の文化の一部で、ninong・ninang から贈り物をもらう、と明記)
  https://www.philstar.com/news-commentary/2015/12/24/1536217/namamasko-po-christmas-scenarios-we-can-all-relate-to
  aguinaldo が「お金や贈り物」(封筒入りのことが多い)である点は Wikipedia「Christmas in the Philippines」で確認。
- **拍合わせ(#03)**: 4.13秒に曲の上位1%に入る強い打音(拍の位置)があるため、指示書の「4秒付近 ±0.2秒以内」の範囲で、
  答えの登場を 4.00秒 → 4.13秒に合わせています。#01・#02 は明確なアクセントが無く 4.00秒のまま。
- **テロップの位置**: 素材の全フレームで顔と手の位置を検出し(MediaPipe)、テロップを頭上の帯(y≈188〜)に置いています。
  #03 は 5.6〜6.2秒に人物が前に乗り出して額が y≈398 まで上がるため、答えの「正解は…」を答えの左に小さく縦書きにして
  1段に収めました(2段だと額に重なる)。書き出し後、全450フレームでテロップが顔から30px以上離れていること、
  頭上の帯で手と重ならないこと、TikTok の透かし(前半は左中央・後半は右下)と重ならないことを確認しました。
  質問の行が長いので、「？」は左に1つだけです(右に置くと右端の余白に入るため)。
- **配置ガイド**: テロップの文字は上端180px・下端360px・右端180pxの内側、左端80px以上に収まっています
  (本作品の目安であり、プラットフォーム公式のセーフゾーンではありません)。#03 は答えが横に長いため、
  飾りの集中線だけが 0.35秒間、右と上の余白に少しかかります(文字はかかりません)。
- **エンドカード**: `endCard.enabled` で付け外しできます。素材が「15秒 + エンドカードの秒数」以上ある回だけ付けられます。
- **音声**: Remotion は内部で AAC を ADTS 形式で作るため、先頭のプライミング情報が失われ、
  元動画より 2048 サンプル(約43ms)遅れます。`npm run render` は映像を音声なしで書き出した後、
  元動画の音声を同じ区間で AAC 化して合わせるので、ズレは 0 です(相互相関で確認)。
- **フォント**: Noto Sans CJK JP(Noto Sans JP 相当)の Black / Bold を同梱(`public/fonts/OFL.txt`)。
  エンドカードの店名は Playfair Display Bold(`public/fonts/OFL-PlayfairDisplay.txt`)。
- **Remotion のライセンス**: 個人・従業員3人以下の会社・非営利団体は無料(商用可)。
  それ以上の規模の会社は有料ライセンスが必要です(`node_modules/remotion/LICENSE.md`)。
