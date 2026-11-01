import { web } from '@e2e-dev/web';
import type { E2EConfig } from 'e2e';
import { webmcpBrowsers } from '../../skills/qa/assets/webmcp/webmcp';

const app = {
  url: 'http://127.0.0.1:0',
  command: { executable: 'node', args: ['server.mjs', '{port}'],
    env: { BROKEN_UI: process.env.BROKEN_UI ?? '0' }, log: '.e2e/logs/app.log' },
};
export default {
  tests: ['smoke.e2e.ts'],
  targets: [
    // Only under the WebMCP launcher, so a plain `e2e run` still runs the ordinary target.
    ...(process.env.HONEY_WEBMCP_PORT_FILES ? [{ name: 'webmcp', app, engine: web({ browser: webmcpBrowsers }) }] : []),
    { name: 'ordinary', app, engine: web() },
  ],
  retries: 0,
} satisfies E2EConfig;
