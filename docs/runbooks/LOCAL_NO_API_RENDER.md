# Local no-API render runbook (sandbox-verified 2026-10-12)

Verified in the sandbox: headless Chromium, Remotion render of OpenMontage's
`Explainer` composition (1920x1080, 30 fps, 4 s, H.264 + AAC), and frame extraction.
No API keys are used.

## 1. Chromium (no CDN needed)
The binary comes from the npm package `@sparticuz/chromium` (npm registry is allowed):
```bash
mkdir -p /tmp/chromium-test && cd /tmp/chromium-test
npm install @sparticuz/chromium
# extract the bundled chromium (executablePath() writes /tmp/chromium)
node --input-type=module -e "import c from '@sparticuz/chromium'; console.log(await c.executablePath())"
# shared libs: decompress al2023.tar.br + swiftshader.tar.br from node_modules/@sparticuz/chromium/bin
export LD_LIBRARY_PATH=/tmp/al2023/lib:/tmp/swiftshader
/tmp/chromium --headless=shell --no-sandbox --no-zygote --disable-gpu \
  --remote-debugging-port=9222 --user-data-dir=/tmp/chr-prof about:blank
```

## 2. Remotion render (offline fonts)
`vendor/OpenMontage/remotion-composer` is pinned upstream. Its composition loads Google Fonts,
which are blocked here, so `tools/render/remotion-offline/` provides:
- `font-shim.mjs`: an offline stand-in for `@remotion/google-fonts`.
- `remotion.config.mjs`: aliases the font modules and sets `--browser-executable`.

```bash
cd vendor/OpenMontage/remotion-composer && npm install
export LD_LIBRARY_PATH=/tmp/al2023/lib:/tmp/swiftshader
npx remotion render src/index.tsx Explainer out.mp4 \
  --config=<abs>/tools/render/remotion-offline/remotion.config.mjs \
  --props=public/demo-props/code-to-screen.json --frames=0-119 \
  --browser-executable=/tmp/chromium --concurrency=1 --log=error
```

## Known limits
- `TitledVideo` needs a `videoSrc` asset, which the repo does not ship.
- Clips with real footage or images need those assets supplied locally.
- Speed: 1 concurrency on 2 vCPU. Use short frame ranges.
- Piper voices come from HuggingFace, which is blocked here. Narration needs another local TTS.
