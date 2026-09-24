import React from 'react';
import {config} from '../config';
import {FONT_STACK} from '../fonts';

/** 左上の余白に小さく固定表示するシリーズ名(主役にしない) */
export const SeriesLabel: React.FC = () => {
  const {left, top} = config.layout.seriesLabel;
  const size = config.fontSize.series;
  return (
    <div
      style={{
        position: 'absolute',
        left,
        top,
        padding: `${size * 0.2}px ${size * 0.5}px ${size * 0.24}px`,
        borderRadius: size,
        background: config.colors.seriesBand,
        color: config.colors.text,
        fontFamily: FONT_STACK,
        fontWeight: 700,
        fontSize: size,
        lineHeight: 1.2,
        whiteSpace: 'pre',
        fontFeatureSettings: '"palt" 1',
        letterSpacing: '0.03em',
      }}
    >
      {config.texts.series.title} <span style={{color: config.colors.highlight}}>{config.texts.series.episode}</span>
    </div>
  );
};
