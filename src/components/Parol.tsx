import React from 'react';
import {config} from '../config';

const RED = '#E2312F';
const GREEN = '#1E9E5A';
const INK = config.colors.outline;

/** 5点の星(外径 R・内径 r)の頂点 */
const starPoints = (cx: number, cy: number, R: number, r: number) =>
  Array.from({length: 10}, (_, i) => {
    const a = -Math.PI / 2 + (i * Math.PI) / 5;
    const rad = i % 2 === 0 ? R : r;
    return `${(cx + rad * Math.cos(a)).toFixed(2)},${(cy + rad * Math.sin(a)).toFixed(2)}`;
  }).join(' ');

/** 縁取り付きの線(黒い太線の上に色線を重ねる) */
const Stroke: React.FC<{d: string; color: string}> = ({d, color}) => (
  <>
    <path d={d} stroke={INK} strokeWidth={13} fill="none" strokeLinecap="round" />
    <path d={d} stroke={color} strokeWidth={7} fill="none" strokeLinecap="round" />
  </>
);

/** パロル(フィリピンのクリスマスの星形ランタン)。シンプルなベクター図形のみで構成。size = 高さ(px) */
export const Parol: React.FC<{size: number}> = ({size}) => (
  <svg
    width={size * 0.8}
    height={size}
    viewBox="0 0 120 150"
    style={{display: 'block', overflow: 'visible', filter: `drop-shadow(0 6px 8px ${config.colors.shadow})`}}
  >
    {/* 下に垂れる2本の飾り(しっぽ) */}
    <Stroke d="M45,104 C39,118 49,130 41,145" color={RED} />
    <Stroke d="M75,104 C81,118 71,130 79,145" color={GREEN} />
    {/* 外側の輪 */}
    <circle cx={60} cy={57} r={50} fill="none" stroke={INK} strokeWidth={13} />
    <circle cx={60} cy={57} r={50} fill="none" stroke={RED} strokeWidth={7} />
    {/* 星 */}
    <polygon
      points={starPoints(60, 57, 50, 21)}
      fill={config.colors.highlight}
      stroke={INK}
      strokeWidth={5}
      strokeLinejoin="round"
    />
    {/* 中心の飾り */}
    <circle cx={60} cy={57} r={9} fill={RED} stroke={INK} strokeWidth={3.5} />
    <circle cx={57} cy={54} r={2.6} fill="#FFFFFF" opacity={0.9} />
  </svg>
);
