import { web } from '@e2e-dev/web';
import type { E2EConfig } from 'e2e';
import { webmcpBrowsers } from '../../../skills/qa/assets/webmcp/webmcp';

const app = { url: process.env.APP_URL! };
const target = (name: string, width: number, height: number) => ({
  name, app, engine: web({
    viewport: { width, height },
    browser: webmcpBrowsers,
  }),
});

export default {
  tests: ['tasks.e2e.ts'],
  targets: [target('desktop', 1440, 900), target('mobile', 390, 844)],
  workers: 1, retries: 0, assertionTimeout: 500, actionTimeout: 2000,
} satisfies E2EConfig;
