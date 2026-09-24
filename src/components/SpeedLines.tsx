import React from 'react';
import {Easing, interpolate, random} from 'remotion';
import {config} from '../config';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

type Props = {
  /** 登場からの経過フレーム */
  frame: number;
  /** 文字の箱の大きさ(px)。線はこの箱の外周から外側へ伸びる */
  width: number;
  height: number;
};

const COUNT = 30;

/**
 * 文字の背後だけに出す短い集中線(約0.35秒)。
 * 人物や画面全体は動かさず、テロップの周囲だけで完結させる。
 */
export const SpeedLines: React.FC<Props> = ({frame, width, height}) => {
  const total = config.motion.speedLinesFrames;
  if (frame < 0 || frame >= total || width === 0) {
    return null;
  }
  const t = frame / total;
  // 前半: 外へ伸びる / 後半: 根元が外へ抜けながら消える
  const grow = interpolate(t, [0, 0.4], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const retract = interpolate(t, [0.35, 1], [0, 1], {...clamp, easing: Easing.in(Easing.quad)});
  const opacity = interpolate(t, [0.55, 1], [1, 0], clamp);

  // 線の範囲: 横に広く、下側(頭の方向)は控えめ
  const padX = 92;
  const padTop = 34;
  const padBottom = 26;
  const cx = width / 2;
  const cy = height / 2;
  const svgW = width + padX * 2;
  const svgH = height + padTop + padBottom;

  const paths: React.ReactNode[] = [];
  for (let i = 0; i < COUNT; i++) {
    const angle = ((i + random(`a${i}`) * 0.6) / COUNT) * Math.PI * 2;
    const dx = Math.cos(angle);
    const dy = Math.sin(angle);
    const rx0 = width * 0.44;
    const ry0 = height * 0.36;
    const len = 0.55 + random(`l${i}`) * 0.45;
    const rx1 = width / 2 + padX * len;
    const ry1 = height / 2 + (dy > 0 ? padBottom : padTop) * len;
    const inner = rx0 + (rx1 - rx0) * retract;
    const innerY = ry0 + (ry1 - ry0) * retract;
    const outer = rx0 + (rx1 - rx0) * grow;
    const outerY = ry0 + (ry1 - ry0) * grow;
    const x0 = cx + dx * inner;
    const y0 = cy + dy * innerY;
    const x1 = cx + dx * outer;
    const y1 = cy + dy * outerY;
    if (Math.hypot(x1 - x0, y1 - y0) < 2) {
      continue;
    }
    // 根元が太く先が細いくさび形
    const w = 5 + random(`w${i}`) * 4;
    const nx = -dy;
    const ny = dx;
    const d = `M${x0 + nx * w},${y0 + ny * w} L${x1},${y1} L${x0 - nx * w},${y0 - ny * w} Z`;
    paths.push(
      <path
        key={i}
        d={d}
        fill={i % 3 === 0 ? config.colors.text : config.colors.highlight}
        stroke={config.colors.outline}
        strokeWidth={2.5}
        strokeLinejoin="round"
      />,
    );
  }

  return (
    <svg
      width={svgW}
      height={svgH}
      viewBox={`${-padX} ${-padTop} ${svgW} ${svgH}`}
      style={{position: 'absolute', left: -padX, top: -padTop, overflow: 'visible', opacity, pointerEvents: 'none'}}
    >
      {paths}
    </svg>
  );
};
