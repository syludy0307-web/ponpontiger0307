import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

/** テロップ用フォント: Noto Sans CJK JP(= Noto Sans JP 相当)の Black / Bold を同梱 */
export const FONT_FAMILY = 'TelopNotoSansJP';
export const FONT_STACK = `${FONT_FAMILY}, "Noto Sans JP", "Noto Sans CJK JP", sans-serif`;

// 行の高さを日本語の字面(0.88 / 0.12 em)基準にそろえ、行の積み方を OS に左右されないようにする
const metrics = {ascentOverride: '88%', descentOverride: '12%', lineGapOverride: '0%'};

export const fontsReady = Promise.all([
  loadFont({family: FONT_FAMILY, url: staticFile('fonts/NotoSansCJKjp-Black.subset.woff2'), weight: '900', ...metrics}),
  loadFont({family: FONT_FAMILY, url: staticFile('fonts/NotoSansCJKjp-Bold.subset.woff2'), weight: '700', ...metrics}),
]);
