import React from 'react';
import {config} from '../config';
import {FONT_STACK} from '../fonts';

const INK = config.colors.outline;
const RED = '#E2312F';

/** 1月のカレンダー。最初の日曜日のマスだけ黄色(「1月の第1日曜日」につながる)。size = 高さ(px) */
export const CalendarIcon: React.FC<{size: number}> = ({size}) => {
  const cells: React.ReactNode[] = [];
  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 7; col++) {
      const first = row === 0 && col === 0;
      const s = first ? 13 : 9.5;
      const cx = 20 + col * 13.4;
      const cy = 68 + row * 17;
      cells.push(
        <rect
          key={`${row}-${col}`}
          x={cx - s / 2}
          y={cy - s / 2}
          width={s}
          height={s}
          rx={first ? 3.5 : 2.5}
          fill={first ? config.colors.highlight : '#C7CCD4'}
          stroke={first ? INK : 'none'}
          strokeWidth={first ? 2.5 : 0}
        />,
      );
    }
  }
  return (
    <svg
      width={size * (120 / 130)}
      height={size}
      viewBox="0 0 120 130"
      style={{display: 'block', overflow: 'visible', filter: `drop-shadow(0 6px 8px ${config.colors.shadow})`}}
    >
      <rect x={6} y={16} width={108} height={108} rx={16} fill="#FFFFFF" stroke={INK} strokeWidth={6} />
      <path d="M9,32 A13,13 0 0 1 22,19 H98 A13,13 0 0 1 111,32 V50 H9 Z" fill={RED} />
      <line x1={9} y1={50} x2={111} y2={50} stroke={INK} strokeWidth={4} />
      <text x={60} y={43} textAnchor="middle" fontFamily={FONT_STACK} fontWeight={900} fontSize={23} fill="#FFFFFF" letterSpacing={3}>
        JAN
      </text>
      <rect x={30} y={4} width={10} height={24} rx={5} fill="#5B6270" stroke={INK} strokeWidth={4} />
      <rect x={80} y={4} width={10} height={24} rx={5} fill="#5B6270" stroke={INK} strokeWidth={4} />
      {cells}
    </svg>
  );
};
