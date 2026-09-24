import React from 'react';
import {useCurrentFrame} from 'remotion';
import {bounceOffset} from '../animation';
import {CaptionBlock} from '../components/CaptionBlock';
import {OutlinedLine} from '../components/OutlinedLine';
import {QuestionMark} from '../components/QuestionMark';
import {config} from '../config';

/** 0.00〜4.00秒: クイズ。1フレーム目から読める状態で、キーワードだけ最初の0.25秒で軽く弾む */
export const QuizScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {quiz} = config.texts;
  const bounce = bounceOffset(frame, config.motion.bounceFrames, config.fontSize.main);
  return (
    <CaptionBlock>
      <OutlinedLine line={quiz.line1} fontSize={config.fontSize.sub} />
      <div style={{position: 'relative'}}>
        <QuestionMark frame={frame} start={9} side="left" tilt={-14} size={config.fontSize.questionMark * 0.85} />
        <OutlinedLine line={quiz.line2} fontSize={config.fontSize.main} bounce={bounce} />
        <QuestionMark frame={frame} start={5} side="right" tilt={14} highlight />
      </div>
    </CaptionBlock>
  );
};
