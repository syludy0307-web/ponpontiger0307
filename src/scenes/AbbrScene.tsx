import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {progress} from '../animation';
import {CaptionBlock} from '../components/CaptionBlock';
import {OutlinedLine} from '../components/OutlinedLine';
import {config} from '../config';

/** 7.50〜11.50秒: 略語の意味「Comfort Room / の略です」 */
export const AbbrScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {abbr} = config.texts;
  // 短い登場(0.15秒)の後は文字を動かさない
  const enter = progress(frame, 0, 5);
  const opacity = interpolate(frame, [0, 3], [0.3, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  // C と R の下線を、それぞれ約0.25秒で左から右へ
  const uf = config.motion.underlineFrames;
  const underline = [progress(frame, 5, uf), progress(frame, 9, uf)];
  return (
    <CaptionBlock style={{opacity, transform: `translateY(${(1 - enter) * 14}px)`}}>
      <div style={{marginBottom: config.layout.underlineExtraGap}}>
        <OutlinedLine line={abbr.line1} fontSize={config.fontSize.main} underline={underline} />
      </div>
      <OutlinedLine line={abbr.line2} fontSize={config.fontSize.sub} />
    </CaptionBlock>
  );
};
