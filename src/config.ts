/**
 * 踊るフィリピン豆知識 #01「CRって何？」— 編集用の設定ファイル
 *
 * 素材・区間・文言・切り替えタイミング・文字サイズ・位置・色は、すべてここで変更できます。
 * 座標はすべて 1080x1920 の完成画面上の px です。
 */

/** テロップ1行を「部分」ごとに書く。部分ごとに色や動きを付けられます */
export type Segment = {
  text: string;
  /** 強調色(黄色)にする */
  highlight?: boolean;
  /** 登場直後に軽く弾ませる(クイズの「CR」) */
  bounce?: boolean;
  /** 黄色い下線を左から右へ引く(略語説明の「C」「R」) */
  underline?: boolean;
};
export type RichLine = Segment[];

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

export const config = {
  video: {
    /** 入力動画(public/ からの相対パス)。元ファイルは上書きしません */
    src: 'input/dance.mp4',
    /** 使用区間の開始位置(秒)。区間指定がなければ 0 = 先頭から */
    trimStartSeconds: 0,
    /**
     * 目標の尺: 15.00秒 = 450フレーム。
     * 素材がそれより短い場合は、ループや静止画で水増しせず「素材の長さ」で止めます。
     */
    targetDurationInFrames: 450,
    /** 元動画の音量(1 = そのまま) */
    volume: 1,
  },

  /** 各シーンの開始フレーム(30fps)。シーンは次のシーンの開始直前まで表示 */
  scenes: {
    quiz: 0, // 0.00秒  クイズ
    answer: 120, // 4.00秒  答え
    abbr: 225, // 7.50秒  略語の意味
    recap: 345, // 11.50秒 復習と締め(最後のフレームまで)
  },

  texts: {
    series: {title: '踊るフィリピン豆知識', episode: '#01'},
    quiz: {
      line1: [{text: 'フィリピンで見かける'}] as RichLine,
      line2: [{text: '『'}, {text: 'CR', highlight: true, bounce: true}, {text: '』って何？'}] as RichLine,
    },
    answer: {
      line1: [{text: '正解は…'}] as RichLine,
      line2: [{text: 'トイレ！', highlight: true}] as RichLine,
    },
    abbr: {
      line1: [
        {text: 'C', highlight: true, underline: true},
        {text: 'omfort '},
        {text: 'R', highlight: true, underline: true},
        {text: 'oom'},
      ] as RichLine,
      line2: [{text: 'の略です'}] as RichLine,
    },
    recap: {
      line1: [{text: 'CR', highlight: true}, {text: ' ＝ '}, {text: 'トイレ', highlight: true}] as RichLine,
      line2: [{text: '知ってた？'}] as RichLine,
    },
  },

  /** 文字サイズ(px) */
  fontSize: {
    series: 32, // シリーズ名 30〜36
    sub: 58, // 補足文 48〜60(「フィリピンで見かける」「正解は…」「の略です」)
    main: 100, // 質問・英語表記・復習 76〜100
    answer: 146, // 「トイレ！」130〜150(動画内で最大)
    recapSub: 76, // 「知ってた？」(復習より少し小さく)
    questionMark: 66, // クイズ横の「？」
  },

  layout: {
    /**
     * テロップの上端 Y。人物の頭上の空き(y≈190〜460)に収める位置。
     * 素材の顔位置を解析した結果、この帯は顔・手・透かしと重ならない
     */
    captionTop: 246,
    /** テロップの中心 X */
    centerX: 540,
    /** 1行の最大幅。超えたら自動で縮小(centerX ± 360 = 180〜900 で右端180pxの余白を守る) */
    maxLineWidth: 720,
    /** 行間(px) */
    lineGap: 4,
    /** 下線付きの行(Comfort Room)の下に足す余白(px) */
    underlineExtraGap: 20,
    /** 行の高さ(文字サイズに対する倍率) */
    lineHeight: 1.14,
    /** シリーズ名の位置(左上の余白) */
    seriesLabel: {left: 80, top: 186},
    /** トイレ案内ピクトグラムの一辺(px) */
    pictogramSize: 128,
    /** 「トイレ！」とピクトグラムの間隔(px) */
    pictogramGap: 30,
  },

  colors: {
    text: '#FFFFFF',
    highlight: '#FFE600',
    outline: '#000000',
    /** 文字の下に落とす薄い影 */
    shadow: 'rgba(0, 0, 0, 0.45)',
    /** シリーズ名の下に敷く半透明の小さな帯 */
    seriesBand: 'rgba(0, 0, 0, 0.5)',
  },

  /** 縁取りの太さ(文字サイズに対する割合) */
  outlineRatio: 0.1,

  /** アニメーション(フレーム数は 30fps 換算) */
  motion: {
    crBounceFrames: 7.5, // 「CR」を弾ませる長さ 0.25秒
    answerPop: {from: 0.85, peak: 1.08, frames: 6}, // 85% → 108% → 100% を 0.2秒
    speedLinesFrames: 10.5, // 集中線 0.35秒
    underlineFrames: 7.5, // 下線が伸びる長さ 0.25秒
  },
};
