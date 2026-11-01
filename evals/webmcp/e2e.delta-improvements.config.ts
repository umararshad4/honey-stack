import type { E2EConfig } from 'e2e';

export default {
  tests: ['delta-improvements.e2e.ts'],
  targets: [{ name: 'delta-improvements', platform: 'cli' }],
  workers: 1,
  retries: 0,
  timeout: 120_000,
  output: '.e2e-delta-improvements',
} satisfies E2EConfig;
