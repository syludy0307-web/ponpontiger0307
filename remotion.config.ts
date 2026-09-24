import {Config} from '@remotion/cli/config';

// 書き出し設定: TikTok 向け 1080x1920 / 30fps / H.264 yuv420p / CRF 18 / AAC 192kbps
// (解像度・fps・尺は src/Root.tsx と src/config.ts 側で決まります)
Config.setEntryPoint('src/index.ts');
Config.setVideoImageFormat('png'); // フレームの取り込みを可逆に(JPEG の劣化を避ける)
Config.setCodec('h264');
Config.setCrf(18);
Config.setPixelFormat('yuv420p');
Config.setColorSpace('bt709');
Config.setX264Preset('slow');
Config.setAudioCodec('aac');
Config.setAudioBitrate('192k');
Config.setOverwriteOutput(true);

// Chrome を自分で指定したい場合だけ使う(未指定なら Remotion が自動でダウンロード)
if (process.env.REMOTION_BROWSER_EXECUTABLE) {
  Config.setBrowserExecutable(process.env.REMOTION_BROWSER_EXECUTABLE);
}
