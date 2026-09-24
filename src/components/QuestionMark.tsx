import React from 'react';
import {Easing, interpolate} from 'remotion';
import {config} from '../config';
import {OutlinedLine} from './OutlinedLine';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

type Props = {
  frame: number;
  /** 出現フレーム */
  start: number;
  side: 'left' | 'right';
  /** 落ち着いた後の傾き(度) */
  tilt: number;
  highlight?: boolean;
  size?: number;
};

/** 質問の横に出す小さな「？」。短く揺れた後は静止する */
export const QuestionMark: React.FC<Props> = ({frame, start, side, tilt, highlight, size = config.fontSize.questionMark}) => {
  const f = frame - start;
  if (f < 0) {
    return null;
  }
  const scale = interpolate(f, [0, 4, 7], [0.3, 1.08, 1], {...clamp, easing: Easing.out(Easing.quad)});
  const opacity = interpolate(f, [0, 2], [0, 1], clamp);
  // 約0.6秒だけ揺れて、その後は傾いたまま静止
  const wiggle = f < 18 ? 13 * Math.sin((f / 18) * Math.PI * 3) * (1 - f / 18) : 0;
  return (
    <div
      style={{
        position: 'absolute',
        top: -size * 0.28,
        [side === 'right' ? 'left' : 'right']: '100%',
        [side === 'right' ? 'marginLeft' : 'marginRight']: size * 0.06,
        transform: `rotate(${tilt + wiggle}deg) scale(${scale})`,
        transformOrigin: '50% 80%',
        opacity,
      }}
    >
      <OutlinedLine line={[{text: '？', highlight}]} fontSize={size} />
    </div>
  );
};
