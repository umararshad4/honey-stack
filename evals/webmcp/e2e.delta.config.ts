import type { E2EConfig } from 'e2e';

export default {
  tests: ['delta.e2e.ts'],
  targets: [{ name: 'delta-cli', platform: 'cli' }],
  workers: 1,
  retries: 0,
  timeout: 90_000,
  output: '.e2e-delta',
} satisfies E2EConfig;
