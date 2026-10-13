// Local Remotion config: offline fonts + sandbox Chromium. Lives outside the vendored repo.
import { Config } from '@remotion/cli/config';

// Absolute path: Remotion loads this config as CJS, so import.meta is unavailable.
const shim = '/home/user/Monarch-Studio/tools/render/remotion-offline/font-shim.mjs';

Config.overrideWebpackConfig((cfg) => ({
  ...cfg,
  resolve: {
    ...cfg.resolve,
    alias: {
      ...(cfg.resolve?.alias || {}),
      '@remotion/google-fonts/SpaceGrotesk': shim,
      '@remotion/google-fonts/PlayfairDisplay': shim,
    },
  },
}));
Config.setBrowserExecutable('/tmp/chromium');
Config.setChromiumOpenGlRenderer('swangle');
