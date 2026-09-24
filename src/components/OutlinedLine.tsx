import React, {useLayoutEffect, useRef, useState} from 'react';
import type {RichLine} from '../config';
import {config} from '../config';
import {FONT_STACK} from '../fonts';

/** 丸い縁取り: 同心円状に並べた text-shadow(角がトゲにならない) */
const ringShadow = (radius: number, color: string) => {
  const shadows: string[] = [];
  const rings: Array<[number, number]> = [
    [radius, 36],
    [radius * 0.67, 24],
    [radius * 0.34, 12],
  ];
  for (const [r, steps] of rings) {
    for (let i = 0; i < steps; i++) {
      const a = (i / steps) * Math.PI * 2;
      shadows.push(`${(Math.cos(a) * r).toFixed(2)}px ${(Math.sin(a) * r).toFixed(2)}px 0 ${color}`);
    }
  }
  return shadows.join(', ');
};

const Underline: React.FC<{progress: number; fontSize: number}> = ({progress, fontSize}) => (
  <span
    style={{
      position: 'absolute',
      left: '4%',
      right: '4%',
      bottom: -fontSize * 0.02,
      height: fontSize * 0.08,
      borderRadius: fontSize * 0.04,
      background: config.colors.highlight,
      boxShadow: `0 0 0 ${Math.round(fontSize * 0.035)}px ${config.colors.outline}`,
      transform: `scaleX(${progress})`,
      transformOrigin: 'left center',
    }}
  />
);

type Props = {
  line: RichLine;
  fontSize: number;
  weight?: 700 | 900;
  /** bounce: true の部分に適用する変形 */
  bounce?: {y: number; scale: number};
  /** underline: true の部分の下線の伸び具合(0〜1)。部分の登場順 */
  underline?: number[];
  /** 行の最大幅(px)。超えたら縮小して収める */
  maxWidth?: number;
};

/**
 * 黒縁取り + 薄い影付きの1行テロップ。
 * 縁取り層(下)と塗り層(上)を重ねる2層構造なので、色違いの部分同士で縁取りが食い込まない。
 */
export const OutlinedLine: React.FC<Props> = ({
  line,
  fontSize,
  weight = 900,
  bounce,
  underline,
  maxWidth = config.layout.maxLineWidth,
}) => {
  const outline = Math.max(4, Math.round(fontSize * config.outlineRatio));
  const ref = useRef<HTMLDivElement>(null);
  const [fit, setFit] = useState(1);
  const textKey = line.map((s) => s.text).join('');

  // はみ出し防止: 行幅(縁取り込み)が最大幅を超える場合だけ縮小
  useLayoutEffect(() => {
    const width = (ref.current?.offsetWidth ?? 0) + outline * 2;
    setFit(width > maxWidth ? maxWidth / width : 1);
  }, [textKey, fontSize, maxWidth, outline]);

  const renderSegments = (layer: 'outline' | 'fill') => {
    let underlineIndex = 0;
    return line.map((seg, i) => {
      const style: React.CSSProperties = {};
      if (layer === 'fill') {
        style.color = seg.highlight ? config.colors.highlight : config.colors.text;
      }
      if (seg.bounce || seg.underline) {
        style.display = 'inline-block';
        style.position = 'relative';
      }
      if (seg.bounce && bounce) {
        style.transform = `translateY(${bounce.y}px) scale(${bounce.scale})`;
        style.transformOrigin = '50% 85%';
      }
      const p = seg.underline ? (underline?.[underlineIndex++] ?? 1) : 0;
      return (
        <span key={i} style={style}>
          {seg.text}
          {seg.underline && layer === 'fill' && p > 0 ? <Underline progress={p} fontSize={fontSize} /> : null}
        </span>
      );
    });
  };

  return (
    <div style={{transform: fit === 1 ? undefined : `scale(${fit})`, transformOrigin: '50% 50%'}}>
      <div
        ref={ref}
        style={{
          position: 'relative',
          display: 'inline-block',
          whiteSpace: 'pre',
          fontFamily: FONT_STACK,
          fontWeight: weight,
          fontSize,
          lineHeight: config.layout.lineHeight,
          fontFeatureSettings: '"palt" 1',
        }}
      >
        <div
          aria-hidden
          style={{
            position: 'absolute',
            inset: 0,
            color: config.colors.outline,
            textShadow: ringShadow(outline, config.colors.outline),
            filter: `drop-shadow(0 ${Math.round(fontSize * 0.05)}px ${Math.round(fontSize * 0.06)}px ${config.colors.shadow})`,
          }}
        >
          {renderSegments('outline')}
        </div>
        <div style={{position: 'relative'}}>{renderSegments('fill')}</div>
      </div>
    </div>
  );
};
