# Test runner & CI glue

## Vitest 3 in a monorepo — inline `projects` (not the deprecated `vitest.workspace.ts`)
```ts
// vitest.config.ts (root)
import { defineConfig } from "vitest/config";
export default defineConfig({ test: { projects: ["packages/*", "apps/*"] } });
```
Each matched folder is its own project. Affected tests: `turbo run test --filter='[HEAD^1]'` or `vitest --changed HEAD~1`. Make `test` a Turborepo task with `outputs: ["coverage/**"]` so unchanged packages are cache hits. (Jest 30 if you have heavy Jest-specific infra.)

## GitHub Actions — install(cached) → lint → typecheck → test → build
```yaml
name: CI
on: { push: { branches: [main] }, pull_request: {} }
env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: ${{ vars.TURBO_TEAM }}
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }          # needed for affected filtering + changesets
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo run lint typecheck test build --filter='[origin/main...HEAD]'
```
One `turbo run` runs the whole pipeline respecting the task graph; the filter restricts to affected packages; the remote cache restores unchanged work.

**Mistakes:** omitting `fetch-depth: 0` (breaks affected + changesets); secrets not wired (remote cache misses every run); not using `--frozen-lockfile`; leaving `vitest.workspace.ts` after upgrading to Vitest 3.
