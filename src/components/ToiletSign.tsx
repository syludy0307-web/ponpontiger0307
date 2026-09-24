import React from 'react';
import {config} from '../config';

const BLUE = '#1F5FD1';
const RED = '#E2312F';

/** トイレ案内のピクトグラム(男女マーク)。シンプルなベクター図形のみで構成 */
export const ToiletSign: React.FC<{size: number}> = ({size}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 120 120"
    style={{display: 'block', overflow: 'visible', filter: `drop-shadow(0 6px 8px ${config.colors.shadow})`}}
  >
    <rect x={4} y={4} width={112} height={112} rx={22} fill="#FFFFFF" stroke={config.colors.outline} strokeWidth={6} />
    <line x1={60} y1={24} x2={60} y2={96} stroke="#222" strokeWidth={3.5} strokeLinecap="round" />
    {/* 男性 */}
    <circle cx={34} cy={30} r={8.5} fill={BLUE} />
    <rect x={23} y={42} width={22} height={30} rx={6} fill={BLUE} />
    <rect x={24.5} y={66} width={8.5} height={31} rx={3.5} fill={BLUE} />
    <rect x={35} y={66} width={8.5} height={31} rx={3.5} fill={BLUE} />
    {/* 女性 */}
    <circle cx={86} cy={30} r={8.5} fill={RED} />
    <path d="M79,42 H93 Q96,42 97,45 L104,73 Q105,77 101,77 H71 Q67,77 68,73 L75,45 Q76,42 79,42 Z" fill={RED} />
    <rect x={78.5} y={74} width={7.5} height={23} rx={3} fill={RED} />
    <rect x={86} y={74} width={7.5} height={23} rx={3} fill={RED} />
  </svg>
);
