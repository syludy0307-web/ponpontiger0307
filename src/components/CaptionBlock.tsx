import React from 'react';
import {config} from '../config';

/** メインテロップの置き場所(人物の頭上)。全シーン共通の位置で、上下左右に動かさない */
export const CaptionBlock: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => {
  const {captionTop, centerX, maxLineWidth, lineGap} = config.layout;
  return (
    <div
      style={{
        position: 'absolute',
        top: captionTop,
        left: centerX - maxLineWidth / 2,
        width: maxLineWidth,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: lineGap,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
