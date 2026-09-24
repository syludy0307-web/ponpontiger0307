import type React from 'react';
import {Parol} from './Parol';
import {ToiletSign} from './ToiletSign';

/** 答えの横に出せるアイコン。aspect = 幅 / 高さ */
export const ANSWER_ICONS: Record<string, {Component: React.FC<{size: number}>; aspect: number}> = {
  parol: {Component: Parol, aspect: 0.8},
  toilet: {Component: ToiletSign, aspect: 1},
};
