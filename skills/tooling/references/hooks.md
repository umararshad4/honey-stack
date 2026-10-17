# Pre-commit hooks

Pick: **Husky + lint-staged** (JS/TS default); **Lefthook** (Go binary, fastest, parallel, polyglot, built-in staged filtering); **`pre-commit`** framework (Python/polyglot, huge prebuilt-hook library).

## Husky v9+ (no old boilerplate)
```bash
pnpm add -D husky lint-staged
pnpm exec husky init          # creates .husky/, a pre-commit hook, and the "prepare": "husky" script
```
`.husky/pre-commit` → just `pnpm exec lint-staged`. `package.json`:
```json
{ "scripts": { "prepare": "husky" },
  "lint-staged": { "*.{js,ts,tsx}": ["biome check --write --no-errors-on-unmatched"] } }
```

## Lefthook (`lefthook.yml`)
```yaml
pre-commit:
  parallel: true
  commands:
    lint: { glob: "*.{js,ts,tsx}", run: "biome check --write {staged_files}", stage_fixed: true }
commit-msg:
  commands:
    commitlint: { run: "pnpm exec commitlint --edit {1}" }
```
`pnpm add -D lefthook && pnpm exec lefthook install`.

## pre-commit framework (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks: [ { id: ruff, args: [--fix] }, { id: ruff-format } ]
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.24.2
    hooks: [ { id: gitleaks } ]
```
`pip install pre-commit && pre-commit install`; refresh pins with `pre-commit autoupdate`.

## Conventional Commits + secrets
`pnpm add -D @commitlint/cli @commitlint/config-conventional`; `commitlint.config.js` → `export default { extends: ['@commitlint/config-conventional'] }`; commit-msg hook runs `commitlint --edit $1`. Secret scan: `gitleaks protect --staged --redact` in pre-commit (or the hook above).

**Mistakes:** old Husky v4/v8 boilerplate in a v9 hook (breaks); linting the whole repo not staged files (slow → devs disable it); not re-staging auto-fixes; missing `"prepare": "husky"` so hooks don't install on clone; unpinned gitleaks `rev`.
