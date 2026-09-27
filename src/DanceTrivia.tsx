import React, {useEffect, useState} from 'react';
import {AbsoluteFill, cancelRender, continueRender, delayRender, OffthreadVideo, Sequence, staticFile, useVideoConfig} from 'remotion';
import {EndCard} from './components/EndCard';
import {SeriesLabel} from './components/SeriesLabel';
import {config} from './config';
import {fontsReady} from './fonts';
import {AnswerScene} from './scenes/AnswerScene';
import {ExplainScene} from './scenes/ExplainScene';
import {QuizScene} from './scenes/QuizScene';
import {RecapScene} from './scenes/RecapScene';

export type DanceTriviaProps = {
  /** cover: 9:16素材をそのまま全面に / contain-blur: 9:16以外の素材を切らずに収め、背景にぼかしを敷く */
  fit: 'cover' | 'contain-blur';
};

/** フォントの読み込みが終わってからテロップを描く(文字幅の計測を正しくするため) */
const FontGate: React.FC<{children: React.ReactNode}> = ({children}) => {
  const [handle] = useState(() => delayRender('テロップ用フォントの読み込み'));
  const [ready, setReady] = useState(false);
  useEffect(() => {
    fontsReady.then(() => setReady(true)).catch((err) => cancelRender(err));
  }, []);
  useEffect(() => {
    if (ready) {
      continueRender(handle);
    }
  }, [ready, handle]);
  return ready ? <>{children}</> : null;
};

export const DanceTrivia: React.FC<DanceTriviaProps> = ({fit}) => {
  const {fps, durationInFrames} = useVideoConfig();
  // エンドカードは最後の数秒(ダンスはその下で流れ続ける)
  const endFrames = config.endCard.enabled ? Math.round(config.endCard.seconds * fps) : 0;
  const endStart = durationInFrames - endFrames;
  const src = staticFile(config.video.src);
  const trimBefore = Math.round(config.video.trimStartSeconds * fps);
  const s = config.scenes;
  const fill: React.CSSProperties = {width: '100%', height: '100%'};

  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {/* 最下層: ダンス動画を全編で1本だけ連続再生(シーンごとに再スタートしない) */}
      {fit === 'contain-blur' ? (
        <AbsoluteFill style={{overflow: 'hidden'}}>
          <OffthreadVideo
            src={src}
            trimBefore={trimBefore}
            muted
            style={{...fill, objectFit: 'cover', filter: 'blur(48px) brightness(0.65)', transform: 'scale(1.15)'}}
          />
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill>
        <OffthreadVideo
          src={src}
          trimBefore={trimBefore}
          volume={config.video.volume}
          style={{...fill, objectFit: fit === 'cover' ? 'cover' : 'contain'}}
        />
      </AbsoluteFill>

      {/* 上層: テロップ・ピクトグラム・集中線 */}
      <FontGate>
        <SeriesLabel />
        <Sequence name="クイズ" from={s.quiz} durationInFrames={s.answer - s.quiz} layout="none">
          <QuizScene />
        </Sequence>
        <Sequence name="答え" from={s.answer} durationInFrames={s.explain - s.answer} layout="none">
          <AnswerScene />
        </Sequence>
        <Sequence name="解説" from={s.explain} durationInFrames={s.recap - s.explain} layout="none">
          <ExplainScene />
        </Sequence>
        <Sequence name="復習と締め" from={s.recap} durationInFrames={Math.max(1, endStart - s.recap)} layout="none">
          <RecapScene />
        </Sequence>
        {endFrames > 0 ? (
          <Sequence name="エンドカード" from={endStart} layout="none">
            <EndCard />
          </Sequence>
        ) : null}
      </FontGate>
    </AbsoluteFill>
  );
};
