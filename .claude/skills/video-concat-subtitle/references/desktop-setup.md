# デスクトップでの準備とトラブル対処

まず `python <スキル>/scripts/setup_check.py` を実行し、足りないと言われたものだけ入れます。
入れる前にユーザーに「〇〇を入れてもいいですか」と一言確認してください（PC にソフトを入れる操作なので）。
入れ終わったら、もう一度 setup_check.py を実行して「準備OK」を確認します。

## Mac

1. **Homebrew**（無ければ）: https://brew.sh のトップにある1行コマンドをターミナルで実行
2. **ffmpeg**: `brew install ffmpeg`
   - setup_check が「libass: なし」と言ったら、字幕を焼き込めない版です。
     `brew install ffmpeg-full` を試し、それで無理なら
     `brew tap homebrew-ffmpeg/ffmpeg && brew install homebrew-ffmpeg/ffmpeg/ffmpeg`
   - 入れ替えても古い ffmpeg を拾うときは、環境変数 `FFMPEG_BIN` / `FFPROBE_BIN` に
     新しい方のフルパスを入れて実行する（スクリプトはこの変数を最優先で見る）
3. **Python のパッケージ**（専用の環境を作る）:
   ```
   python3 -m venv ~/video-tools-venv
   ~/video-tools-venv/bin/pip install faster-whisper Pillow
   ```
   以降はすべて `~/video-tools-venv/bin/python <スキル>/scripts/xxx.py` で実行する。
   Homebrew の python に直接 `pip install` すると `externally-managed-environment` で断られるため
4. **フォント**（任意）: `brew install --cask font-noto-sans-cjk-jp`
   入れなくてもヒラギノ角ゴシックで動きます。これまでの完成品と見た目を揃えたいなら入れる

## Windows

1. **ffmpeg**: `winget install --id Gyan.FFmpeg -e`
   入れた直後は PATH に載らないことがありますが、スクリプトは WinGet の置き場所も探します
2. **Python**（無ければ）: `winget install --id Python.Python.3.12 -e`
3. **Python のパッケージ**（専用の環境を作る）:
   ```
   py -m venv %USERPROFILE%\video-tools-venv
   %USERPROFILE%\video-tools-venv\Scripts\pip install faster-whisper Pillow
   ```
   以降はすべて `%USERPROFILE%\video-tools-venv\Scripts\python <スキル>\scripts\xxx.py` で実行する
4. **フォント**（任意）: https://fonts.google.com/noto/specimen/Noto+Sans+JP からダウンロードし、
   zip の中の `static/NotoSansJP-Bold.ttf` を右クリック →「インストール」。
   入れなくても游ゴシック / メイリオで動きます

## よくあるエラー

| 症状 | 原因と対処 |
|---|---|
| `externally-managed-environment` | システムの Python に直接 pip しようとした。上の手順で専用の環境（venv）を作る |
| `No such filter: 'subtitles'` / libass: なし | 字幕を焼き込めない ffmpeg。libass 入りの版に入れ替える（上の Mac / Windows の手順） |
| ffmpeg が見つからない（winget の直後） | 新しいターミナルを開くか、`FFMPEG_BIN` にフルパスを入れる |
| 字幕が □（豆腐）になる・違う書体になる | 日本語フォントが見つかっていない。setup_check の「フォント」行を確認。特定のファイルを使わせたいときは環境変数 `JP_FONT` にフォントファイルのパスを入れる |
| デスクトップが見つからない | OneDrive にデスクトップが移っていることがある。`deliver.py --to <フォルダ>` で直接指定するか、ユーザーに置き場所を聞く |
| 文字起こしがとても遅い | CPU だと 45秒の動画でも数分かかるのは普通。NVIDIA の GPU があれば `analyze.py scan ... --device cuda`（CUDA と cuDNN が必要。無理に入れなくてよい） |
| 初回だけ極端に遅い | Whisper のモデル（large-v3 で約3GB）をダウンロードしている。2回目からは速い |

## クラウド版（Claude Code on the web）で使うとき

- コンテナは作り直されることがあり、そのたびに ffmpeg やフォントが消えます。setup_check で確認し、
  Linux の手順（`apt-get install -y ffmpeg fonts-noto-cjk` と `pip install faster-whisper Pillow`）で入れ直す
- デスクトップはありません。完成品はファイル送付のツールで渡します
- アップロードされたファイルはコピーなので消しても原本はユーザーの手元に残りますが、
  消した後に直しが入ると作り直せないので、片付けはやはり確認が済んでから
