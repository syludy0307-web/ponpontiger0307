import React from 'react';
import {useCurrentFrame} from 'remotion';
import {popScale} from '../animation';
import {CaptionBlock} from '../components/CaptionBlock';
import {OutlinedLine} from '../components/OutlinedLine';
import {config} from '../config';

/** 11.50秒〜最後: 復習と締め。登場時だけ軽くポップ、その後は最後まで静止 */
export const RecapScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {recap} = config.texts;
  const pop = popScale(frame, {from: 0.9, peak: 1.05, frames: 7});
  return (
    <CaptionBlock style={{transform: `scale(${pop})`, transformOrigin: '50% 40%'}}>
      <OutlinedLine line={recap.line1} fontSize={config.fontSize.recap} />
      <OutlinedLine line={recap.line2} fontSize={config.fontSize.recapSub} />
    </CaptionBlock>
  );
};
