import React, {useLayoutEffect, useRef, useState} from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {popScale} from '../animation';
import {ANSWER_ICONS} from '../components/answerIcons';
import {CaptionBlock} from '../components/CaptionBlock';
import {OutlinedLine} from '../components/OutlinedLine';
import {SpeedLines} from '../components/SpeedLines';
import {config} from '../config';

/** 4.00秒〜7.50秒: 答え(この動画で一番強い演出はここだけ) */
export const AnswerScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {answer} = config.texts;
  const {iconSize, iconGap, maxLineWidth, answerLabel} = config.layout;
  const icon = config.answerIcon === 'none' ? null : ANSWER_ICONS[config.answerIcon];
  const iconWidth = icon ? iconSize * icon.aspect + iconGap : 0;
  // 縦書きラベルは答えの左に置く(その分、答えの最大幅を減らす)。間隔は答えが108%に膨らんでも重ならない幅
  const labelGap = 40;
  const labelWidth = answerLabel === 'vertical' ? config.fontSize.answerLabel * config.layout.lineHeight + labelGap : 0;
  const textRef = useRef<HTMLDivElement>(null);
  const [box, setBox] = useState({w: 0, h: 0});

  useLayoutEffect(() => {
    const el = textRef.current;
    if (el) {
      setBox({w: el.offsetWidth, h: el.offsetHeight});
    }
  }, []);

  // 答えの文字: 85% → 108% → 100% を約0.2秒。その後は静止
  const pop = popScale(frame, config.motion.answerPop);
  // アイコンは少し遅れて出す
  const iconScale = popScale(frame - 2, {from: 0.5, peak: 1.1, frames: 7});
  const iconOpacity = interpolate(frame, [2, 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const answerRow = (
    <div style={{display: 'flex', alignItems: 'center', gap: iconGap}}>
      <div ref={textRef} style={{position: 'relative'}}>
        <SpeedLines frame={frame} width={box.w} height={box.h} />
        <div style={{transform: `scale(${pop})`, transformOrigin: '50% 55%'}}>
          <OutlinedLine line={answer.line2} fontSize={config.fontSize.answer} maxWidth={maxLineWidth - iconWidth - labelWidth} />
        </div>
      </div>
      {icon ? (
        <div style={{transform: `scale(${iconScale})`, opacity: iconOpacity}}>
          <icon.Component size={iconSize} />
        </div>
      ) : null}
    </div>
  );

  if (answerLabel === 'vertical') {
    // 「正解は…」を答えの左に小さく縦書き → 答えが1段に収まり、頭上の帯の高さを使い切らない
    return (
      <CaptionBlock>
        <div style={{display: 'flex', alignItems: 'center', gap: labelGap}}>
          {/* 集中線より手前に描く */}
          <div style={{position: 'relative', zIndex: 2}}>
            <OutlinedLine line={answer.line1} fontSize={config.fontSize.answerLabel} vertical />
          </div>
          {answerRow}
        </div>
      </CaptionBlock>
    );
  }

  return (
    <CaptionBlock>
      <OutlinedLine line={answer.line1} fontSize={config.fontSize.sub} />
      {answerRow}
    </CaptionBlock>
  );
};
