# ゲンとモカ — コード100%オープニング（10秒）

動画生成AI・画像生成AI・外部素材を一切使わず、**絵も音もすべてコードで生成**した 10 秒の OP です。

- 完成動画：`out/genmoka_op_code.mp4`（1920×1080 / 30fps / 300フレーム / H.264 CRF16 / AAC 192kbps 48kHz / -16 LUFS）
- 本体：`genmoka_op.html`（映像・音・プレビューUI入り、外部ライブラリなし、フォントは base64 埋め込み、オフライン動作）
- 確認用：`out/review/`（f15/f75/f150/f200/f270 の静止画、コンタクトシート、自己レビューログ）

## 見る

`genmoka_op.html` をブラウザで開くとプレビューモードになります（スマホ縦持ち対応）。
初回はアセット（毛並み・背景）を生成するため数十秒かかります。再生／停止、シークバー（カット境界マーカー付き）、±1フレーム、ループ、音のオンオフ。
PC ではスペースキーで再生、←→ でコマ送り。

## 書き出し（Windows / macOS / Linux 共通）

必要なもの：Node.js 18 以上、Python 3、ffmpeg（`ffmpeg` と `ffprobe` に PATH を通すか、環境変数 `FFMPEG` / `FFPROBE` で指定）

```bash
npm install                         # playwright
npx playwright install chromium     # 初回のみ
pip install fonttools brotli        # フォント埋め込みを作り直すときだけ必要

node export.mjs --review            # 確認用の静止画とコンタクトシート → out/review/
node export.mjs --check             # 決定論チェック（同じフレームを再描画して一致するか）＋カット境界
node export.mjs                     # 全300フレーム + 音声 → out/genmoka_op_code.mp4
```

Windows で ffmpeg を入れる例：`winget install Gyan.FFmpeg`

## 話数タイトルの差し替え

`genmoka_op.html` の先頭にある

```js
const EPISODE_TITLE = '第12話「はじめての落ち葉」';
```

を書き換えて、`python build_fonts.py` を実行してください（使う文字だけをフォントからサブセット化して埋め込み直します。
かな・数字・約物は常に含めているので、漢字を変えたときは必ず再実行）。

## 仕組み（要点）

| 要素 | 実装 |
|---|---|
| 毛並み | 独自のソフトウェア・ラスタライザ。形→距離変換→擬似3D法線→逆光ライティング→毛色マップ（赤胡麻・裏白・タビー）→毛流れ場に沿ったテーパー付きの毛をパーツあたり数万本（Float32 でプリマルチプライド合成） |
| リグ | パーツ単位でオフスクリーンに一度だけ描いてキャッシュし、毎フレームはピボット回転・拡縮で合成。目・まぶた・鼻・ひげは毎フレーム描画。尾はバネ（事前積分） |
| 縁側 | ピクセル単位のレイキャスト（板の木目、柱の影、障子、フレネル反射で庭と夕日が映り込む）＋深度から被写界深度 |
| 庭・空 | Canvas で描いたパノラマ（雲・遠山・紅葉・すすき・灯籠）をカットごとに切り出してぼかし＋丸ボケ |
| 落ち葉・光の粒 | 重力＋空気抵抗＋振り子揺れ＋ノイズ風の擬似物理（固定刻みで事前積分）、粒は時刻の純関数 |
| 文字 | Yuji Syuku（筆）を1文字ずつ縦に配置し金グラデ＋光の走り、Noto Serif JP ExtraLight/Light。fontTools でサブセット→woff2→base64 |
| 音 | Karplus-Strong（都節音階の琴風）、FM の鈴、帯域ノイズの風、和音＋パッド、合成インパルス応答の畳み込みリバーブ。OfflineAudioContext は直列チェーンで処理し、ミックスは JS で固定順に加算（バイト一致の決定論） |
| 決定論 | `Math.random` / `Date` / `performance.now` は不使用。乱数はシード付き mulberry32（アセット名ごとに独立）、ノイズは自前実装 |

フォント：Yuji Syuku、Noto Serif JP（SIL Open Font License 1.1、`fonts/OFL_*.txt`）
