import {parseMedia} from '@remotion/media-parser';
import React from 'react';
import {CalculateMetadataFunction, Composition, staticFile} from 'remotion';
import {config, FPS, HEIGHT, WIDTH} from './config';
import {DanceTrivia, DanceTriviaProps} from './DanceTrivia';

/**
 * 素材の長さから尺を決める。
 * - 素材が長い: 指定区間(trimStartSeconds から)の 450 フレーム = 15.00秒(+ エンドカード)
 * - 素材が短い: 素材の終わりで止める(ループ・静止画での水増しはしない)
 */
const calculateMetadata: CalculateMetadataFunction<DanceTriviaProps> = async ({props}) => {
  const media = await parseMedia({
    src: staticFile(config.video.src),
    fields: {durationInSeconds: true, slowNumberOfFrames: true, fps: true, dimensions: true},
    acknowledgeRemotionLicense: true,
  });
  // 映像トラックの長さ(音声だけ長い素材でも、映像の無い区間を作らない)
  const videoSeconds =
    media.slowNumberOfFrames && media.fps ? media.slowNumberOfFrames / media.fps : (media.durationInSeconds ?? 0);
  const usableSeconds = Math.min(videoSeconds, media.durationInSeconds ?? Infinity) - config.video.trimStartSeconds;
  const available = Math.floor(usableSeconds * FPS + 1e-6);
  // 豆知識パート(450) + エンドカード(有効なら 5秒 = 150)
  const target = config.video.targetDurationInFrames + (config.endCard.enabled ? Math.round(config.endCard.seconds * FPS) : 0);
  if (available < target) {
    console.warn(
      `[尺不足] 素材の使える長さは ${usableSeconds.toFixed(3)} 秒 (${available} フレーム)。` +
        `目標 ${target} フレームに ${target - available} フレーム足りないため、素材の長さで書き出します。`,
    );
  }
  const aspect = media.dimensions ? media.dimensions.width / media.dimensions.height : WIDTH / HEIGHT;
  const fit: DanceTriviaProps['fit'] = Math.abs(aspect - WIDTH / HEIGHT) < 0.01 ? 'cover' : 'contain-blur';
  return {durationInFrames: Math.max(1, Math.min(target, available)), props: {...props, fit}};
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="DanceTrivia"
    component={DanceTrivia}
    width={WIDTH}
    height={HEIGHT}
    fps={FPS}
    durationInFrames={config.video.targetDurationInFrames + (config.endCard.enabled ? Math.round(config.endCard.seconds * FPS) : 0)}
    defaultProps={{fit: 'cover'} satisfies DanceTriviaProps}
    calculateMetadata={calculateMetadata}
  />
);
