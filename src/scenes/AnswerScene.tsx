import React, {useLayoutEffect, useRef, useState} from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {popScale} from '../animation';
import {CaptionBlock} from '../components/CaptionBlock';
import {OutlinedLine} from '../components/OutlinedLine';
import {SpeedLines} from '../components/SpeedLines';
import {ToiletSign} from '../components/ToiletSign';
import {config} from '../config';

/** 4.00〜7.50秒: 答え「正解は… / トイレ！」(この動画で一番強い演出はここだけ) */
export const AnswerScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {answer} = config.texts;
  const {pictogramSize, pictogramGap, maxLineWidth} = config.layout;
  const textRef = useRef<HTMLDivElement>(null);
  const [box, setBox] = useState({w: 0, h: 0});

  useLayoutEffect(() => {
    const el = textRef.current;
    if (el) {
      setBox({w: el.offsetWidth, h: el.offsetHeight});
    }
  }, []);

  // 「トイレ！」: 85% → 108% → 100% を約0.2秒。その後は静止
  const pop = popScale(frame, config.motion.answerPop);
  // ピクトグラムは少し遅れて出す
  const iconScale = popScale(frame - 2, {from: 0.5, peak: 1.1, frames: 7});
  const iconOpacity = interpolate(frame, [2, 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <CaptionBlock>
      <OutlinedLine line={answer.line1} fontSize={config.fontSize.sub} />
      <div style={{display: 'flex', alignItems: 'center', gap: pictogramGap}}>
        <div ref={textRef} style={{position: 'relative'}}>
          <SpeedLines frame={frame} width={box.w} height={box.h} />
          <div style={{transform: `scale(${pop})`, transformOrigin: '50% 55%'}}>
            <OutlinedLine
              line={answer.line2}
              fontSize={config.fontSize.answer}
              maxWidth={maxLineWidth - pictogramSize - pictogramGap}
            />
          </div>
        </div>
        <div style={{transform: `scale(${iconScale})`, opacity: iconOpacity}}>
          <ToiletSign size={pictogramSize} />
        </div>
      </div>
    </CaptionBlock>
  );
};
