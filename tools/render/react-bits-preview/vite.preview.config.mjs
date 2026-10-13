// Preview wrapper: reuses the vendored React Bits config and allows the sandbox preview host.
// vendor/react-bits stays untouched.
import path from 'path';
import { fileURLToPath } from 'url';
import { mergeConfig } from '../../../vendor/react-bits/node_modules/vite/dist/node/index.js';
import base from '../../../vendor/react-bits/vite.config.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const app = path.resolve(here, '../../../vendor/react-bits');

export default mergeConfig(base, {
  root: app,
  server: { host: '0.0.0.0', port: 5173, strictPort: true, allowedHosts: true },
});
