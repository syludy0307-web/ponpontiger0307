import React from 'react';
import {AbsoluteFill, Easing, interpolate, random, useCurrentFrame} from 'remotion';
import {config} from '../config';
import {FONT_STACK, SERIF_STACK} from '../fonts';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.out(Easing.cubic);
const {goldLight, gold, goldDeep} = config.colors;
const GOLD_FILL = `linear-gradient(180deg, ${goldLight} 0%, #FFE9A8 38%, ${gold} 68%, ${goldDeep} 100%)`;
const clipText: React.CSSProperties = {WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent'};

/** 金色の文字: 影とグロー(下) + 金のグラデーション(中) + 光が走る層(上) */
const GoldText: React.FC<{children: string; style: React.CSSProperties; shine: number}> = ({children, style, shine}) => (
  <span style={{position: 'relative', display: 'inline-block', whiteSpace: 'pre', ...style}}>
    <span
      aria-hidden
      style={{position: 'absolute', inset: 0, color: 'transparent', textShadow: '0 3px 10px rgba(0,0,0,0.75), 0 0 26px rgba(255,196,80,0.45)'}}
    >
      {children}
    </span>
    <span style={{position: 'relative', backgroundImage: GOLD_FILL, ...clipText}}>{children}</span>
    <span
      aria-hidden
      style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: 'linear-gradient(105deg, transparent 42%, rgba(255,255,255,0.95) 50%, transparent 58%)',
        backgroundSize: '300% 100%',
        backgroundPosition: `${shine}% 0`,
        ...clipText,
      }}
    >
      {children}
    </span>
  </span>
);

/** 中央から左右へ伸びる金の細線(ひし形の飾り付き) */
const GoldLine: React.FC<{p: number; width: number; diamond?: boolean}> = ({p, width, diamond}) => (
  <div style={{position: 'relative', width, height: 14, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
    <div
      style={{
        width: '100%',
        height: 2,
        transform: `scaleX(${p})`,
        background: `linear-gradient(90deg, transparent, ${gold} 18%, ${goldLight} 50%, ${gold} 82%, transparent)`,
        boxShadow: '0 0 8px rgba(255,210,120,0.6)',
      }}
    />
    {diamond ? (
      <div
        style={{
          position: 'absolute',
          width: 10,
          height: 10,
          transform: `rotate(45deg) scale(${p})`,
          background: goldLight,
          boxShadow: '0 0 10px rgba(255,220,140,0.9)',
        }}
      />
    ) : null}
  </div>
);

/** 4方向に光るきらめき */
const Sparkle: React.FC<{x: number; y: number; size: number; opacity: number}> = ({x, y, size, opacity}) => (
  <svg
    width={size}
    height={size}
    viewBox="-10 -10 20 20"
    style={{position: 'absolute', left: x - size / 2, top: y - size / 2, opacity, filter: 'drop-shadow(0 0 6px rgba(255,230,160,0.95))'}}
  >
    <path d="M0,-10 C1.2,-1.2 1.2,-1.2 10,0 C1.2,1.2 1.2,1.2 0,10 C-1.2,1.2 -1.2,1.2 -10,0 C-1.2,-1.2 -1.2,-1.2 0,-10 Z" fill="#FFF7DC" />
  </svg>
);

/**
 * 最後の数秒に重ねるエンドカード(所属・店名・名前)。
 * ダンスは止めず、人物の頭上の帯だけで完結させる。登場の動きの後は読みやすさ優先で静止。
 */
export const EndCard: React.FC = () => {
  const f = useCurrentFrame();
  const {label, club, name, top} = config.endCard;
  const {centerX} = config.layout;

  // 背景: 上から下へ薄くなる暗いグラデーション(文字のコントラスト確保。顔の位置までは届かない)
  const scrim = interpolate(f, [0, 10], [0, 1], clamp);
  // 切り替わりの光(斜めの光が左から右へ一度だけ走る)
  const sweepX = interpolate(f, [0, 20], [-30, 130], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const sweepOpacity = interpolate(f, [0, 4, 14, 20], [0, 0.85, 0.85, 0], clamp);
  // 金の線
  const line1 = interpolate(f, [4, 18], [0, 1], {...clamp, easing: ease});
  const line2 = interpolate(f, [16, 30], [0, 1], {...clamp, easing: ease});
  // 所属 + 店名: 左から右へ現れる
  const rowReveal = interpolate(f, [10, 28], [100, 0], {...clamp, easing: ease});
  const rowShift = interpolate(f, [10, 28], [18, 0], {...clamp, easing: ease});
  // 名前: ぼかし → くっきり、字間が締まる
  const nameP = interpolate(f, [22, 40], [0, 1], {...clamp, easing: ease});
  const tracking = 0.22 + (1 - nameP) * 0.33;
  // 光が文字の上を一度だけ走る
  const nameShine = interpolate(f, [46, 72], [100, 0], clamp);
  const clubShine = interpolate(f, [56, 82], [100, 0], clamp);

  const sparkles = Array.from({length: 14}, (_, i) => {
    const x = 150 + random(`sx${i}`) * 780;
    const y = top - 6 + random(`sy${i}`) * 236;
    const period = 26 + random(`sp${i}`) * 22;
    const phase = random(`sph${i}`) * period;
    const t = f - 18 - phase;
    const opacity = t < 0 ? 0 : Math.pow(Math.max(0, Math.sin((t / period) * Math.PI * 2)), 3);
    return <Sparkle key={i} x={x} y={y} size={12 + random(`ss${i}`) * 14} opacity={opacity} />;
  });

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 0,
          height: top + 270,
          opacity: scrim,
          background: 'linear-gradient(180deg, rgba(12,8,2,0.66) 0%, rgba(12,8,2,0.5) 55%, rgba(12,8,2,0) 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top,
          left: centerX - 540,
          width: 1080,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <GoldLine p={line1} width={620} />
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 22,
            marginTop: 6,
            clipPath: `inset(-20% ${rowReveal}% -20% -5%)`,
            transform: `translateX(${rowShift}px)`,
          }}
        >
          <div
            style={{
              border: `1.5px solid ${gold}`,
              borderRadius: 4,
              padding: '3px 10px 5px 20px',
              background: 'rgba(0,0,0,0.3)',
              color: goldLight,
              fontFamily: FONT_STACK,
              fontWeight: 700,
              fontSize: 28,
              lineHeight: 1.2,
              letterSpacing: '0.35em',
              boxShadow: '0 0 12px rgba(255,210,120,0.35)',
            }}
          >
            {label}
          </div>
          <GoldText
            shine={clubShine}
            style={{fontFamily: SERIF_STACK, fontWeight: 700, fontSize: 62, lineHeight: 1.12, letterSpacing: '0.03em'}}
          >
            {club}
          </GoldText>
        </div>
        <GoldLine p={line2} width={440} diamond />
        <div
          style={{
            marginTop: 2,
            paddingLeft: `${tracking}em`,
            fontSize: 104,
            opacity: nameP,
            filter: nameP < 1 ? `blur(${(1 - nameP) * 12}px)` : undefined,
            transform: `scale(${1 + (1 - nameP) * 0.06})`,
          }}
        >
          <GoldText
            shine={nameShine}
            style={{fontFamily: FONT_STACK, fontWeight: 900, fontSize: 104, lineHeight: 1.1, letterSpacing: `${tracking}em`}}
          >
            {name}
          </GoldText>
        </div>
      </div>
      {sparkles}
      <div style={{position: 'absolute', left: 0, right: 0, top: top - 40, height: 300, overflow: 'hidden', opacity: sweepOpacity}}>
        <div
          style={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            width: 240,
            left: `${sweepX}%`,
            transform: 'translateX(-50%) skewX(-22deg)',
            background: 'linear-gradient(90deg, transparent, rgba(255,240,205,0.55), transparent)',
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
