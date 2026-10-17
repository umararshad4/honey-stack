# Monorepo (pnpm + Turborepo + Changesets)

`pnpm-workspace.yaml`:
```yaml
packages:
  - "apps/*"
  - "packages/*"
catalog:            # pnpm catalogs: centralize versions, consume with "react": "catalog:"
  react: ^19.0.0
  typescript: ^5.7.0
```

Root `package.json`:
```json
{
  "private": true,
  "packageManager": "pnpm@9.15.0",
  "scripts": { "build": "turbo run build", "lint": "turbo run lint", "test": "turbo run test", "typecheck": "turbo run typecheck" },
  "devDependencies": { "turbo": "^2.8.0" }
}
```

`turbo.json` (the key is `tasks`, not `pipeline`):
```json
{
  "$schema": "https://turborepo.dev/schema.json",
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**", ".next/**", "!.next/cache/**"] },
    "test": { "dependsOn": ["build"], "outputs": ["coverage/**"] },
    "lint": {},
    "typecheck": { "dependsOn": ["^build"] },
    "dev": { "cache": false, "persistent": true }
  }
}
```
`^build` = build internal deps first (topological); `dependsOn: ["build"]` = same-package. `persistent`+`cache:false` for dev servers.

- **Affected only:** `turbo run build --filter='[origin/main...HEAD]'` builds changed packages + dependents; the rest are cache hits.
- **Remote cache:** `turbo login && turbo link`; in CI set `TURBO_TOKEN` + `TURBO_TEAM` or it silently never hits.
- **Changesets:** `pnpm add -Dw @changesets/cli && pnpm changeset init`; author `pnpm changeset` → `pnpm changeset version` → `pnpm changeset publish`. CI: `changesets/action` opens a release PR; needs `fetch-depth: 0` + `NPM_TOKEN`; set `"access": "public"` for public packages.

**Mistakes:** no `outputs` listed → nothing cached, every build a miss; caching `dev`/watch tasks; missing `TURBO_TOKEN`/`TURBO_TEAM` in CI; leaving the old `pipeline` key after upgrading to v2.

When workspaces alone are enough: a small repo with no caching/orchestration need — workspaces just link dependencies.
