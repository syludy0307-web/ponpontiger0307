import {Easing, interpolate} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** from → peak → 1 のポップアップ(前半で膨らみ、後半で 100% に戻る) */
export const popScale = (frame: number, {from, peak, frames}: {from: number; peak: number; frames: number}) => {
  const half = frames / 2;
  if (frame <= half) {
    return interpolate(frame, [0, half], [from, peak], {...clamp, easing: Easing.out(Easing.quad)});
  }
  return interpolate(frame, [half, frames], [peak, 1], {...clamp, easing: Easing.inOut(Easing.quad)});
};

/** クイズのキーワードを軽く2回弾ませる。frame 0 と終了後は静止位置(= 最初のフレームから読める) */
export const bounceOffset = (frame: number, frames: number, fontSize: number) => {
  if (frame <= 0 || frame >= frames) {
    return {y: 0, scale: 1};
  }
  const decay = 1 - frame / frames;
  const hop = Math.abs(Math.sin((Math.PI * frame) / (frames * 0.6)));
  return {y: -0.17 * fontSize * hop * decay, scale: 1 + 0.08 * hop * decay};
};

/** 0 → 1 の進み具合(ease-out) */
export const progress = (frame: number, start: number, frames: number) =>
  interpolate(frame, [start, start + frames], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
